from datetime import timedelta

import jwt

from src.auth.config import auth_settings
from src.auth.constants import JWT_ALGORITHM
from src.auth.exceptions import EmailTaken, InvalidCredentials, InvalidToken
from src.auth.models import User
from src.auth.repository import UserRepository
from src.auth.utils import hash_password, verify_password
from src.utils import utc_now


class AuthService:
    def __init__(self, repository: UserRepository):
        self.repository = repository

    def signup(self, email: str, password: str, name: str) -> User:
        email = email.lower()
        if self.repository.get_by_email(email):
            raise EmailTaken()
        return self.repository.create(email=email, name=name.strip(), password_hash=hash_password(password))

    def signin(self, email: str, password: str) -> str:
        """A signed token for the user, valid for TOKEN_TTL_MINUTES."""
        user = self.repository.get_by_email(email.lower())
        if not user or not verify_password(password, user.password_hash):
            raise InvalidCredentials()
        now = utc_now()
        payload = {"sub": user.id, "iat": now, "exp": now + timedelta(minutes=auth_settings.TOKEN_TTL_MINUTES)}
        return jwt.encode(payload, auth_settings.AUTH_SECRET, algorithm=JWT_ALGORITHM)

    def user_from_token(self, token: str) -> User:
        try:
            payload = jwt.decode(token, auth_settings.AUTH_SECRET, algorithms=[JWT_ALGORITHM])
        except jwt.PyJWTError as e:
            raise InvalidToken(str(e)) from e
        user = self.repository.get_by_id(payload["sub"])
        if not user:
            raise InvalidToken("user not found")
        return user
