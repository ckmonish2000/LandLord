"""All /whatsapp routes, split by feature. main.py includes `router` from here."""

from fastapi import APIRouter

from src.whatsapp.router import accounts, groups, linked_device

router = APIRouter(prefix="/whatsapp")
router.include_router(accounts.router)
router.include_router(linked_device.router)
router.include_router(groups.router)
