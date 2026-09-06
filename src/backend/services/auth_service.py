import logging
from typing import Optional

from ..models.api_model import APIResponseModel
from ..models.auth_model import LoginRequest, LoginResponse, UserPayload
from ..repositories.auth_repository import AuthRepository
from ..utils.auth_utils import create_access_token, verify_password


class AuthService:
    def __init__(self, auth_repository: Optional[AuthRepository] = None):
        self._auth_repository = auth_repository if auth_repository else AuthRepository()

    def login(self, login_data: LoginRequest) -> APIResponseModel[Optional[LoginResponse]]:
        logging.info(f"[INFO][auth_service.py][login] Authenticating user: {login_data.email}")
        try:
            user = self._auth_repository.get_user_by_email(login_data.email)
            if not user or not verify_password(login_data.password, user["password_hash"]):
                return APIResponseModel[Optional[LoginResponse]](
                    is_success = False,
                    error = "Invalid email or password.",
                    status_code = 401,
                    message = "Invalid email or password.",
                    payload = None
                )

            token_payload = {
                "sub": user["user_id"],
                "employee_id": user["employee_id"],
                "employee_number": user["employee_number"],
                "email": user["email"],
                "role": user["role"]
            }
            access_token = create_access_token(data = token_payload)

            response = LoginResponse(
                access_token = access_token,
                token_type = "bearer",
                user_id = user["user_id"],
                employee_id = user["employee_id"],
                employee_number = user["employee_number"],
                email = user["email"],
                role = user["role"],
                first_name = user["first_name"],
                last_name = user["last_name"]
            )

            return APIResponseModel[Optional[LoginResponse]](
                is_success = True,
                status_code = 200,
                message = "User authenticated successfully",
                payload = response
            )
        except Exception as e:
            logging.error(f"[ERROR][auth_service.py][login] Authentication failed. Error: {e}")
            return APIResponseModel[Optional[LoginResponse]](
                is_success = False,
                error = str(e),
                status_code = 500,
                message = f"Authentication failed: {str(e)}",
                payload = None
            )

    def get_me(self, user_payload: UserPayload) -> APIResponseModel[Optional[UserPayload]]:
        return APIResponseModel[Optional[UserPayload]](
            is_success = True,
            status_code = 200,
            message = "Current user retrieved successfully",
            payload = user_payload
        )

