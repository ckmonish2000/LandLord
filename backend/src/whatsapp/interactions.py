"""Reading the landlord's answers to questions we sent: list picks, button taps
and poll votes. Pure parsing, no business logic.

A list pick or button tap comes back as a new message that points at our question
(contextInfo.stanzaID) and carries the chosen id. A poll vote comes back as an
encrypted pollUpdateMessage that points at the poll and carries SHA-256 hashes of
the chosen option names.
"""

import hashlib
import json
from dataclasses import dataclass

from neonize.client import NewClient
from neonize.events import MessageEv
from neonize.proto.waE2E.WAWebProtobufsE2E_pb2 import Message


@dataclass(frozen=True)
class ChoiceReply:
    question_id: str  # id of the list / buttons message that was answered
    choice_id: str  # id of the row or button tapped


@dataclass(frozen=True)
class PollVote:
    poll_id: str  # id of the poll message
    selected_hashes: tuple[bytes, ...]  # SHA-256 of each chosen option name; empty = vote removed


def option_hash(name: str) -> bytes:
    """How WhatsApp identifies a poll option in a vote."""
    return hashlib.sha256(name.encode()).digest()


def decode_vote(vote: PollVote, options: list[str]) -> list[str]:
    """Turn a vote's hashes back into option names, in the poll's order."""
    chosen = set(vote.selected_hashes)
    return [name for name in options if option_hash(name) in chosen]


def parse_choice(message: Message) -> ChoiceReply | None:
    """A tap on a list row or reply button, in any of the formats WhatsApp uses."""
    if message.HasField("interactiveResponseMessage"):
        reply = message.interactiveResponseMessage
        try:
            params = json.loads(reply.nativeFlowResponseMessage.paramsJSON or "{}")
        except json.JSONDecodeError:
            return None
        choice_id = params.get("id")
        if not choice_id:
            return None
        return ChoiceReply(reply.contextInfo.stanzaID, str(choice_id))
    if message.HasField("buttonsResponseMessage"):
        reply = message.buttonsResponseMessage
        return ChoiceReply(reply.contextInfo.stanzaID, reply.selectedButtonID)
    if message.HasField("listResponseMessage"):
        reply = message.listResponseMessage
        return ChoiceReply(reply.contextInfo.stanzaID, reply.singleSelectReply.selectedRowID)
    if message.HasField("templateButtonReplyMessage"):
        reply = message.templateButtonReplyMessage
        return ChoiceReply(reply.contextInfo.stanzaID, reply.selectedID)
    return None


def parse_poll_vote(client: NewClient, event: MessageEv) -> PollVote | None:
    """Decrypt a poll vote. Raises if WhatsApp's decryption fails."""
    if not event.Message.HasField("pollUpdateMessage"):
        return None
    vote = client.decrypt_poll_vote(event)
    poll_id = event.Message.pollUpdateMessage.pollCreationMessageKey.ID
    return PollVote(poll_id, tuple(vote.selectedOptions))


def is_question(message: Message) -> bool:
    """Polls, lists and button messages: things we send, never prompts for an agent."""
    return any(
        message.HasField(field)
        for field in (
            "interactiveMessage",
            "pollCreationMessage",
            "pollCreationMessageV2",
            "pollCreationMessageV3",
            "pollCreationMessageV4",
            "pollCreationMessageV5",
            "pollCreationMessageV6",
        )
    )
