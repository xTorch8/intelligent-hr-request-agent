from datetime import datetime
from langchain_core.tools import tool
from typing import Optional

from ..models.employee_model import (
    EmployeeProfileRequest,
    HealthBenefitRequest,
    LeaveBalanceRequest
)
from ..models.request_model import ProcessLeaveRequest
from ..services.employee_service import EmployeeService
from ..services.request_service import RequestService


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


@tool("submit_leave_request")
def submit_leave_request(
    employee_number: str,
    leave_type: str,
    start_date: str,
    end_date: str,
    requested_days: float,
    reason: Optional[str] = None
) -> str:
    """
    Use this tool to submit and evaluate a Leave Request for an employee against deterministic business rules (employment status, available balance, max consecutive days, notice period, overlapping leave).
    Dates must be formatted as YYYY-MM-DD (e.g. '2026-10-01').
    """
    try:
        parsed_start = datetime.strptime(start_date, "%Y-%m-%d").date()
        parsed_end = datetime.strptime(end_date, "%Y-%m-%d").date()
    except Exception as e:
        return f"Invalid date format for start_date or end_date. Must be YYYY-MM-DD. Error: {e}"

    service = RequestService()
    req = ProcessLeaveRequest(
        employee_number = employee_number,
        leave_type = leave_type,
        start_date = parsed_start,
        end_date = parsed_end,
        requested_days = requested_days,
        reason = reason
    )

    response = service.process_leave_request(req)
    if not response.payload:
        return f"Failed to process leave request: {response.message or response.error}"

    res = response.payload
    lines = [
        f"Leave Request Submission & Evaluation Result:",
        f"- Request Number: {res.request_number} (ID: {res.request_id})",
        f"- Status: {res.request_status}",
        f"- Recommendation: {res.recommendation} | Eligibility: {res.eligibility_result}",
        f"- Reasoning: {res.reasoning_summary}",
        f"- Rule Validation Details:"
    ]
    for r in res.rule_results:
        status_symbol = "✓ PASSED" if r.passed else "✗ FAILED"
        lines.append(f"  * [{status_symbol}] {r.rule_name}: {r.details}")

    return "\n".join(lines)
