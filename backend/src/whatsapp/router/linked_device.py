"""Linking a user's WhatsApp account to the app (QR / pair code)."""

from fastapi import APIRouter, Depends, HTTPException, Response

from src.auth import dependencies as auth_dependencies
from src.whatsapp.dependencies import get_whatsapp_service
from src.whatsapp.exceptions import AlreadyLinked, NotReady
from src.whatsapp.schemas import PairCodeRequest
from src.whatsapp.service import WhatsappService

router = APIRouter(tags=["whatsapp: linked device"])


@router.get("/qr", responses={200: {"content": {"image/png": {}}}})
def get_qr(
    user: dict = Depends(auth_dependencies.get_current_user),
    service: WhatsappService = Depends(get_whatsapp_service),
):
    try:
        png = service.get_qr_png(user["id"])
    except AlreadyLinked as e:
        raise HTTPException(409, "WhatsApp is already linked for this user") from e
    except NotReady as e:
        raise HTTPException(503, str(e)) from e
    return Response(png, media_type="image/png", headers={"Cache-Control": "no-store"})


@router.post("/pair-code")
def generate_pair_code(
    body: PairCodeRequest,
    user: dict = Depends(auth_dependencies.get_current_user),
    service: WhatsappService = Depends(get_whatsapp_service),
):
    try:
        code = service.generate_pair_code(user["id"], body.phone)
    except AlreadyLinked as e:
        raise HTTPException(409, "WhatsApp is already linked for this user") from e
    except NotReady as e:
        raise HTTPException(503, str(e)) from e
    return {"code": code}
