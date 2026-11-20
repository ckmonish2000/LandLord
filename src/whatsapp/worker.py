"""Routes the linked user's own WhatsApp messages to an agent and replies,
using a thread pool so slow work stays off neonize's event threads.

Flow per message from me:
  1. save the request (status: processing) and react 👁️
  2. a worker thread runs the agent and replies (quoting the message)
  3. reaction becomes ✅ and the request is marked done,
     or ❌ and failed (with the error) if the agent or the reply fails.
A new reaction from the same sender replaces the old one, so 👁️ turns into ✅ / ❌.
"""

import logging
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime, timezone

from neonize.client import NewClient
from neonize.events import MessageEv
from neonize.proto.Neonize_pb2 import JID
from neonize.utils.jid import Jid2String
from neonize.utils.message import extract_text

from src.agents.base import Agent
from src.whatsapp.constants import (
    REACTION_DONE,
    REACTION_FAILED,
    REACTION_RECEIVED,
    WORKER_MAX_THREADS,
    RequestStatus,
)
from src.whatsapp.repository import AgentRequestRepository
from src.whatsapp.utils import format_agent_reply

log = logging.getLogger(__name__)

_executor = ThreadPoolExecutor(max_workers=WORKER_MAX_THREADS, thread_name_prefix="wa-worker")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class MessageTask:
    """Everything a worker needs to process one message."""

    request_id: str  # id of the agent request record
    client_id: str
    client: NewClient
    event: MessageEv  # original message, used to quote it in the reply
    chat: JID
    sender: JID
    message_id: str
    prompt: str


class MessageHandler:
    def __init__(self, repository: AgentRequestRepository, agent: Agent):
        self.repository = repository
        self.agent = agent

    def on_message(self, client_id: str, client: NewClient, event: MessageEv) -> None:
        """Called on neonize's thread for every message: keep it quick, hand off to a worker."""
        source = event.Info.MessageSource
        if not source.IsFromMe:
            return
        prompt = extract_text(event.Message).strip()
        if not prompt or prompt.startswith(self.agent.signature):
            return  # reactions/edits/media without text, or the agent's own reply

        record = self.repository.create({
            "client_id": client_id,
            "agent": self.agent.name,
            "chat_jid": Jid2String(source.Chat),
            "sender_jid": Jid2String(source.Sender),
            "message_id": event.Info.ID,
            "prompt": prompt,
            "response": None,
            "status": RequestStatus.PROCESSING,
            "error": None,
            "created_at": _now(),
            "completed_at": None,
        })
        task = MessageTask(
            request_id=record["id"],
            client_id=client_id,
            client=client,
            event=event,
            chat=source.Chat,
            sender=source.Sender,
            message_id=event.Info.ID,
            prompt=prompt,
        )
        self._react(task, REACTION_RECEIVED)
        _executor.submit(self._process, task)

    def _process(self, task: MessageTask) -> None:
        """Runs on a worker thread."""
        try:
            response = format_agent_reply(self.agent.signature, self.agent.run(task.prompt))
            task.client.reply_message(response, task.event)
        except Exception as e:
            log.exception("%s failed on message %s", self.agent.name, task.message_id)
            self._react(task, REACTION_FAILED)
            self.repository.update(task.request_id, {
                "status": RequestStatus.FAILED,
                "error": str(e),
                "completed_at": _now(),
            })
            return

        self._react(task, REACTION_DONE)
        self.repository.update(task.request_id, {
            "status": RequestStatus.DONE,
            "response": response,
            "completed_at": _now(),
        })

    def _react(self, task: MessageTask, emoji: str) -> None:
        """Set our reaction on the original message. Never raises."""
        try:
            task.client.send_message(
                task.chat,
                task.client.build_reaction(task.chat, task.sender, task.message_id, emoji),
            )
        except Exception:
            log.exception("could not react %s on message %s", emoji, task.message_id)

    @staticmethod
    def shutdown() -> None:
        """Stop accepting work and drop queued tasks; running ones finish on their own."""
        _executor.shutdown(wait=False, cancel_futures=True)
