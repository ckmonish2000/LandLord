from src.agents.alfred.agent import AlfredAgent
from src.whatsapp.worker import MessageHandler
from src.whatsapp.repository import AgentRequestRepository, WhatsappAccountRepository
from src.whatsapp.service import WhatsappService


def get_whatsapp_service() -> WhatsappService:
    return WhatsappService(
        WhatsappAccountRepository(),
        MessageHandler(AgentRequestRepository(), AlfredAgent()),
    )
