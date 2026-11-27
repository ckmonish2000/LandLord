"""WhatsApp worker: routes the landlord's own WhatsApp messages to the agent, on a
thread pool so slow work stays off neonize's event threads.

Only messages in the landlord's "Message yourself" chat are handled. Each one is:

  a new prompt (text)    → start a new agent run
  a list / button tap    → resume the run that asked that question
  a poll vote            → remember it; once the taps settle, resume that run
  our own poll / list    → ignored

Per prompt: record the conversation (agent_conversations.json, via the runner) and
react 👁️. A run either finishes (reply quoting the prompt, reaction ✅), pauses to ask
something (still 👁️), or fails (❌ and a short note). A resumed run ends the same way,
against the original prompt. The runner keeps the conversation's status.
"""

import logging
from concurrent.futures import ThreadPoolExecutor

from neonize.client import NewClient
from neonize.events import MessageEv
from neonize.proto.Neonize_pb2 import JID
from neonize.utils.message import extract_text

from src.agents.base import Agent, AgentContext, AgentResult, choice_answer, poll_answer
from src.agents.repository import ConversationRepository
from src.agents.runner import ConversationRunner
from src.whatsapp.channel import WhatsappChannel
from src.whatsapp.interactions import ChoiceReply, decode_vote, is_question, parse_choice, parse_poll_vote
from src.whatsapp.sender import WhatsappSender
from src.whatsapp.utils import format_agent_reply, to_jid
from src.workers.whatsapp.constants import (
    POLL_SETTLE_SECONDS,
    QUESTION_CLOSED,
    REACTION_DONE,
    REACTION_FAILED,
    REACTION_RECEIVED,
    SOMETHING_WRONG,
    WHATSAPP_MAX_THREADS,
)
from src.workers.whatsapp.schemas import Resume
from src.workers.whatsapp.utils import VoteSettler, plain_jid

log = logging.getLogger(__name__)


class WhatsappWorker:
    """One per process (see src/whatsapp/dependencies.py): it owns the thread pool and
    the pending poll timers."""

    def __init__(self, agent: Agent, conversations: ConversationRepository):
        self.agent = agent
        self.runner = ConversationRunner(agent, conversations)
        self._executor = ThreadPoolExecutor(max_workers=WHATSAPP_MAX_THREADS, thread_name_prefix="wa-worker")
        self._votes = VoteSettler(POLL_SETTLE_SECONDS)

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
        """True for the landlord's own "Message yourself" chat.

        WhatsApp may address that chat by the phone number or by the account's @lid id.
        """
        me = client.get_me()
        own_ids = {me.JID.User, me.LID.User} - {""}
        return chat.User in own_ids

    # ---- new prompt ----

    def _on_prompt(self, client_id: str, client: NewClient, event: MessageEv, prompt: str) -> None:
        source = event.Info.MessageSource
        prompt_ref = {"chat": plain_jid(source.Chat), "sender": plain_jid(source.Sender), "message_id": event.Info.ID}
        thread_id = self.runner.open(client_id, prompt, prompt_ref)
        self._react(WhatsappSender(client), prompt_ref, REACTION_RECEIVED)
        self._executor.submit(self._start, client_id, client, event, prompt, thread_id, prompt_ref)

    def _start(
        self, client_id: str, client: NewClient, event: MessageEv, prompt: str, thread_id: str, prompt_ref: dict
    ) -> None:
        """Runs on a worker thread."""
        sender = WhatsappSender(client)
        try:
            result = self.runner.start(thread_id, prompt, self._context(client_id, client, prompt_ref))
        except Exception as e:
            self._fail(sender, thread_id, prompt_ref, e)
            return
        self._finish(sender, thread_id, prompt_ref, result, reply_to=event)

    # ---- answers to questions ----

    def _on_choice(self, client_id: str, client: NewClient, event: MessageEv, choice: ChoiceReply) -> None:
        conversation = self.runner.find_waiting_on(client_id, choice.question_id)
        if conversation is None:
            chat = plain_jid(event.Info.MessageSource.Chat)
            self._executor.submit(self._say, WhatsappSender(client), chat, QUESTION_CLOSED)
            return
        job = Resume(client_id, client, conversation, choice.question_id, choice_answer(choice.choice_id))
        self._executor.submit(self._resume, job)

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

        if not selected:  # every option unticked: wait for a new choice
            self._votes.cancel(thread_id)
            return
        job = Resume(client_id, client, conversation, poll_id, poll_answer(selected))
        self._votes.settle(thread_id, lambda: self._executor.submit(self._resume, job))

    def _resume(self, job: Resume) -> None:
        """Runs on a worker thread."""
        thread_id, prompt_ref = job.conversation["thread_id"], job.conversation["prompt_ref"]
        sender = WhatsappSender(job.client)
        self._votes.cancel(thread_id)  # e.g. Yes was tapped while a vote was still settling
        try:
            ctx = self._context(job.client_id, job.client, prompt_ref)
            result = self.runner.resume(thread_id, job.question_id, job.answer, ctx)
        except Exception as e:
            self._fail(sender, thread_id, prompt_ref, e)
            return
        if result is not None:  # None: the run had already moved past this question
            self._finish(sender, thread_id, prompt_ref, result)

    # ---- outcomes ----

    def _finish(
        self,
        sender: WhatsappSender,
        thread_id: str,
        prompt_ref: dict,
        result: AgentResult,
        reply_to: MessageEv | None = None,
    ) -> None:
        """Send the final reply. The runner has already recorded the outcome."""
        if result.waiting:
            return  # the agent sent its question; nothing to reply yet
        try:
            if result.reply:
                reply = format_agent_reply(self.agent.signature, result.reply)
                sender.text(prompt_ref["chat"], reply, reply_to=reply_to)
        except Exception as e:
            self._fail(sender, thread_id, prompt_ref, e)
            return
        self._react(sender, prompt_ref, REACTION_DONE)

    def _fail(self, sender: WhatsappSender, thread_id: str, prompt_ref: dict, error: Exception) -> None:
        log.exception("%s failed on message %s", self.agent.name, prompt_ref["message_id"], exc_info=error)
        self.runner.mark_failed(thread_id, error)
        self._react(sender, prompt_ref, REACTION_FAILED)
        self._say(sender, prompt_ref["chat"], SOMETHING_WRONG.format(error=error))

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
        """Send the landlord a short note from the agent. Never raises."""
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

    def shutdown(self) -> None:
        """Stop accepting work and drop queued tasks; running ones finish on their own."""
        self._votes.shutdown()
        self._executor.shutdown(wait=False, cancel_futures=True)
