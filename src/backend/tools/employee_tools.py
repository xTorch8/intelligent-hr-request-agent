from langchain_core.tools import tool
from typing import Optional

from ..models.employee_model import (
    EmployeeProfileRequest,
    HealthBenefitRequest,
    LeaveBalanceRequest
)
from ..services.employee_service import EmployeeService


@tool("get_employee_profile")
def get_employee_profile(employee_number: str) -> str:
    """
    Use this tool to retrieve the profile details of an employee (such as name, email, department, job title, employment status, hire date).
    Accepts employee_number (e.g. 'EMP-0001').
    """
    service = EmployeeService()
    request = EmployeeProfileRequest(employee_number = employee_number)
    response = service.get_employee_profile(request)
    if not response.payload:
        return f"Employee profile not found for employee_number: {employee_number}"
    
    profile = response.payload
    return (
        f"Employee Profile:\n"
        f"- ID: {profile.employee_id}\n"
        f"- Employee Number: {profile.employee_number}\n"
        f"- Name: {profile.first_name} {profile.last_name}\n"
        f"- Email: {profile.email}\n"
        f"- Department: {profile.department}\n"
        f"- Job Title: {profile.job_title}\n"
        f"- Employment Type: {profile.employment_type}\n"
        f"- Status: {profile.employment_status}\n"
        f"- Hire Date: {profile.hire_date}"
    )


@tool("get_leave_balance")
def get_leave_balance(employee_number: str, year: Optional[int] = 2026) -> str:
    """
    Use this tool to retrieve the remaining leave balance for an employee across leave types (ANNUAL, SICK, etc.) from the leave_balances table.
    Accepts employee_number (e.g. 'EMP-0001').
    """
    service = EmployeeService()
    request = LeaveBalanceRequest(employee_number = employee_number, year = year)
    response = service.get_leave_balance(request)
    if not response.payload or not response.payload.balances:
        return f"Leave balance not found for employee_number: {employee_number} in year {year}"
    
    balance_resp = response.payload
    lines = [f"Leave Balances for Year {balance_resp.year} (Employee ID: {balance_resp.employee_id}):"]
    for b in balance_resp.balances:
        lines.append(f"- {b.leave_type}: Total = {b.total_days} days, Used = {b.used_days} days, Remaining = {b.remaining_days} days")
    
    return "\n".join(lines)


@tool("get_health_benefit")
def get_health_benefit(employee_number: str, benefit_type: Optional[str] = None) -> str:
    """
    Use this tool to retrieve employee benefit details (plan name, coverage percentage, annual limit, used amount, remaining limit) from the employee_benefits table.
    Accepts employee_number (e.g. 'EMP-0001') and optional benefit_type (e.g. 'HEALTH', 'DENTAL').
    """
    service = EmployeeService()
    request = HealthBenefitRequest(employee_number = employee_number, benefit_type = benefit_type)
    response = service.get_health_benefit(request)
    if not response.payload or not response.payload.benefits:
        return f"Health/Benefit plans not found for employee_number: {employee_number}"
    
    benefit_resp = response.payload
    lines = [f"Employee Benefit Plans (Employee ID: {benefit_resp.employee_id}):"]
    for item in benefit_resp.benefits:
        cov = f"{item.coverage_percentage}%" if item.coverage_percentage is not None else "N/A"
        ann_lim = f"${item.annual_limit:,.2f}" if item.annual_limit is not None else "No Limit"
        rem_lim = f"${item.remaining_limit:,.2f}" if item.remaining_limit is not None else "No Limit"
        lines.append(
            f"- [{item.benefit_type}] {item.plan_name} (Status: {item.status})\n"
            f"  Coverage: {cov} | Annual Limit: {ann_lim} | Used: ${item.used_amount:,.2f} | Remaining: {rem_lim}\n"
            f"  Effective: {item.effective_date} to {item.expiration_date or 'Indefinite'}"
        )
    
    return "\n".join(lines)
