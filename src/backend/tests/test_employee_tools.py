import logging
from src.backend.models.agent_model import AgentQueryRequest
from src.backend.models.employee_model import (
    EmployeeProfileRequest,
    HealthBenefitRequest,
    LeaveBalanceRequest
)
from src.backend.services.agent_service import AgentService
from src.backend.services.employee_service import EmployeeService


def test_employee_service_postgres():
    print("\n==================================================")
    print("      Testing EmployeeService Request/Response Models")
    print("==================================================")
    
    service = EmployeeService()
    
    # 1. Get profile for EMP-0001
    profile_req = EmployeeProfileRequest(employee_number = "EMP-0001")
    res_profile = service.get_employee_profile(profile_req)
    print("\n1. get_employee_profile(EmployeeProfileRequest(employee_number='EMP-0001')):")
    print(f"Is Success: {res_profile.is_success}")
    print(f"Status Code: {res_profile.status_code}")
    print(f"Message: {res_profile.message}")
    if res_profile.payload:
        print(f"Employee Name: {res_profile.payload.first_name} {res_profile.payload.last_name}")
        print(f"Department: {res_profile.payload.department}")
    
    # 2. Get leave balance for EMP-0001
    balance_req = LeaveBalanceRequest(employee_number = "EMP-0001", year = 2026)
    res_balance = service.get_leave_balance(balance_req)
    print("\n2. get_leave_balance(LeaveBalanceRequest(employee_number='EMP-0001', year=2026)):")
    print(f"Is Success: {res_balance.is_success}")
    print(f"Status Code: {res_balance.status_code}")
    print(f"Message: {res_balance.message}")
    if res_balance.payload:
        for b in res_balance.payload.balances:
            print(f"  [{b.leave_type}] Total: {b.total_days}, Used: {b.used_days}, Remaining: {b.remaining_days}")

    # 3. Get health benefit for EMP-0001
    benefit_req = HealthBenefitRequest(employee_number = "EMP-0001")
    res_benefit = service.get_health_benefit(benefit_req)
    print("\n3. get_health_benefit(HealthBenefitRequest(employee_number='EMP-0001')):")
    print(f"Is Success: {res_benefit.is_success}")
    print(f"Status Code: {res_benefit.status_code}")
    print(f"Message: {res_benefit.message}")
    if res_benefit.payload:
        for item in res_benefit.payload.benefits:
            print(f"  [{item.benefit_type}] {item.plan_name} - Coverage: {item.coverage_percentage}%, Limit: {item.annual_limit}, Used: {item.used_amount}, Remaining: {item.remaining_limit}")


def test_agent_employee_postgres_tools():
    print("\n==================================================")
    print("      Testing Agent Integration with DB Tools")
    print("==================================================")
    
    agent_service = AgentService()
    
    queries = [
        "What is the remaining annual leave balance for employee EMP-0001?",
        "Can you check the health benefit plans and remaining limits for employee EMP-0001?"
    ]
    
    for q in queries:
        print(f"\n💬 User Query: '{q}'")
        request = AgentQueryRequest(query = q)
        response = agent_service.ask(request)
        print(f"Is Success: {response.is_success}")
        if response.payload:
            print(f"Model Used: {response.payload.model_used}")
            print(f"Answer:\n{response.payload.answer}\n")


if __name__ == "__main__":
    logging.basicConfig(level = logging.INFO)
    test_employee_service_postgres()
    test_agent_employee_postgres_tools()
