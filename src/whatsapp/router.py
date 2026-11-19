from fastapi import APIRouter, Depends, HTTPException, Response

from src.auth import dependencies as auth_dependencies
from src.whatsapp.dependencies import get_whatsapp_service
from src.whatsapp.exceptions import AlreadyLinked, NotLinked, NotReady, WhatsappRequestFailed
from src.whatsapp.schemas import GroupResponse, PairCodeRequest
from src.whatsapp.service import WhatsappService

router = APIRouter(prefix="/whatsapp", tags=["whatsapp"])


@router.get("/qr", responses={200: {"content": {"image/png": {}}}})
def get_qr(
    user: dict = Depends(auth_dependencies.get_current_user),
    service: WhatsappService = Depends(get_whatsapp_service),
):
    try:
        png = service.get_qr_png(user["id"])
    except AlreadyLinked:
        raise HTTPException(409, "WhatsApp is already linked for this user")
    except NotReady as e:
        raise HTTPException(503, str(e))
    return Response(png, media_type="image/png", headers={"Cache-Control": "no-store"})


@router.post("/pair-code")
def generate_pair_code(
    body: PairCodeRequest,
    user: dict = Depends(auth_dependencies.get_current_user),
    service: WhatsappService = Depends(get_whatsapp_service),
):
    try:
        code = service.generate_pair_code(user["id"], body.phone)
    except AlreadyLinked:
        raise HTTPException(409, "WhatsApp is already linked for this user")
    except NotReady as e:
        raise HTTPException(503, str(e))
    return {"code": code}


@router.get("/groups", response_model=list[GroupResponse])
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
