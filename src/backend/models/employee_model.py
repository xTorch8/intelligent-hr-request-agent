from datetime import date
from typing import List, Optional
from pydantic import BaseModel, Field


# Request Models
class EmployeeProfileRequest(BaseModel):
    employee_number: str = Field(..., description = "Employee Number e.g. EMP-0001")


class LeaveBalanceRequest(BaseModel):
    employee_number: str = Field(..., description = "Employee Number e.g. EMP-0001")
    year: Optional[int] = Field(default = 2026, description = "Filter leave balances by year")


class HealthBenefitRequest(BaseModel):
    employee_number: str = Field(..., description = "Employee Number e.g. EMP-0001")
    benefit_type: Optional[str] = Field(default = None, description = "Optional benefit type filter e.g. HEALTH, DENTAL")


# Response Models
class EmployeeProfileResponse(BaseModel):
    employee_id: str
    employee_number: str
    first_name: str
    last_name: str
    email: str
    department: str
    job_title: str
    employment_type: str
    employment_status: str
    hire_date: date


class LeaveTypeBalance(BaseModel):
    leave_type: str
    total_days: float
    used_days: float
    remaining_days: float
    year: int


class LeaveBalanceResponse(BaseModel):
    employee_id: str
    year: int
    balances: List[LeaveTypeBalance]


class BenefitItem(BaseModel):
    benefit_id: str
    benefit_type: str
    plan_name: str
    coverage_percentage: Optional[float] = None
    annual_limit: Optional[float] = None
    used_amount: float
    remaining_limit: Optional[float] = None
    effective_date: date
    expiration_date: Optional[date] = None
    status: str


class HealthBenefitResponse(BaseModel):
    employee_id: str
    benefits: List[BenefitItem]
