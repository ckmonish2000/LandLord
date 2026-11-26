"""Bill split sub-agent, as a LangGraph subgraph inside Alfred.

    extract ─→ resolve_property ─┬─────────────────────────→ load_members
                                 └→ ask_property → wait_property ┘   │
                                                                     ▼
            ┌──────────── new vote ─────────────┐     ask_members (polls)
            ▼                                   │            │
    compute → ask_confirm (buttons) → wait_confirm   wait_members ─→ compute
                                        ├─ yes → deliver → END
                                        └─ no  → END

Every ask_* node sends a question and saves its message ids in `waiting`; the
wait_* node after it pauses with interrupt(). Sending and waiting are separate
nodes on purpose: on resume LangGraph re-runs the paused node from the top, and
the question must not be sent twice.
"""

import time

from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, START, StateGraph
from langgraph.runtime import Runtime
from langgraph.types import Command, interrupt

from src.agents.base import AgentContext, Option
from src.agents.bill_split import messages
from src.agents.bill_split.extract import extract_bill
from src.agents.bill_split.utils import as_poll_members
from src.agents.bill_split.constants import (
    ALL_OPTION,
    CONFIRM_NO,
    CONFIRM_YES,
    DELIVERY_DELAY_SECONDS,
    MEMBERS_PER_POLL,
    PROPERTY_LIST_MAX,
)
from src.agents.bill_split.state import BillSplitState
from src.bills.utils import to_paise
from src.tools import bills as bill_tools
from src.tools import properties as property_tools

Ctx = Runtime[AgentContext]


# ---- 1. understand the request ----

def extract(state: BillSplitState) -> Command:
    request = extract_bill(state["prompt"])
    if request.amount is None:
        return Command(goto=END, update={"reply": messages.ASK_AMOUNT, "outcome": "done"})
    bill = {
        "item": request.item,
        "currency": request.currency,
        "total_paise": to_paise(request.amount),
        "property_hint": request.property_hint,
    }
    return Command(goto="resolve_property", update={"bill": bill})


# ---- 2. which property ----

def resolve_property(state: BillSplitState, runtime: Ctx) -> Command:
    client_id = runtime.context.client_id
    properties = property_tools.list_properties(client_id)
    if not properties:
        return Command(goto=END, update={"reply": messages.NO_PROPERTIES, "outcome": "done"})
    hint = state["bill"].get("property_hint")
    matches = property_tools.find_properties(client_id, hint) if hint else []
    if len(matches) == 1:
        return Command(goto="load_members", update={"property": matches[0]})
    candidates = sorted(matches or properties, key=lambda p: p["name"].lower())[:PROPERTY_LIST_MAX]
    return Command(goto="ask_property", update={"candidates": candidates})


def ask_property(state: BillSplitState, runtime: Ctx) -> dict:
    matched = bool(state["bill"].get("property_hint")) and len(state["candidates"]) > 1
    options = [Option(id=p["id"], title=p["name"]) for p in state["candidates"]]
    question = runtime.context.channel.ask_choice(
        messages.ask_property(state["bill"], matched), "Choose property", options
    )
    return {"waiting": {"stage": "choose_property", "message_ids": [question]}}


def wait_property(state: BillSplitState) -> Command:
    answer = interrupt(state["waiting"])
    chosen = next(
        (p for p in state["candidates"] if answer.get("type") == "choice" and p["id"] == answer.get("id")), None
    )
    if chosen is None:  # not one of the listed properties: keep waiting
        return Command(goto="wait_property")
    return Command(goto="load_members", update={"property": chosen})


# ---- 3. who shares it ----

def load_members(state: BillSplitState, runtime: Ctx) -> Command:
    ctx = runtime.context
    contacts = property_tools.list_member_contacts(ctx.client_id, state["property"]["id"], ctx.channel.owner_ids)
    members = as_poll_members(contacts)
    if not members:
        reply = messages.NO_MEMBERS.format(property=state["property"]["name"])
        return Command(goto=END, update={"reply": reply, "outcome": "done"})
    return Command(goto="ask_members", update={"members": members})


def ask_members(state: BillSplitState, runtime: Ctx) -> dict:
    """One multi-select poll; more if there are over 11 members (12 options per poll,
    the first one also offers ALL_OPTION)."""
    names = [m["name"] for m in state["members"]]
    chunks = [[ALL_OPTION, *names[: MEMBERS_PER_POLL - 1]]]
    rest = names[MEMBERS_PER_POLL - 1:]
    chunks += [rest[i: i + MEMBERS_PER_POLL] for i in range(0, len(rest), MEMBERS_PER_POLL)]
    if len(chunks[-1]) == 1 and len(chunks) > 1:  # a poll needs 2 options: move one over
        chunks[-1].insert(0, chunks[-2].pop())

    polls = {}
    for i, options in enumerate(chunks, start=1):
        question = messages.poll_question(state["bill"], i, len(chunks))
        poll_id = runtime.context.channel.ask_poll(question, options, multiple=True)
        polls[poll_id] = options
    waiting = {"stage": "choose_members", "message_ids": list(polls), "polls": polls}
    return {"polls": polls, "waiting": waiting}


