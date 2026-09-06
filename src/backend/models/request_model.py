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
