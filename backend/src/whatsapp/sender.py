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
from dataclasses import dataclass

from neonize.client import NewClient
from neonize.events import MessageEv
from neonize.ext.interactive_message import ButtonMessage
from neonize.proto.Neonize_pb2 import JID, SendResponse
from neonize.utils.enum import VoteType

from src.whatsapp.constants import BUTTONS_MAX, LIST_MAX_ROWS, POLL_MAX_OPTIONS, POLL_MIN_OPTIONS
from src.whatsapp.exceptions import WhatsappRequestFailed
from src.whatsapp.utils import to_jid

Recipient = str | JID
Media = bytes | str  # file contents, or a local path / URL


@dataclass(frozen=True)
class Choice:
    """One row of a list or one reply button. `id` comes back when the user taps it."""

    id: str
    title: str
    description: str = ""


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

    def list_message(
        self,
        to: Recipient,
        body: str,
        button_text: str,
        rows: list[Choice],
        section_title: str = "",
        footer: str | None = None,
    ) -> str:
        """A message with a button that opens a list; the user picks one row.
        The reply arrives as an interactiveResponseMessage carrying the row id."""
        if not 1 <= len(rows) <= LIST_MAX_ROWS:
            raise ValueError(f"a list needs 1 to {LIST_MAX_ROWS} rows")
        message = ButtonMessage().set_body(body).add_selection(button_text).add_section(section_title)
        for row in rows:
            message.add_row(row.title, description=row.description, id=row.id)
        if footer:
            message.set_footer(footer)
        return self._send(lambda: self.client.send_interactive_message(to_jid(to), message))

    def buttons(self, to: Recipient, body: str, buttons: list[Choice], footer: str | None = None) -> str:
        """A message with up to 3 quick reply buttons. The tap arrives as an
        interactiveResponseMessage carrying the button id."""
        if not 1 <= len(buttons) <= BUTTONS_MAX:
            raise ValueError(f"a message needs 1 to {BUTTONS_MAX} buttons")
        message = ButtonMessage().set_body(body)
        for button in buttons:
            message.add_reply(button.title, button.id)
        if footer:
            message.set_footer(footer)
        return self._send(lambda: self.client.send_interactive_message(to_jid(to), message))

    def react(self, chat: Recipient, sender: Recipient, message_id: str, emoji: str) -> str:
        """React to a message. Our new reaction replaces our previous one; emoji="" removes it."""
        chat_jid = to_jid(chat)

        def send() -> SendResponse:
            message = self.client.build_reaction(chat_jid, to_jid(sender), message_id, emoji)
            return self.client.send_message(chat_jid, message)

        return self._send(send)

    # ---- internals ----

    @staticmethod
    def _send(do: Callable[[], SendResponse]) -> str:
        try:
            return do().ID
        except Exception as e:
            raise WhatsappRequestFailed(str(e)) from e
