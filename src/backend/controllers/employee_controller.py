from fastapi import APIRouter, Depends
from typing import Optional

from ..models.api_model import APIResponseModel
from ..models.employee_model import (
    EmployeeProfileRequest,
    EmployeeProfileResponse,
    HealthBenefitRequest,
    HealthBenefitResponse,
    LeaveBalanceRequest,
    LeaveBalanceResponse
)
from ..services.employee_service import EmployeeService

router = APIRouter(
    prefix = "/api/employee",
    tags = ["employee"]
)

employee_service = EmployeeService()


@router.get("/profile", response_model = APIResponseModel[Optional[EmployeeProfileResponse]])
async def get_employee_profile(request: EmployeeProfileRequest = Depends()):
    return employee_service.get_employee_profile(request)


@router.get("/leave-balance", response_model = APIResponseModel[Optional[LeaveBalanceResponse]])
async def get_leave_balance(request: LeaveBalanceRequest = Depends()):
    return employee_service.get_leave_balance(request)


@router.get("/health-benefit", response_model = APIResponseModel[Optional[HealthBenefitResponse]])
async def get_health_benefit(request: HealthBenefitRequest = Depends()):
    return employee_service.get_health_benefit(request)
