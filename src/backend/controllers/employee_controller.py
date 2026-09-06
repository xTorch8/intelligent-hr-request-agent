from typing import Optional
from fastapi import APIRouter, Depends

from ..models.api_model import APIResponseModel
from ..models.auth_model import UserPayload
from ..models.employee_model import (
    EmployeeProfileRequest,
    EmployeeProfileResponse,
    HealthBenefitRequest,
    HealthBenefitResponse,
    LeaveBalanceRequest,
    LeaveBalanceResponse
)
from ..services.employee_service import EmployeeService
from ..utils.security import get_current_user

router = APIRouter(
    prefix = "/api/employee",
    tags = ["employee"]
)

employee_service = EmployeeService()


@router.get("/profile", response_model = APIResponseModel[Optional[EmployeeProfileResponse]])
async def get_employee_profile(
    request: EmployeeProfileRequest = Depends(),
    current_user: UserPayload = Depends(get_current_user)
):
    return employee_service.get_employee_profile(request)


@router.get("/leave-balance", response_model = APIResponseModel[Optional[LeaveBalanceResponse]])
async def get_leave_balance(
    request: LeaveBalanceRequest = Depends(),
    current_user: UserPayload = Depends(get_current_user)
):
    return employee_service.get_leave_balance(request)


@router.get("/health-benefit", response_model = APIResponseModel[Optional[HealthBenefitResponse]])
async def get_health_benefit(
    request: HealthBenefitRequest = Depends(),
    current_user: UserPayload = Depends(get_current_user)
):
    return employee_service.get_health_benefit(request)
