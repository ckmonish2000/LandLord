import io
import logging
from datetime import datetime, timezone

import segno
from neonize.proto.Neonize_pb2 import JID, ContactInfo, Device, GetProfilePictureParams
from neonize.utils.jid import Jid2String

from src.whatsapp import sessions
from src.whatsapp.constants import (
    CONNECT_WAIT_SECONDS,
    ERR_GROUP_NOT_FOUND,
    ERR_NOT_GROUP_MEMBER,
    QR_WAIT_SECONDS,
    AccountStatus,
)
from src.whatsapp.exceptions import (
    AlreadyLinked,
    GroupNotFound,
    NotGroupMember,
    NotLinked,
    NotReady,
    WhatsappRequestFailed,
)
from src.whatsapp.repository import WhatsappAccountRepository
from src.whatsapp.utils import (
    contacts_by_jid,
    find_contact,
    group_jid,
    group_to_dict,
    member_to_dict,
)

log = logging.getLogger(__name__)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class WhatsappService:
    def __init__(self, repository: WhatsappAccountRepository):
        self.repository = repository

    # ---- linking ----

    def get_qr_png(self, client_id: str) -> bytes:
        s = self._session_awaiting_pairing(client_id)
        if not s.latest_qr:
            raise NotReady("QR not available, retry in a few seconds")
        buf = io.BytesIO()
        segno.make_qr(s.latest_qr).save(buf, kind="png", scale=8, border=2)
        return buf.getvalue()

    def generate_pair_code(self, client_id: str, phone: str) -> str:
        s = self._session_awaiting_pairing(client_id)
        try:
            return s.client.PairPhone(phone, show_push_notification=True)
        except Exception as e:
            raise NotReady(str(e)) from e

    # ---- groups ----

    def list_groups(self, client_id: str) -> list[dict]:
        s = self._connected_session(client_id)
        try:
            groups = s.client.get_joined_groups()
        except Exception as e:
            raise WhatsappRequestFailed(str(e)) from e
        return [
            group_to_dict(g, self._picture_url(s, g.JID, is_community=g.GroupParent.IsParent))
            for g in groups
        ]

    def list_group_members(self, client_id: str, group_id: str) -> list[dict]:
        s = self._connected_session(client_id)
        try:
            info = s.client.get_group_info(group_jid(group_id))
        except Exception as e:
            msg = str(e)
            if ERR_GROUP_NOT_FOUND in msg:
                raise GroupNotFound() from e
            if ERR_NOT_GROUP_MEMBER in msg:
                raise NotGroupMember() from e
            raise WhatsappRequestFailed(msg) from e
        contacts = self._contacts(s)
        return [
            member_to_dict(p, self._picture_url(s, p.JID), find_contact(p, contacts))
            for p in info.Participants
        ]

    def _contacts(self, s: sessions.Session) -> dict[str, ContactInfo]:
        """The linked account's local contact store (names synced from the phone)."""
        try:
            return contacts_by_jid(s.client.contact.get_all_contacts())
        except Exception as e:  # names are optional; never fail the request over them
            log.warning("could not read contacts for %s: %s", s.client_id, e)
            return {}

    def _picture_url(self, s: sessions.Session, jid: JID, is_community: bool = False) -> str | None:
        """DP URL of a group or user, or None if there's no photo or it isn't visible to us."""
        try:
            pic = s.client.get_profile_picture(jid, GetProfilePictureParams(IsCommunity=is_community))
        except Exception as e:  # no photo set, or hidden by the person's privacy settings
            log.debug("no picture for %s: %s", jid.User, e)
            return None
        return pic.URL or None

    # ---- lifecycle ----

    def restore_all(self) -> None:
        """Reconnect every account that was linked before the server restarted."""
        for account in self.repository.get_all():
            if account.get("status") == AccountStatus.CONNECTED:
                self._start_session(account["client_id"])

    def stop_all(self) -> None:
        sessions.stop_all()

    # ---- internals ----

    def _is_linked(self, client_id: str) -> bool:
        account = self.repository.get_by_client_id(client_id)
        return bool(account and account.get("status") == AccountStatus.CONNECTED)

    def _start_session(self, client_id: str) -> sessions.Session:
        """Resume the user's linked account, or start a fresh device to pair."""
        account = self.repository.get_by_client_id(client_id)
        jid = None
        if account and account.get("status") == AccountStatus.CONNECTED:
            jid = JID(
                User=account["phone"],
                Server=account["server"],
                Device=account["device"],
                RawAgent=0,
                Integrator=0,
                IsEmpty=False,
            )
        return sessions.get_or_start(client_id, jid, self._on_connected, self._on_logged_out)

    def _session_awaiting_pairing(self, client_id: str) -> sessions.Session:
        """Start (or reuse) the user's session and wait until WhatsApp is ready to pair."""
        if self._is_linked(client_id):
            raise AlreadyLinked()
        s = self._start_session(client_id)
        if s.client.is_logged_in:
            raise AlreadyLinked()
        if not s.qr_ready.wait(QR_WAIT_SECONDS):
            raise NotReady("WhatsApp did not respond in time, retry in a few seconds")
        return s

    def _connected_session(self, client_id: str) -> sessions.Session:
        """Return the user's linked session once it is connected (resuming it if needed)."""
        if not self._is_linked(client_id):
            raise NotLinked()
        s = self._start_session(client_id)
        if not s.connected.wait(CONNECT_WAIT_SECONDS):
            raise NotReady("WhatsApp is still connecting, retry in a few seconds")
        return s

    # ---- event callbacks (called from the session's thread) ----

    def _on_connected(self, client_id: str, me: Device) -> None:
        now = _now()
        existing = self.repository.get_by_client_id(client_id)
        self.repository.save(client_id, {
            "jid": Jid2String(me.JID),
            "phone": me.JID.User,
            "server": me.JID.Server,
            "device": me.JID.Device,
            "lid": Jid2String(me.LID) if me.LID.User else None,
            "push_name": me.PushName,
            "business_name": me.BussinessName,
            "platform": me.Platform,
            "status": AccountStatus.CONNECTED,
            "linked_at": (existing or {}).get("linked_at") or now,
            "last_connected_at": now,
        })
        log.info("whatsapp connected for %s as %s", client_id, me.JID.User)

    def _on_logged_out(self, client_id: str, reason: int) -> None:
        self.repository.save(client_id, {"status": AccountStatus.LOGGED_OUT, "logged_out_at": _now()})
        log.info("whatsapp logged out for %s (reason %s)", client_id, reason)
