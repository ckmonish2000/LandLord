"""Maps WhatsApp service errors to HTTP errors. Shared by every route that talks to WhatsApp."""

from collections.abc import Iterator
from contextlib import contextmanager

from fastapi import HTTPException

from src.whatsapp.exceptions import (
    GroupNotFound,
    NotGroupMember,
    NotLinked,
    NotReady,
    WhatsappRequestFailed,
)


@contextmanager
def whatsapp_http_errors() -> Iterator[None]:
    try:
        yield
    except NotLinked:
        raise HTTPException(409, "WhatsApp is not linked for this user")
    except NotReady as e:
        raise HTTPException(503, str(e))
    except GroupNotFound:
        raise HTTPException(404, "Group not found")
    except NotGroupMember:
        raise HTTPException(403, "Your WhatsApp account is not a member of this group")
    except WhatsappRequestFailed as e:
        raise HTTPException(502, f"WhatsApp request failed: {e}")
