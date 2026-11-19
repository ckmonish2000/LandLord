"""Groups of the user's linked WhatsApp account."""

from fastapi import APIRouter, Depends, HTTPException, Path

from src.auth import dependencies as auth_dependencies
from src.whatsapp.constants import GROUP_ID_PATTERN
from src.whatsapp.dependencies import get_whatsapp_service
from src.whatsapp.exceptions import (
    GroupNotFound,
    NotGroupMember,
    NotLinked,
    NotReady,
    WhatsappRequestFailed,
)
from src.whatsapp.schemas import GroupMemberResponse, GroupResponse
from src.whatsapp.service import WhatsappService

router = APIRouter(prefix="/groups", tags=["whatsapp: groups"])


@router.get("", response_model=list[GroupResponse])
def list_groups(
    user: dict = Depends(auth_dependencies.get_current_user),
    service: WhatsappService = Depends(get_whatsapp_service),
):
    try:
        return service.list_groups(user["id"])
    except NotLinked:
        raise HTTPException(409, "WhatsApp is not linked for this user")
    except NotReady as e:
        raise HTTPException(503, str(e))
    except WhatsappRequestFailed as e:
        raise HTTPException(502, f"WhatsApp request failed: {e}")


@router.get("/{group_id}/members", response_model=list[GroupMemberResponse])
def list_group_members(
    group_id: str = Path(
        pattern=GROUP_ID_PATTERN,
        description="Group JID (120363012345678901@g.us) or just its number (120363012345678901)",
    ),
    user: dict = Depends(auth_dependencies.get_current_user),
    service: WhatsappService = Depends(get_whatsapp_service),
):
    try:
        return service.list_group_members(user["id"], group_id)
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
