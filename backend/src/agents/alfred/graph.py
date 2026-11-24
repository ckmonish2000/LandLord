"""Alfred as a supervisor: a router node picks a sub-agent, the sub-agent returns
the reply, and the graph ends.

    START → route ─┬─ bill_split → END
                   └─ general    → END

To add a sub-agent: add a route in constants/schemas, describe it in ROUTER_PROMPT,
add a node here and an entry in ROUTES.
"""

from functools import lru_cache

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from src.agents.alfred.constants import HELP, ROUTE_BILL_SPLIT, ROUTE_GENERAL
from src.agents.alfred.prompts import ROUTER_PROMPT
from src.agents.alfred.schemas import AlfredState, RouteDecision
from src.agents.bill_split.agent import BillSplitAgent
from src.llm import get_llm


def route(state: AlfredState) -> AlfredState:
    """Classify the message with the LLM (temperature 0 for stable routing)."""
    router = get_llm(temperature=0).with_structured_output(RouteDecision)
    decision = router.invoke([SystemMessage(ROUTER_PROMPT), HumanMessage(state["prompt"])])
    return {"route": decision.route}


def bill_split(state: AlfredState) -> AlfredState:
    return {"reply": BillSplitAgent().run(state["prompt"])}


def general(state: AlfredState) -> AlfredState:
    return {"reply": HELP}


ROUTES = {ROUTE_BILL_SPLIT: bill_split, ROUTE_GENERAL: general}


@lru_cache
def build_graph() -> CompiledStateGraph:
    """Compiled once and shared; safe to invoke from several worker threads."""
    graph = StateGraph(AlfredState)
    graph.add_node("route", route)
    for name, node in ROUTES.items():
        graph.add_node(name, node)
        graph.add_edge(name, END)
    graph.add_edge(START, "route")
    graph.add_conditional_edges("route", lambda s: s["route"], list(ROUTES))
    return graph.compile()
