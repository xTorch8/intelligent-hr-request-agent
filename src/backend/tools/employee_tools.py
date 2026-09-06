from langchain_core.tools import tool
from typing import Optional

from ..models.employee_model import EmployeeProfileRequest, LeaveBalanceRequest
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
