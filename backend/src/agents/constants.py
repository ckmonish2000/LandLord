class ConversationStatus:
    """Life of one conversation (agent run) in agent_conversations.json."""

    RUNNING = "running"  # the agent is working on it
    WAITING = "waiting"  # the agent asked the landlord something and is paused
    DONE = "done"
    CANCELLED = "cancelled"  # the landlord said no (e.g. "don't send the bill")
    FAILED = "failed"

    FINISHED = (DONE, CANCELLED, FAILED)
