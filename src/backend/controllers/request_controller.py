from fastapi import APIRouter, Depends
from typing import Optional

from ..models.api_model import APIResponseModel
from ..models.request_model import (
    BenefitClaimDecisionResponse,
    ExpenseClaimDecisionResponse,
    GetRequestListFilterRequest,
    LeaveRequestDecisionResponse,
    ProcessBenefitClaimRequest,
    ProcessExpenseClaimRequest,
    ProcessLeaveRequest,
    RequestListResponse,
    UpdateRequestStatusRequest
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


@router.get("/list", response_model = APIResponseModel[Optional[RequestListResponse]])
async def get_requests(filter_req: GetRequestListFilterRequest = Depends()):
    return request_service.get_requests(filter_req)


@router.post("/accept", response_model = APIResponseModel[bool])
async def accept_request(request: UpdateRequestStatusRequest):
    return request_service.update_request_status(request, new_status = "APPROVED")


@router.post("/reject", response_model = APIResponseModel[bool])
async def reject_request(request: UpdateRequestStatusRequest):
    return request_service.update_request_status(request, new_status = "REJECTED")
