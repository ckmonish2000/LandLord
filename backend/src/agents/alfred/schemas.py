from typing import TypedDict

from pydantic import BaseModel, Field

from src.agents.alfred.constants import Route


class RouteDecision(BaseModel):
    """The router's answer: which sub-agent should handle the message."""

    route: Route = Field(description="bill_split for splitting or sharing a bill or expense; general for anything else")


class AlfredState(TypedDict, total=False):
    """Data passed between graph nodes for one message."""

    prompt: str  # the landlord's message
    route: str  # a Route value, set by the router node
    reply: str  # set by whichever node handled the message
    outcome: str  # how the run ended: done | cancelled
