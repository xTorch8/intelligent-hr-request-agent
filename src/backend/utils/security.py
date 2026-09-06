from typing import Callable, List, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from ..models.auth_model import UserPayload
from .auth_utils import decode_access_token

security_scheme = HTTPBearer(auto_error = False)

async def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme)) -> UserPayload:
    if not credentials or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail = "Missing or invalid Bearer authentication token.",
            headers = {"WWW-Authenticate": "Bearer"}
        )

    token = credentials.credentials
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail = "Invalid or expired Bearer authentication token.",
            headers = {"WWW-Authenticate": "Bearer"}
        )

    user_id = payload.get("sub")
    email = payload.get("email")
    role = payload.get("role")

    if not user_id or not email or not role:
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail = "Malformed token payload.",
            headers = {"WWW-Authenticate": "Bearer"}
        )

    return UserPayload(
        user_id = user_id,
        employee_id = payload.get("employee_id"),
        employee_number = payload.get("employee_number"),
        email = email,
        role = role,
        first_name = payload.get("first_name"),
        last_name = payload.get("last_name")
    )


def require_role(allowed_roles: List[str]) -> Callable:
    async def role_checker(current_user: UserPayload = Depends(get_current_user)) -> UserPayload:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code = status.HTTP_403_FORBIDDEN,
                detail = f"Access denied. Required role in: {allowed_roles}. Current user role: '{current_user.role}'."
            )
        return current_user

    return role_checker

