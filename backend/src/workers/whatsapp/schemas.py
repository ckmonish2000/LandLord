from dataclasses import dataclass

from neonize.client import NewClient

from src.agents.base import Answer


@dataclass(frozen=True)
class Resume:
    """Everything needed to continue a paused run."""

    client_id: str
    client: NewClient
    conversation: dict
    question_id: str  # the question that was answered
    answer: Answer
