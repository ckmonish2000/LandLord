"""Starts and resumes agent runs and keeps each run's conversation record current.

The record is what lets an incoming answer find its paused run:
    new text            -> start()   (new thread_id)
    answer to a question -> find_waiting_on() -> resume()
"""

import threading
import uuid
from datetime import datetime, timezone

from src.agents.base import Agent, AgentContext, AgentResult, Answer
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

    def start(self, prompt: str, ctx: AgentContext, request_id: str, prompt_ref: dict) -> AgentResult:
        thread_id = str(uuid.uuid4())
        now = _now()
        self.conversations.save(thread_id, {
            "client_id": ctx.client_id,
            "agent": self.agent.name,
            "status": "running",
            "stage": None,
            "waiting": None,
            "votes": {},
            "request_id": request_id,
            "prompt_ref": prompt_ref,
            "created_at": now,
            "updated_at": now,
        })
        with _lock(thread_id):
            return self._run(thread_id, lambda: self.agent.start(thread_id, prompt, ctx))

    def resume(self, thread_id: str, question_id: str, answer: Answer, ctx: AgentContext) -> AgentResult | None:
        """Resume a paused run. Returns None if the run is no longer waiting on
        `question_id` (already answered, or moved on to another question)."""
        with _lock(thread_id):
            conversation = self.conversations.get_by_thread(thread_id)
            if not conversation or conversation["status"] != "waiting":
                return None
            if question_id not in (conversation.get("waiting") or {}).get("message_ids", []):
                return None
            self.conversations.save(thread_id, {"status": "running", "updated_at": _now()})
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

    def _run(self, thread_id: str, call) -> AgentResult:
        try:
            result = call()
        except Exception as e:
            self.conversations.save(thread_id, {"status": "failed", "error": str(e), "updated_at": _now()})
            raise
        if result.waiting:
            fields = {"status": "waiting", "stage": result.waiting.get("stage"), "waiting": result.waiting}
        else:
            fields = {"status": result.outcome or "done", "waiting": None}
        self.conversations.save(thread_id, {**fields, "updated_at": _now()})
        return result
