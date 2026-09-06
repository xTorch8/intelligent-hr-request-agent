from typing import Optional
from fastapi import APIRouter, Depends

from ..models.api_model import APIResponseModel
from ..models.auth_model import LoginRequest, LoginResponse, UserPayload
from ..services.auth_service import AuthService
from ..utils.security import get_current_user

router = APIRouter(
    prefix = "/api/auth",
    tags = ["auth"]
)

auth_service = AuthService()

@router.post("/login", response_model = APIResponseModel[Optional[LoginResponse]])
async def login(request: LoginRequest):
    return auth_service.login(request)

@router.get("/me", response_model = APIResponseModel[Optional[UserPayload]])
async def get_me(current_user: UserPayload = Depends(get_current_user)):
    return auth_service.get_me(current_user)

