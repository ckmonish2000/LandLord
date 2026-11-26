"""Contracts between agents and the outside world.

Agents never import WhatsApp. They talk through a Channel (implemented by
src/whatsapp/channel.py) and can pause to wait for the landlord's answer.

A run either finishes (AgentResult.reply) or pauses (AgentResult.waiting). A paused
run is resumed later with the landlord's answer, using the same thread_id.
"""

from dataclasses import dataclass
from typing import Any, Literal, Protocol, TypedDict


@dataclass(frozen=True)
class Option:
    """A choice offered to the landlord. `id` comes back when they pick it."""

    id: str
    title: str
    description: str = ""


class Channel(Protocol):
    """How an agent sends messages. The landlord's chat is the default recipient."""

    owner_ids: set[str]  # the landlord's own WhatsApp user ids (phone and lid), e.g. to leave them out of lists

    def send_text(self, body: str, to: str | None = None) -> str:
        """Send text to the landlord (to=None) or to a member / group jid. Returns the message id."""
        ...

    def ask_choice(self, body: str, button_text: str, options: list[Option]) -> str:
        """Ask the landlord to pick one option from a list. Returns the question's message id."""
        ...

    def ask_buttons(self, body: str, options: list[Option]) -> str:
        """Ask the landlord to tap one of up to 3 buttons. Returns the question's message id."""
        ...

    def ask_poll(self, question: str, options: list[str], multiple: bool = True) -> str:
        """Send the landlord a poll. Returns the poll's message id."""
        ...


@dataclass(frozen=True)
class AgentContext:
    """Per-run dependencies. Not saved with the conversation state."""

    client_id: str  # the app user (landlord) the message belongs to
    channel: Channel


class Waiting(TypedDict, total=False):
    """What a paused run is waiting for (the payload of its interrupt)."""

    stage: str  # e.g. "choose_property"; shown in the conversation record
    message_ids: list[str]  # an answer to any of these messages resumes the run
    polls: dict[str, list[str]]  # poll message id -> option names, to decode votes


class ChoiceAnswer(TypedDict):
    type: Literal["choice"]
    id: str  # the picked option / button id


class PollAnswer(TypedDict):
    type: Literal["poll"]
    selected: list[str]  # names of every option currently chosen, across the run's polls


Answer = ChoiceAnswer | PollAnswer


@dataclass(frozen=True)
class AgentResult:
    thread_id: str
    reply: str | None = None  # final message for the landlord; None while waiting
    waiting: Waiting | None = None  # set when the run is paused
    outcome: str | None = None  # how a finished run ended, e.g. "done", "cancelled"


class Agent(Protocol):
    name: str  # stable id, stored with each request, e.g. "alfred"
    signature: str  # header shown above its messages, e.g. "🎩 *Alfred*"

    def start(self, thread_id: str, prompt: str, ctx: AgentContext) -> AgentResult:
        """Handle a new message. Blocking is fine (runs on a worker thread)."""
        ...

    def resume(self, thread_id: str, answer: Answer, ctx: AgentContext) -> AgentResult:
        """Continue a paused run with the landlord's answer."""
        ...


def choice_answer(option_id: str) -> ChoiceAnswer:
    return {"type": "choice", "id": option_id}


def poll_answer(selected: list[str]) -> PollAnswer:
    return {"type": "poll", "selected": selected}
