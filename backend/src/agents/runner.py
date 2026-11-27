"""Starts and resumes agent runs, and keeps each conversation's record current.

The record (agent_conversations.json) is both the history of the conversation and
what lets an incoming answer find its paused run:

    message arrives      -> open()  (new thread_id, status running)
    on a worker thread   -> start()
    answer to a question -> find_waiting_on() -> resume()
"""

import threading
import uuid
from datetime import datetime, timezone

from src.agents.base import Agent, AgentContext, AgentResult, Answer
from src.agents.constants import ConversationStatus
from src.agents.repository import ConversationRepository

# One lock per thread, so a button tap and a poll vote can't resume the same run at once.
_locks: dict[str, threading.Lock] = {}
_locks_guard = threading.Lock()


def _lock(thread_id: str) -> threading.Lock:
    with _locks_guard:
        return _locks.setdefault(thread_id, threading.Lock())


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class ConversationRunner:
    def __init__(self, agent: Agent, conversations: ConversationRepository):
        self.agent = agent
        self.conversations = conversations

    def open(self, client_id: str, prompt: str, prompt_ref: dict) -> str:
        """Record a new conversation the moment the message arrives. Returns its thread_id.
        Done before any slow work, so even a failure on the way is in the history."""
        thread_id = str(uuid.uuid4())
        now = _now()
        self.conversations.save(thread_id, {
            "client_id": client_id,
            "agent": self.agent.name,
            "prompt": prompt,
            "response": None,
            "status": ConversationStatus.RUNNING,
            "stage": None,
            "error": None,
            "waiting": None,
            "votes": {},
            "prompt_ref": prompt_ref,
            "created_at": now,
            "updated_at": now,
            "completed_at": None,
        })
        return thread_id

    def start(self, thread_id: str, prompt: str, ctx: AgentContext) -> AgentResult:
        with _lock(thread_id):
            return self._run(thread_id, lambda: self.agent.start(thread_id, prompt, ctx))

    def resume(self, thread_id: str, question_id: str, answer: Answer, ctx: AgentContext) -> AgentResult | None:
        """Resume a paused run. Returns None if the run is no longer waiting on
        `question_id` (already answered, or moved on to another question)."""
        with _lock(thread_id):
            conversation = self.conversations.get_by_thread(thread_id)
            if not conversation or conversation["status"] != ConversationStatus.WAITING:
                return None
            if question_id not in (conversation.get("waiting") or {}).get("message_ids", []):
                return None
            self.conversations.save(thread_id, {"status": ConversationStatus.RUNNING, "updated_at": _now()})
            return self._run(thread_id, lambda: self.agent.resume(thread_id, answer, ctx))

    def find_waiting_on(self, client_id: str, message_id: str) -> dict | None:
        return self.conversations.find_waiting_on(client_id, message_id)

    def record_vote(self, thread_id: str, poll_id: str, selected: list[str]) -> list[str]:
        """Remember the options now chosen on one poll. Returns the choices across
        all of the run's polls (a long member list is split over several polls)."""
        with _lock(thread_id):
            conversation = self.conversations.get_by_thread(thread_id) or {}
            votes = {**conversation.get("votes", {}), poll_id: selected}
            self.conversations.save(thread_id, {"votes": votes, "updated_at": _now()})
        polls = (conversation.get("waiting") or {}).get("polls", {})
        return [name for pid in polls for name in votes.get(pid, [])]

    def mark_failed(self, thread_id: str, error: Exception | str) -> None:
        """For failures outside the agent, e.g. the reply could not be sent."""
        now = _now()
        self.conversations.save(thread_id, {
            "status": ConversationStatus.FAILED,
            "error": str(error),
            "waiting": None,
            "updated_at": now,
            "completed_at": now,
        })

    def _run(self, thread_id: str, call) -> AgentResult:
        try:
            result = call()
        except Exception as e:
            self.mark_failed(thread_id, e)
            raise
        now = _now()
        if result.waiting:
            fields = {
                "status": ConversationStatus.WAITING,
                "stage": result.waiting.get("stage"),
                "waiting": result.waiting,
            }
        else:
            status = ConversationStatus.CANCELLED if result.outcome == "cancelled" else ConversationStatus.DONE
            fields = {"status": status, "response": result.reply, "waiting": None, "completed_at": now}
        self.conversations.save(thread_id, {**fields, "updated_at": now})
        return result
