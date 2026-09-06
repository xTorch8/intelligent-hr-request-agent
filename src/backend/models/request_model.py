from datetime import date, datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ProcessLeaveRequest(BaseModel):
    employee_number: str = Field(..., description = "Employee Number e.g. EMP-0001")
    leave_type: str = Field(..., description = "Leave type e.g. ANNUAL, SICK, MATERNITY_PATERNITY, UNPAID")
    start_date: date = Field(..., description = "Leave start date (YYYY-MM-DD)")
    end_date: date = Field(..., description = "Leave end date (YYYY-MM-DD)")
    requested_days: float = Field(..., description = "Total number of requested leave days")
    reason: Optional[str] = Field(default = None, description = "Reason for leave request")


class ProcessBenefitClaimRequest(BaseModel):
    employee_number: str = Field(..., description = "Employee Number e.g. EMP-0001")
    benefit_type: str = Field(..., description = "Benefit type e.g. HEALTH, DENTAL")
    service_date: date = Field(..., description = "Service date (YYYY-MM-DD)")
    provider_name: str = Field(..., description = "Healthcare provider name")
    claim_amount: float = Field(..., description = "Total claim amount")
    currency: str = Field(default = "IDR", description = "Currency code e.g. IDR, USD")
    description: Optional[str] = Field(default = None, description = "Claim description or details")
    blob_url: Optional[str] = Field(default = None, description = "Medical document receipt blob URL")


class ProcessExpenseClaimRequest(BaseModel):
    employee_number: str = Field(..., description = "Employee Number e.g. EMP-0001")
    expense_category: str = Field(..., description = "Category e.g. TRAVEL, MEALS, SUPPLIES, INTERNET")
    expense_date: date = Field(..., description = "Expense transaction date (YYYY-MM-DD)")
    merchant: str = Field(..., description = "Merchant name e.g. Airline, Hotel, Restaurant")
    claim_amount: float = Field(..., description = "Claimed expense amount")
    currency: str = Field(default = "IDR", description = "Currency code e.g. IDR, USD")
    description: Optional[str] = Field(default = None, description = "Business justification or notes")
    blob_url: Optional[str] = Field(default = None, description = "Receipt blob URL")


class GetRequestListFilterRequest(BaseModel):
    request_type: Optional[str] = Field(default = None, description = "Optional filter: LEAVE, EXPENSE, BENEFIT")
    status: Optional[str] = Field(default = None, description = "Optional filter: SUBMITTED, PROCESSING, PENDING_REVIEW, APPROVED, REJECTED, COMPLETED, CANCELLED")
    employee_number: Optional[str] = Field(default = None, description = "Optional filter by employee_number e.g. EMP-0001")


class UpdateRequestStatusRequest(BaseModel):
    request_id: str = Field(..., description = "Request UUID")
    actor_id: Optional[str] = Field(default = None, description = "HR Admin employee UUID")
    reason: Optional[str] = Field(default = None, description = "Reason for decision")


class RuleCheckResult(BaseModel):
    rule_name: str
    passed: bool
    details: str


class LeaveRequestDecisionResponse(BaseModel):
    request_id: str
    request_number: str
    employee_number: str
    leave_type: str
    start_date: date
    end_date: date
    requested_days: float
    request_status: str = Field(..., description = "SUBMITTED, APPROVED, REJECTED, PENDING_REVIEW")
    recommendation: str = Field(..., description = "APPROVE, REJECT, REVIEW")
    eligibility_result: str = Field(..., description = "ELIGIBLE, NOT_ELIGIBLE, PARTIALLY_ELIGIBLE, REQUIRES_REVIEW")
    rule_results: List[RuleCheckResult] = Field(default_factory = list)
    reasoning_summary: str
    agent_run_id: str
    submitted_at: datetime


class BenefitClaimDecisionResponse(BaseModel):
    request_id: str
    request_number: str
    employee_number: str
    benefit_type: str
    service_date: date
    provider_name: str
    claim_amount: float
    eligible_amount: float
    currency: str
    request_status: str = Field(..., description = "SUBMITTED, APPROVED, REJECTED, PENDING_REVIEW")
    recommendation: str = Field(..., description = "APPROVE, REJECT, REVIEW")
    eligibility_result: str = Field(..., description = "ELIGIBLE, NOT_ELIGIBLE, PARTIALLY_ELIGIBLE, REQUIRES_REVIEW")
    rule_results: List[RuleCheckResult] = Field(default_factory = list)
    reasoning_summary: str
    agent_run_id: str
    submitted_at: datetime


class ExpenseClaimDecisionResponse(BaseModel):
    request_id: str
    request_number: str
    employee_number: str
    expense_category: str
    expense_date: date
    merchant: str
    claim_amount: float
    eligible_amount: float
    currency: str
    request_status: str = Field(..., description = "SUBMITTED, APPROVED, REJECTED, PENDING_REVIEW")
    recommendation: str = Field(..., description = "APPROVE, REJECT, REVIEW")
    eligibility_result: str = Field(..., description = "ELIGIBLE, NOT_ELIGIBLE, PARTIALLY_ELIGIBLE, REQUIRES_REVIEW")
    rule_results: List[RuleCheckResult] = Field(default_factory = list)
    reasoning_summary: str
    agent_run_id: str
    submitted_at: datetime


class RequestSummaryItem(BaseModel):
    request_id: str
    request_number: str
    employee_id: str
    employee_number: str
    employee_name: str
    department: str
    request_type: str
    status: str
    title: str
    description: Optional[str] = None
    recommendation: Optional[str] = None
    eligibility_result: Optional[str] = None
    reasoning_summary: Optional[str] = None
    submitted_at: datetime
    updated_at: datetime


class RequestListResponse(BaseModel):
    total_count: int
    requests: List[RequestSummaryItem]
