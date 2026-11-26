from src.database import JsonCollection


class ConversationRepository(JsonCollection):
    """One record per agent run (thread). Tells the worker whether an incoming
    message answers a paused run, and which one.

    {id, thread_id, client_id, agent, status, stage, waiting, votes,
     request_id, prompt_ref, created_at, updated_at}

    status: running | waiting | done | cancelled | failed
    waiting: the run's Waiting payload (message ids it waits on, poll options)
    votes: poll message id -> option names currently chosen on that poll
    prompt_ref: chat / sender / message id of the landlord's original message (for reactions)
    """

    def __init__(self):
        super().__init__("agent_conversations")

    def get_by_thread(self, thread_id: str) -> dict | None:
        return self.find_one("thread_id", thread_id)

    def save(self, thread_id: str, fields: dict) -> dict:
        return self.upsert("thread_id", thread_id, fields)

    def find_waiting_on(self, client_id: str, message_id: str) -> dict | None:
        """The paused run of this landlord that is waiting on `message_id`, if any."""
        for c in self.find(client_id=client_id, status="waiting"):
            if message_id in (c.get("waiting") or {}).get("message_ids", []):
                return c
        return None
