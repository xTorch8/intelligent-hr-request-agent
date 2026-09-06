from fastapi import APIRouter, Depends
from typing import Optional

from ..models.api_model import APIResponseModel
from ..models.employee_model import (
    EmployeeProfileRequest,
    EmployeeProfileResponse,
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
