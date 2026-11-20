from typing import Protocol


class Agent(Protocol):
    """What every agent must provide."""

    name: str  # stable id, stored with each request, e.g. "alfred"
    signature: str  # header shown above its replies, e.g. "🎩 *Alfred*"

    def run(self, prompt: str) -> str:
        """Handle one prompt and return the reply body. Raise on failure.

        Called on a worker thread, so blocking work (LLM calls, graph.invoke) is fine.
        """
        ...
