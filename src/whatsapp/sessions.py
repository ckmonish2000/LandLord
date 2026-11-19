"""Runtime registry of neonize clients, one per client_id, each on its own thread.

Infrastructure only: it creates/starts/stops clients, captures QR codes and
forwards connection events to callbacks. Decisions and persistence live in
WhatsappService.
"""

import logging
import threading
from collections.abc import Callable

from neonize.client import NewClient
from neonize.events import ConnectedEv, LoggedOutEv, PairStatusEv
from neonize.proto.Neonize_pb2 import JID, Device

from src.config import settings
from src.whatsapp.config import whatsapp_settings

log = logging.getLogger(__name__)

settings.DATA_DIR.mkdir(exist_ok=True)

OnConnected = Callable[[str, Device], None]  # (client_id, me)
OnLoggedOut = Callable[[str, int], None]  # (client_id, reason)

_sessions: dict[str, "Session"] = {}
_registry_lock = threading.Lock()


class Session:
    def __init__(self, client_id: str, client: NewClient):
        self.client_id = client_id
        self.client = client
        self.latest_qr: str | None = None
        self.qr_ready = threading.Event()  # set once WhatsApp sends a QR
        self.connected = threading.Event()  # set while logged in and connected
        self.thread: threading.Thread | None = None

    def is_running(self) -> bool:
        return self.thread is not None and self.thread.is_alive()


def _register_handlers(s: Session, on_connected: OnConnected, on_logged_out: OnLoggedOut) -> None:
    c = s.client

    def on_qr(_: NewClient, data: bytes):
        s.latest_qr = data.decode()
        s.qr_ready.set()

    c.event.qr(on_qr)

    @c.event(PairStatusEv)
    def _on_pair(_: NewClient, ev: PairStatusEv):
        if ev.Status == PairStatusEv.SUCCESS:
            s.latest_qr = None
        else:
            log.warning("pairing failed for %s: %s", s.client_id, ev.Error)

    @c.event(ConnectedEv)
    def _on_connected(client: NewClient, _: ConnectedEv):
        s.latest_qr = None
        s.connected.set()
        on_connected(s.client_id, client.get_me())

    @c.event(LoggedOutEv)
    def _on_logged_out(client: NewClient, ev: LoggedOutEv):
        s.connected.clear()
        with _registry_lock:
            if _sessions.get(s.client_id) is s:
                del _sessions[s.client_id]
        # Stop from another thread so we don't stop the client inside its own callback.
        threading.Thread(target=client.stop, daemon=True).start()
        on_logged_out(s.client_id, ev.Reason)


def get_or_start(
    client_id: str,
    jid: JID | None,
    on_connected: OnConnected,
    on_logged_out: OnLoggedOut,
) -> Session:
    """Return the running session for client_id, or start one.

    jid resumes a stored WhatsApp session; None starts a fresh device to pair.
    """
    with _registry_lock:
        s = _sessions.get(client_id)
        if s and s.is_running():
            return s

        if jid is not None:
            client = NewClient(whatsapp_settings.WHATSAPP_DB, jid=jid)
        else:
            client = NewClient(whatsapp_settings.WHATSAPP_DB, uuid=client_id, new_device=True)

        s = Session(client_id, client)
        _register_handlers(s, on_connected, on_logged_out)
        s.thread = threading.Thread(target=client.connect, daemon=True, name=f"wa-{client_id}")
        s.thread.start()
        _sessions[client_id] = s
        return s


def stop_all() -> None:
    with _registry_lock:
        sessions = list(_sessions.values())
        _sessions.clear()
    for s in sessions:
        s.client.stop()
