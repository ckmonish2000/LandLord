from fastapi import APIRouter, Depends, HTTPException

from src.auth.dependencies import get_auth_service, get_current_user
from src.auth.exceptions import EmailTaken, InvalidCredentials
from src.auth.schemas import SigninRequest, SignupRequest
from src.auth.service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", status_code=201)
def signup(body: SignupRequest, service: AuthService = Depends(get_auth_service)):
    try:
        return service.signup(body.email, body.password, body.name)
    except EmailTaken as e:
        raise HTTPException(409, "Email already registered") from e


@router.post("/signin")
def signin(body: SigninRequest, service: AuthService = Depends(get_auth_service)):
    try:
        token = service.signin(body.email, body.password)
    except InvalidCredentials as e:
        raise HTTPException(401, "Invalid email or password") from e
    return {"access_token": token, "token_type": "bearer"}


@router.get("/me")
def me(user: dict = Depends(get_current_user)):
    return user
