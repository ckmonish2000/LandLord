"""WhatsApp accounts linked by the signed-in user."""

from fastapi import APIRouter, Depends

from src.auth import dependencies as auth_dependencies
from src.whatsapp.dependencies import get_whatsapp_service
from src.whatsapp.schemas import AccountResponse
from src.whatsapp.service import WhatsappService

router = APIRouter(prefix="/accounts", tags=["whatsapp: accounts"])


@router.get("", response_model=list[AccountResponse])
def list_accounts(
    user: dict = Depends(auth_dependencies.get_current_user),
    service: WhatsappService = Depends(get_whatsapp_service),
):
    return service.list_accounts(user["id"])
