from src.database import JsonCollection


class UserRepository(JsonCollection):
    def __init__(self):
        super().__init__("users")

    def get_by_email(self, email: str) -> dict | None:
        return self.find_one("email", email)
