"""Groups of the user's linked WhatsApp account."""

from fastapi import APIRouter, Depends, Path

from src.auth import dependencies as auth_dependencies
from src.whatsapp.constants import GROUP_ID_PATTERN
from src.whatsapp.dependencies import get_whatsapp_service
from src.whatsapp.router.errors import whatsapp_http_errors
from src.whatsapp.schemas import GroupMemberResponse, GroupResponse
from src.whatsapp.service import WhatsappService

router = APIRouter(prefix="/groups", tags=["whatsapp: groups"])


@router.get("", response_model=list[GroupResponse])
def list_groups(
    user: dict = Depends(auth_dependencies.get_current_user),
    service: WhatsappService = Depends(get_whatsapp_service),
):
    with whatsapp_http_errors():
        return service.list_groups(user["id"])


@router.get("/{group_id}/members", response_model=list[GroupMemberResponse])
def list_group_members(
    group_id: str = Path(
        pattern=GROUP_ID_PATTERN,
        description="Group JID (120363012345678901@g.us) or just its number (120363012345678901)",
    ),
    user: dict = Depends(auth_dependencies.get_current_user),
    service: WhatsappService = Depends(get_whatsapp_service),
):
    with whatsapp_http_errors():
        return service.list_group_members(user["id"], group_id)
