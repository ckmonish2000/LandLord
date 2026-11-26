from src.agents.repository import ConversationRepository
from src.whatsapp.repository import AgentRequestRepository, WhatsappAccountRepository
from src.whatsapp.service import WhatsappService
from src.whatsapp.worker import MessageHandler


def get_whatsapp_service() -> WhatsappService:
    # Imported here, not at the top: the agents' tools use the property service,
    # which depends on this module. Importing Alfred at call time breaks that cycle.
    from src.agents.alfred.agent import AlfredAgent

    return WhatsappService(
        WhatsappAccountRepository(),
        MessageHandler(AgentRequestRepository(), AlfredAgent(), ConversationRepository()),
    )
