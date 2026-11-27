from src.agents.constants import ConversationStatus
from src.database import JsonCollection


class ConversationRepository(JsonCollection):
    """One record per conversation with an agent: from the landlord's message to
    the final reply, including every pause in between. This is the history of what
    the landlord asked and how it ended, and what lets an answer find its paused run.

    {id, thread_id, client_id, agent,
     prompt, response, status, stage, error,
     waiting, votes, prompt_ref,
     created_at, updated_at, completed_at}

    status: see ConversationStatus
    stage: the question it is paused on, e.g. "choose_members"
    response: the agent's final reply (without the channel's signature)
    waiting: the run's Waiting payload (message ids it waits on, poll options)
    votes: poll message id -> option names currently chosen on that poll
    prompt_ref: chat / sender / message id of the landlord's message, so the
        channel can react to it later. Stored as plain strings.
    """

    def __init__(self):
        super().__init__("agent_conversations")

    def get_by_thread(self, thread_id: str) -> dict | None:
        return self.find_one("thread_id", thread_id)

    def save(self, thread_id: str, fields: dict) -> dict:
        return self.upsert("thread_id", thread_id, fields)

    def find_waiting_on(self, client_id: str, message_id: str) -> dict | None:
        """The paused run of this landlord that is waiting on `message_id`, if any."""
        for c in self.find(client_id=client_id, status=ConversationStatus.WAITING):
            if message_id in (c.get("waiting") or {}).get("message_ids", []):
                return c
        return None
