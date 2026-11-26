"""Routes the linked user's own WhatsApp messages to the agent, on a thread pool so
slow work stays off neonize's event threads.

Only messages in the user's "Message yourself" chat are handled. Each one is:

  a new prompt (text)    → start a new agent run
  a list / button tap    → resume the run that asked that question
  a poll vote            → remember it; once the taps settle, resume that run
  our own poll / list    → ignored

Per prompt: save the request and react 👁️. A run either finishes (reply quoting the
prompt, reaction ✅, request done / cancelled), pauses to ask something (request
waiting, still 👁️), or fails (❌, request failed). A resumed run ends the same way,
against the original prompt.
"""

import logging
import threading
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime, timezone

from neonize.client import NewClient
from neonize.events import MessageEv
from neonize.proto.Neonize_pb2 import JID
from neonize.utils.message import extract_text

from src.agents.base import Agent, AgentContext, AgentResult, Answer, choice_answer, poll_answer
from src.agents.repository import ConversationRepository
from src.agents.runner import ConversationRunner
from src.whatsapp.channel import WhatsappChannel
from src.whatsapp.constants import (
    POLL_SETTLE_SECONDS,
    REACTION_DONE,
    REACTION_FAILED,
    REACTION_RECEIVED,
    WORKER_MAX_THREADS,
    RequestStatus,
)
from src.whatsapp.interactions import ChoiceReply, decode_vote, is_question, parse_choice, parse_poll_vote
from src.whatsapp.repository import AgentRequestRepository
from src.whatsapp.sender import WhatsappSender
from src.whatsapp.utils import format_agent_reply, to_jid

log = logging.getLogger(__name__)

_executor = ThreadPoolExecutor(max_workers=WORKER_MAX_THREADS, thread_name_prefix="wa-worker")

# thread_id -> timer that resumes the run once poll taps stop arriving
_vote_timers: dict[str, threading.Timer] = {}
_vote_timers_guard = threading.Lock()

QUESTION_CLOSED = "That question is no longer open."
SOMETHING_WRONG = "Sorry, something went wrong: {error}"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _plain(jid: JID) -> str:
    """'user@server' without the device part, safe to store and turn back into a JID."""
    return f"{jid.User}@{jid.Server}"


@dataclass(frozen=True)
class Resume:
    """Everything a worker needs to continue a paused run."""

    client_id: str
    client: NewClient
    conversation: dict
    question_id: str  # the question that was answered
    answer: Answer


