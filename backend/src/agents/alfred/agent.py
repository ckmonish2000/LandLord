from langgraph.types import Command

from src.agents.alfred.constants import NAME, SIGNATURE
from src.agents.alfred.graph import build_graph
from src.agents.base import AgentContext, AgentResult, Answer


class AlfredAgent:
    """Supervisor: routes each message to a sub-agent. A run may pause to ask the
    landlord something; resume() continues it with their answer."""

    name = NAME
    signature = SIGNATURE

    def start(self, thread_id: str, prompt: str, ctx: AgentContext) -> AgentResult:
        return self._invoke(thread_id, {"prompt": prompt}, ctx)

    def resume(self, thread_id: str, answer: Answer, ctx: AgentContext) -> AgentResult:
        return self._invoke(thread_id, Command(resume=answer), ctx)

    @staticmethod
    def _invoke(thread_id: str, graph_input, ctx: AgentContext) -> AgentResult:
        config = {"configurable": {"thread_id": thread_id}}
        state = build_graph().invoke(graph_input, config, context=ctx)
        if interrupts := state.get("__interrupt__"):
            return AgentResult(thread_id=thread_id, waiting=interrupts[0].value)
        return AgentResult(thread_id=thread_id, reply=state.get("reply"), outcome=state.get("outcome"))
