QR_WAIT_SECONDS = 15  # how long to wait for WhatsApp to send the first QR
CONNECT_WAIT_SECONDS = 15  # how long to wait for a linked account to (re)connect

class RequestStatus:
    """Status of an agent request record."""

    PROCESSING = "processing"
    DONE = "done"
    FAILED = "failed"


WORKER_MAX_THREADS = 4
REACTION_RECEIVED = "👁️"
REACTION_DONE = "✅"
REACTION_FAILED = "❌"

GROUP_SERVER = "g.us"
# 120363012345678901, old-style 919876543210-1612345678, optionally ending in @g.us
GROUP_ID_PATTERN = r"^\d+(-\d+)?(@g\.us)?$"

# Error texts whatsmeow returns from get_group_info
ERR_GROUP_NOT_FOUND = "that group does not exist"
ERR_NOT_GROUP_MEMBER = "you're not participating in that group"


class AccountStatus:
    CONNECTED = "connected"
    LOGGED_OUT = "logged_out"
