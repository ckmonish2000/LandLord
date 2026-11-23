"""Outgoing WhatsApp messages for one linked account.

A thin layer over neonize's client with one method per message type, so callers
(service, worker, agents) share the same signatures. No business logic here.

    sender = WhatsappSender(session.client)
    sender.text("919876543210", "Rent is due on the 5th")
    sender.poll("120363012345678901@g.us", "Water tank cleaning on", ["Saturday", "Sunday"])
    sender.image(group_jid, png_bytes, caption="New parking layout")

`to` accepts a JID or a string: a phone number, "…@s.whatsapp.net", "…@g.us" or "…@lid".
`reply_to` is a received message (MessageEv); the new message quotes it.
Every send returns the WhatsApp message id. Failures raise WhatsappRequestFailed.
"""

from collections.abc import Callable

from neonize.client import NewClient
from neonize.events import MessageEv
from neonize.proto.Neonize_pb2 import JID, SendResponse
from neonize.utils.enum import VoteType

from src.whatsapp.constants import POLL_MAX_OPTIONS, POLL_MIN_OPTIONS
from src.whatsapp.exceptions import WhatsappRequestFailed
from src.whatsapp.utils import to_jid

Recipient = str | JID
Media = bytes | str  # file contents, or a local path / URL


class WhatsappSender:
    def __init__(self, client: NewClient):
        self.client = client

    # ---- text ----

    def text(self, to: Recipient, body: str, reply_to: MessageEv | None = None, link_preview: bool = False) -> str:
        jid = to_jid(to)
        if reply_to is not None:
            return self._send(lambda: self.client.reply_message(body, reply_to, to=jid, link_preview=link_preview))
        return self._send(lambda: self.client.send_message(jid, body, link_preview=link_preview))

    # ---- media ----

    def image(
        self,
        to: Recipient,
        file: Media,
        caption: str | None = None,
        reply_to: MessageEv | None = None,
        view_once: bool = False,
    ) -> str:
        return self._send(
            lambda: self.client.send_image(to_jid(to), file, caption=caption, quoted=reply_to, viewonce=view_once)
        )

    def video(
        self,
        to: Recipient,
        file: Media,
        caption: str | None = None,
        reply_to: MessageEv | None = None,
        view_once: bool = False,
    ) -> str:
        return self._send(
            lambda: self.client.send_video(to_jid(to), file, caption=caption, quoted=reply_to, viewonce=view_once)
        )

    def audio(self, to: Recipient, file: Media, voice_note: bool = False, reply_to: MessageEv | None = None) -> str:
        """voice_note=True sends it as a recorded voice message instead of an audio file."""
        return self._send(lambda: self.client.send_audio(to_jid(to), file, ptt=voice_note, quoted=reply_to))

    def document(
        self,
        to: Recipient,
        file: Media,
        filename: str | None = None,
        caption: str | None = None,
        mimetype: str | None = None,
        reply_to: MessageEv | None = None,
    ) -> str:
        return self._send(
            lambda: self.client.send_document(
                to_jid(to),
                file,
                caption=caption,
                filename=filename,
                title=filename,
                mimetype=mimetype,
                quoted=reply_to,
            )
        )

    # ---- interactive ----

    def poll(
        self,
        to: Recipient,
        question: str,
        options: list[str],
        multiple: bool = False,
        reply_to: MessageEv | None = None,
    ) -> str:
        """multiple=True lets people pick more than one option."""
        options = [o.strip() for o in options if o.strip()]
        if not POLL_MIN_OPTIONS <= len(options) <= POLL_MAX_OPTIONS:
            raise ValueError(f"a poll needs {POLL_MIN_OPTIONS} to {POLL_MAX_OPTIONS} options")
        if len(set(options)) != len(options):
            raise ValueError("poll options must be different from each other")

        vote_type = VoteType.MULTIPLE if multiple else VoteType.SINGLE

        def send() -> SendResponse:
            message = self.client.build_poll_vote_creation(question, options, vote_type, quoted=reply_to)
            return self.client.send_message(to_jid(to), message)

        return self._send(send)

    def react(self, chat: Recipient, sender: Recipient, message_id: str, emoji: str) -> str:
        """React to a message. Our new reaction replaces our previous one; emoji="" removes it."""
        chat_jid = to_jid(chat)

        def send() -> SendResponse:
            message = self.client.build_reaction(chat_jid, to_jid(sender), message_id, emoji)
            return self.client.send_message(chat_jid, message)

        return self._send(send)

    def react_to(self, event: MessageEv, emoji: str) -> str:
        """React to a received message."""
        source = event.Info.MessageSource
        return self.react(source.Chat, source.Sender, event.Info.ID, emoji)

    # ---- internals ----

    @staticmethod
    def _send(do: Callable[[], SendResponse]) -> str:
        try:
            return do().ID
        except Exception as e:
            raise WhatsappRequestFailed(str(e)) from e
