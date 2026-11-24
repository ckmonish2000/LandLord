from src.agents.alfred.constants import NAME, SIGNATURE
from src.agents.alfred.graph import build_graph


class AlfredAgent:
    """Supervisor: routes each message to a sub-agent and returns its reply."""

    name = NAME
    signature = SIGNATURE

    def run(self, prompt: str) -> str:
        result = build_graph().invoke({"prompt": prompt})
        return result["reply"]
