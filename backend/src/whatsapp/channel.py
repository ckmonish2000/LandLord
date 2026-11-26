"""WhatsApp implementation of the agents' Channel: questions and replies go to the
landlord's own chat ("Message yourself"); other messages go to members / groups."""

from neonize.proto.Neonize_pb2 import JID

from src.agents.base import Option
from src.whatsapp.sender import Choice, WhatsappSender
from src.whatsapp.utils import format_agent_reply

# WhatsApp truncates longer labels
LIST_ROW_TITLE_MAX = 24
LIST_ROW_DESCRIPTION_MAX = 72
BUTTON_TITLE_MAX = 20


class WhatsappChannel:
    def __init__(self, sender: WhatsappSender, chat: JID, signature: str, owner_ids: set[str]):
        self.sender = sender
        self.chat = chat  # the landlord's self chat
        self.signature = signature
        self.owner_ids = owner_ids

    def send_text(self, body: str, to: str | None = None) -> str:
        if to is None:
            return self.sender.text(self.chat, format_agent_reply(self.signature, body))
        return self.sender.text(to, body)  # to residents / groups: from the landlord, no signature

    def ask_choice(self, body: str, button_text: str, options: list[Option]) -> str:
        rows = [
            Choice(o.id, o.title[:LIST_ROW_TITLE_MAX], o.description[:LIST_ROW_DESCRIPTION_MAX]) for o in options
        ]
        return self.sender.list_message(self.chat, format_agent_reply(self.signature, body), button_text, rows)

    def ask_buttons(self, body: str, options: list[Option]) -> str:
        buttons = [Choice(o.id, o.title[:BUTTON_TITLE_MAX]) for o in options]
        return self.sender.buttons(self.chat, format_agent_reply(self.signature, body), buttons)

    def ask_poll(self, question: str, options: list[str], multiple: bool = True) -> str:
        return self.sender.poll(self.chat, question, options, multiple=multiple)