def _selected(state: BillSplitState, names: list[str]) -> list[str]:
    """Member jids for the chosen poll options. ALL_OPTION means everyone."""
    if ALL_OPTION in names:
        return [m["jid"] for m in state["members"]]
    chosen = set(names)
    return [m["jid"] for m in state["members"] if m["name"] in chosen]


def wait_members(state: BillSplitState) -> Command:
    answer = interrupt(state["waiting"])
    selected = _selected(state, answer.get("selected", [])) if answer.get("type") == "poll" else []
    if not selected:
        return Command(goto="wait_members")
    return Command(goto="compute", update={"selected": selected})


# ---- 4. the split and the confirmation ----

def compute(state: BillSplitState) -> dict:
    chosen = set(state["selected"])
    members = [m for m in state["members"] if m["jid"] in chosen]
    return {"shares": bill_tools.split_bill(state["bill"]["total_paise"], members)}


def ask_confirm(state: BillSplitState, runtime: Ctx) -> dict:
    body = messages.confirm(state["bill"], state["property"]["name"], state["shares"])
    question = runtime.context.channel.ask_buttons(
        body, [Option(id=CONFIRM_YES, title="Yes, send"), Option(id=CONFIRM_NO, title="No")]
    )
    # The polls stay open: changing the vote now recalculates and asks again.
    polls = state["polls"]
    waiting = {"stage": "confirm", "message_ids": [question, *polls], "polls": polls}
    return {"waiting": waiting}


def wait_confirm(state: BillSplitState) -> Command:
    answer = interrupt(state["waiting"])
    if answer.get("type") == "poll":
        selected = _selected(state, answer.get("selected", []))
        return Command(goto="compute", update={"selected": selected}) if selected else Command(goto="wait_confirm")
    if answer.get("id") == CONFIRM_YES:
        return Command(goto="deliver")
    if answer.get("id") == CONFIRM_NO:
        return Command(goto=END, update={"reply": messages.CANCELLED, "outcome": "cancelled"})
    return Command(goto="wait_confirm")


# ---- 5. send it ----

def deliver(state: BillSplitState, runtime: Ctx, config: RunnableConfig) -> dict:
    """Message the group, then each person. Each share's delivery is saved as it
    goes, so if this node is retried nobody is messaged twice."""
    ctx = runtime.context
    bill, prop = state["bill"], state["property"]
    thread_id = config["configurable"]["thread_id"]

    record = bill_tools.get_bill_for_thread(thread_id) or bill_tools.record_bill(
        ctx.client_id, prop["id"], bill.get("item"), bill["currency"], bill["total_paise"],
        state["shares"], thread_id,
    )

    group_ok = record.get("group_delivery") == "sent"
    if not group_ok:
        try:
            ctx.channel.send_text(messages.group_notice(bill, record["shares"]), to=prop["group_jid"])
            group_ok = True
        except Exception:
            group_ok = False
        bill_tools.mark_group_notified(record["id"], group_ok)

    sent, failed = [], []
    for share in record["shares"]:
        if share["delivery"] == "sent":
            sent.append(share["name"])
            continue
        try:
            text = messages.personal_notice(bill, prop["name"], share, len(record["shares"]))
            ctx.channel.send_text(text, to=share["member_jid"])
            bill_tools.mark_member_notified(record["id"], share["member_jid"], ok=True)
            sent.append(share["name"])
        except Exception:
            bill_tools.mark_member_notified(record["id"], share["member_jid"], ok=False)
            failed.append(share["name"])
        time.sleep(DELIVERY_DELAY_SECONDS)

    bill_tools.mark_bill_sent(record["id"])
    return {"reply": messages.report(prop["name"], group_ok, sent, failed), "outcome": "done"}


def build_graph() -> StateGraph:
    """Uncompiled; Alfred adds it as a node and compiles it with the checkpointer."""
    graph = StateGraph(BillSplitState, context_schema=AgentContext)
    for node in (
        extract, resolve_property, ask_property, wait_property, load_members, ask_members,
        wait_members, compute, ask_confirm, wait_confirm, deliver,
    ):
        graph.add_node(node)
    graph.add_edge(START, "extract")
    graph.add_edge("ask_property", "wait_property")
    graph.add_edge("ask_members", "wait_members")
    graph.add_edge("compute", "ask_confirm")
    graph.add_edge("ask_confirm", "wait_confirm")
    graph.add_edge("deliver", END)
    return graph
