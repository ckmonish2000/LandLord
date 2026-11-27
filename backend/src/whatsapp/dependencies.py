from functools import lru_cache

from src.agents.repository import ConversationRepository
from src.whatsapp.repository import WhatsappAccountRepository
from src.whatsapp.service import WhatsappService
from src.workers.whatsapp import WhatsappWorker


@lru_cache
def get_whatsapp_service() -> WhatsappService:
    """The one WhatsApp service of this process. Cached because it owns live state:
    the worker's thread pool and poll timers (sessions live in whatsapp/sessions.py).
    FastAPI routes and the app's startup / shutdown all get this same instance."""
    # Imported here, not at the top: the agents' tools use the property service,
    # which depends on this module. Importing Alfred at call time breaks that cycle.
    from src.agents.alfred.agent import AlfredAgent

    return WhatsappService(WhatsappAccountRepository(), WhatsappWorker(AlfredAgent(), ConversationRepository()))