class MessageHandler:
    def __init__(self, repository: AgentRequestRepository, agent: Agent, conversations: ConversationRepository):
        self.repository = repository
        self.agent = agent
        self.runner = ConversationRunner(agent, conversations)

    # ---- entry point (neonize's thread: keep it quick) ----

    def on_message(self, client_id: str, client: NewClient, event: MessageEv) -> None:
        source = event.Info.MessageSource
        if not source.IsFromMe or not self._is_self_chat(client, source.Chat):
            return
        message = event.Message
        if is_question(message):
            return
        if (choice := parse_choice(message)) is not None:
            self._on_choice(client_id, client, event, choice)
        elif message.HasField("pollUpdateMessage"):
            self._on_poll_vote(client_id, client, event)
        else:
            prompt = extract_text(message).strip()
            if prompt and not prompt.startswith(self.agent.signature):
                self._on_prompt(client_id, client, event, prompt)

    @staticmethod
    def _is_self_chat(client: NewClient, chat: JID) -> bool:
        """True for the user's own "Message yourself" chat.

        WhatsApp may address that chat by the phone number or by the account's @lid id.
        """
        me = client.get_me()
        own_ids = {me.JID.User, me.LID.User} - {""}
        return chat.User in own_ids

    # ---- new prompt ----

    def _on_prompt(self, client_id: str, client: NewClient, event: MessageEv, prompt: str) -> None:
        source = event.Info.MessageSource
        prompt_ref = {"chat": _plain(source.Chat), "sender": _plain(source.Sender), "message_id": event.Info.ID}
        record = self.repository.create({
            "client_id": client_id,
            "agent": self.agent.name,
            "chat_jid": prompt_ref["chat"],
            "sender_jid": prompt_ref["sender"],
            "message_id": event.Info.ID,
            "prompt": prompt,
            "response": None,
            "status": RequestStatus.PROCESSING,
            "error": None,
            "created_at": _now(),
            "completed_at": None,
        })
        sender = WhatsappSender(client)
        self._react(sender, prompt_ref, REACTION_RECEIVED)
        _executor.submit(self._start, client_id, client, event, prompt, record["id"], prompt_ref)

    def _start(self, client_id: str, client: NewClient, event: MessageEv, prompt: str, request_id: str, prompt_ref: dict) -> None:
        """Runs on a worker thread."""
        sender = WhatsappSender(client)
        try:
            result = self.runner.start(prompt, self._context(client_id, client, prompt_ref), request_id, prompt_ref)
        except Exception as e:
            self._fail(sender, request_id, prompt_ref, e)
            return
        self._finish(sender, request_id, prompt_ref, result, reply_to=event)

    # ---- answers to questions ----

    def _on_choice(self, client_id: str, client: NewClient, event: MessageEv, choice: ChoiceReply) -> None:
        conversation = self.runner.find_waiting_on(client_id, choice.question_id)
        if conversation is None:
            chat = _plain(event.Info.MessageSource.Chat)
            _executor.submit(self._say, WhatsappSender(client), chat, QUESTION_CLOSED)
            return
        job = Resume(client_id, client, conversation, choice.question_id, choice_answer(choice.choice_id))
        _executor.submit(self._resume, job)

    def _on_poll_vote(self, client_id: str, client: NewClient, event: MessageEv) -> None:
        poll_id = event.Message.pollUpdateMessage.pollCreationMessageKey.ID
        conversation = self.runner.find_waiting_on(client_id, poll_id)
        if conversation is None:
            return
        try:
            vote = parse_poll_vote(client, event)
        except Exception:
            log.exception("could not decrypt a vote on poll %s", poll_id)
            return
        options = conversation["waiting"]["polls"].get(poll_id, [])
        thread_id = conversation["thread_id"]
        selected = self.runner.record_vote(thread_id, poll_id, decode_vote(vote, options))

        job = Resume(client_id, client, conversation, poll_id, poll_answer(selected))
        self._settle(thread_id, (lambda: _executor.submit(self._resume, job)) if selected else None)

    @staticmethod
    def _settle(thread_id: str, action: Callable[[], object] | None) -> None:
        """Run `action` once no new vote has arrived for POLL_SETTLE_SECONDS.
        A new vote replaces the pending action; action=None just cancels it."""
        with _vote_timers_guard:
            if (pending := _vote_timers.pop(thread_id, None)) is not None:
                pending.cancel()
            if action is None:
                return
            timer = threading.Timer(POLL_SETTLE_SECONDS, action)
            timer.daemon = True
            _vote_timers[thread_id] = timer
            timer.start()

    def _resume(self, job: Resume) -> None:
        """Runs on a worker thread."""
        conversation = job.conversation
        prompt_ref, request_id = conversation["prompt_ref"], conversation["request_id"]
        sender = WhatsappSender(job.client)
        with _vote_timers_guard:
            _vote_timers.pop(conversation["thread_id"], None)
        try:
            ctx = self._context(job.client_id, job.client, prompt_ref)
            result = self.runner.resume(conversation["thread_id"], job.question_id, job.answer, ctx)
        except Exception as e:
            self._fail(sender, request_id, prompt_ref, e)
            return
        if result is not None:  # None: the run had already moved past this question
            self._finish(sender, request_id, prompt_ref, result)

    # ---- outcomes ----

    def _finish(
        self,
        sender: WhatsappSender,
        request_id: str,
        prompt_ref: dict,
        result: AgentResult,
        reply_to: MessageEv | None = None,
    ) -> None:
        if result.waiting:
            self.repository.update(request_id, {"status": RequestStatus.WAITING})
            return
        response = format_agent_reply(self.agent.signature, result.reply) if result.reply else None
        try:
            if response:
                sender.text(prompt_ref["chat"], response, reply_to=reply_to)
        except Exception as e:
            self._fail(sender, request_id, prompt_ref, e)
            return
        self._react(sender, prompt_ref, REACTION_DONE)
        status = RequestStatus.CANCELLED if result.outcome == "cancelled" else RequestStatus.DONE
        self.repository.update(request_id, {"status": status, "response": response, "completed_at": _now()})

    def _fail(self, sender: WhatsappSender, request_id: str, prompt_ref: dict, error: Exception) -> None:
        log.exception("%s failed on message %s", self.agent.name, prompt_ref["message_id"], exc_info=error)
        self._react(sender, prompt_ref, REACTION_FAILED)
        self._say(sender, prompt_ref["chat"], SOMETHING_WRONG.format(error=error))
        self.repository.update(request_id, {
            "status": RequestStatus.FAILED,
            "error": str(error),
            "completed_at": _now(),
        })

    # ---- helpers ----

    def _context(self, client_id: str, client: NewClient, prompt_ref: dict) -> AgentContext:
        me = client.get_me()
        channel = WhatsappChannel(
            WhatsappSender(client),
            chat=to_jid(prompt_ref["chat"]),
            signature=self.agent.signature,
            owner_ids={me.JID.User, me.LID.User} - {""},
        )
        return AgentContext(client_id=client_id, channel=channel)

    def _say(self, sender: WhatsappSender, chat: str, body: str) -> None:
        """Send Alfred a short note to the landlord. Never raises."""
        try:
            sender.text(chat, format_agent_reply(self.agent.signature, body))
        except Exception:
            log.exception("could not send a note to %s", chat)

    @staticmethod
    def _react(sender: WhatsappSender, prompt_ref: dict, emoji: str) -> None:
        """Set our reaction on the landlord's original message. Never raises."""
        try:
            sender.react(prompt_ref["chat"], prompt_ref["sender"], prompt_ref["message_id"], emoji)
        except Exception:
            log.exception("could not react %s on message %s", emoji, prompt_ref["message_id"])

    @staticmethod
    def shutdown() -> None:
        """Stop accepting work and drop queued tasks; running ones finish on their own."""
        with _vote_timers_guard:
            for timer in _vote_timers.values():
                timer.cancel()
            _vote_timers.clear()
        _executor.shutdown(wait=False, cancel_futures=True)
