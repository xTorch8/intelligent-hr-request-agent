from fastapi import APIRouter
from typing import Optional

from ..models.api_model import APIResponseModel
from ..models.request_model import (
    BenefitClaimDecisionResponse,
    ExpenseClaimDecisionResponse,
    LeaveRequestDecisionResponse,
    ProcessBenefitClaimRequest,
    ProcessExpenseClaimRequest,
    ProcessLeaveRequest
)
from ..services.request_service import RequestService

router = APIRouter(
    prefix = "/api/request",
    tags = ["request"]
)

request_service = RequestService()


@router.post("/leave", response_model = APIResponseModel[Optional[LeaveRequestDecisionResponse]])
async def process_leave_request(request: ProcessLeaveRequest):
    return request_service.process_leave_request(request)


@router.post("/benefit", response_model = APIResponseModel[Optional[BenefitClaimDecisionResponse]])
async def process_benefit_claim(request: ProcessBenefitClaimRequest):
    return request_service.process_benefit_claim(request)


@router.post("/expense", response_model = APIResponseModel[Optional[ExpenseClaimDecisionResponse]])
async def process_expense_claim(request: ProcessExpenseClaimRequest):
    return request_service.process_expense_claim(request)
