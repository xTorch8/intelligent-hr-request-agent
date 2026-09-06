from datetime import date
import logging
from src.backend.models.agent_model import AgentQueryRequest
from src.backend.models.request_model import ProcessLeaveRequest
from src.backend.services.agent_service import AgentService
from src.backend.services.request_service import RequestService


def test_request_service_direct():
    print("\n==================================================")
    print("      Testing RequestService Direct Processing")
    print("==================================================")
    
    service = RequestService()
    
    req = ProcessLeaveRequest(
        employee_number = "EMP-0001",
        leave_type = "ANNUAL",
        start_date = date(2026, 10, 1),
        end_date = date(2026, 10, 5),
        requested_days = 5.0,
        reason = "Annual family vacation"
    )
    
    response = service.process_leave_request(req)
    print(f"Is Success: {response.is_success}")
    print(f"Status Code: {response.status_code}")
    print(f"Message: {response.message}")
    if response.payload:
        res = response.payload
        print(f"Request Number: {res.request_number}")
        print(f"Status: {res.request_status} | Recommendation: {res.recommendation} | Eligibility: {res.eligibility_result}")
        print(f"Reasoning: {res.reasoning_summary}")
        print("Rule Checks:")
        for r in res.rule_results:
            symbol = "✓" if r.passed else "✗"
            print(f"  [{symbol}] {r.rule_name}: {r.details}")


def test_agent_leave_request_tool():
    print("\n==================================================")
    print("      Testing Agent Integration with submit_leave_request")
    print("==================================================")
    
    agent_service = AgentService()
    
    query = "I am employee EMP-0001. I want to request annual leave from 2026-10-01 to 2026-10-05 (5 days) for annual family vacation. Can you evaluate and submit this leave request for me?"
    
    print(f"\n💬 User Query: '{query}'")
    request = AgentQueryRequest(query = query)
    response = agent_service.ask(request)
    print(f"Is Success: {response.is_success}")
    if response.payload:
        print(f"Model Used: {response.payload.model_used}")
        print(f"Answer:\n{response.payload.answer}\n")


if __name__ == "__main__":
    logging.basicConfig(level = logging.INFO)
    test_request_service_direct()
    test_agent_leave_request_tool()

