import time

from src.agents.alfred.constants import GREETING, NAME, SIGNATURE


class AlfredAgent:
    name = NAME
    signature = SIGNATURE

    def run(self, prompt: str) -> str:
        # Placeholder until the LangGraph graph is added (e.g. return graph.invoke(...)).
        time.sleep(4)
        return GREETING
