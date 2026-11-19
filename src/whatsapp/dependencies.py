from src.whatsapp.repository import WhatsappAccountRepository
from src.whatsapp.service import WhatsappService


def get_whatsapp_service() -> WhatsappService:
    return WhatsappService(WhatsappAccountRepository())
