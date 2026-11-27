from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.auth.exceptions import InvalidToken
from src.auth.repository import UserRepository
from src.auth.service import AuthService

_bearer = HTTPBearer()


def get_auth_service() -> AuthService:
    return AuthService(UserRepository())


def get_current_user(
    creds: HTTPAuthorizationCredentials = Depends(_bearer),
    service: AuthService = Depends(get_auth_service),
) -> dict:
    """Use as a dependency on any route that needs a signed-in user."""
    try:
        return service.user_from_token(creds.credentials)
    except InvalidToken as e:
        raise HTTPException(401, "Invalid or expired token", headers={"WWW-Authenticate": "Bearer"}) from e
