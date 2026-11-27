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
    except NotLinked as e:
        raise HTTPException(409, "WhatsApp is not linked for this user") from e
    except NotReady as e:
        raise HTTPException(503, str(e)) from e
    except GroupNotFound as e:
        raise HTTPException(404, "Group not found") from e
    except NotGroupMember as e:
        raise HTTPException(403, "Your WhatsApp account is not a member of this group") from e
    except WhatsappRequestFailed as e:
        raise HTTPException(502, f"WhatsApp request failed: {e}") from e
