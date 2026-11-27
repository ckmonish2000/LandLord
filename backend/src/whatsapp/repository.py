from src.database import JsonCollection


class WhatsappAccountRepository(JsonCollection):
    """One record per app user (client_id) and the WhatsApp account they linked."""

    def __init__(self):
        super().__init__("whatsapp_accounts")

    def get_by_client_id(self, client_id: str) -> dict | None:
        return self.find_one("client_id", client_id)

    def save(self, client_id: str, fields: dict) -> dict:
        return self.upsert("client_id", client_id, fields)

