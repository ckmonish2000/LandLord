"""Alfred as a supervisor: a router node picks a sub-agent, the sub-agent produces
the reply, and the graph ends.

    START → route ─┬─ bill_split (subgraph, may pause for answers) → END
                   └─ general → END

Compiled with a checkpointer so a sub-agent can pause (interrupt) and be resumed
later on the same thread_id.

To add a sub-agent: add a route in constants/schemas, describe it in ROUTER_PROMPT,
and add its node to ROUTES.
"""

from functools import lru_cache

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from src.agents.alfred.constants import HELP, ROUTE_BILL_SPLIT, ROUTE_GENERAL
from src.agents.alfred.prompts import ROUTER_PROMPT
from src.agents.alfred.schemas import AlfredState, RouteDecision
from src.agents.base import AgentContext
from src.agents.bill_split.graph import build_graph as build_bill_split
from src.agents.checkpoint import get_checkpointer
from src.llm import get_llm


def route(state: AlfredState) -> AlfredState:
    """Classify the message with the LLM (temperature 0 for stable routing)."""
    router = get_llm(temperature=0).with_structured_output(RouteDecision)
    decision = router.invoke([SystemMessage(ROUTER_PROMPT), HumanMessage(state["prompt"])])
    return {"route": decision.route}


def general(state: AlfredState) -> AlfredState:
    return {"reply": HELP, "outcome": "done"}


@lru_cache
def build_graph() -> CompiledStateGraph:
    """Compiled once and shared; safe to invoke from several worker threads."""
    routes = {
        ROUTE_BILL_SPLIT: build_bill_split().compile(),  # inherits the checkpointer
        ROUTE_GENERAL: general,
    }
    graph = StateGraph(AlfredState, context_schema=AgentContext)
    graph.add_node("route", route)
    for name, node in routes.items():
        graph.add_node(name, node)
        graph.add_edge(name, END)
    graph.add_edge(START, "route")
    graph.add_conditional_edges("route", lambda s: s["route"], list(routes))
    return graph.compile(checkpointer=get_checkpointer())
