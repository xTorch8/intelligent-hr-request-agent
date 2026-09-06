from datetime import date
import logging
from src.backend.models.agent_model import AgentQueryRequest
from src.backend.models.request_model import (
    ProcessBenefitClaimRequest,
    ProcessExpenseClaimRequest,
    ProcessLeaveRequest
)
from src.backend.services.agent_service import AgentService
from src.backend.services.request_service import RequestService


def test_request_service_direct():
    print("\n==================================================")
    print("      Testing RequestService Direct Processing")
    print("==================================================")
    
    service = RequestService()
    
    req_leave = ProcessLeaveRequest(
        employee_number = "EMP-0001",
        leave_type = "ANNUAL",
        start_date = date(2026, 10, 1),
        end_date = date(2026, 10, 5),
        requested_days = 5.0,
        reason = "Annual family vacation"
    )
    
    res_leave = service.process_leave_request(req_leave)
    print(f"\n1. Leave Request Result:")
    print(f"Is Success: {res_leave.is_success}")
    if res_leave.payload:
        res = res_leave.payload
        print(f"Request Number: {res.request_number}")
        print(f"Status: {res.request_status} | Recommendation: {res.recommendation} | Eligibility: {res.eligibility_result}")
        print(f"Reasoning: {res.reasoning_summary}")
        for r in res.rule_results:
            symbol = "✓" if r.passed else "✗"
            print(f"  [{symbol}] {r.rule_name}: {r.details}")

    req_benefit = ProcessBenefitClaimRequest(
        employee_number = "EMP-0001",
        benefit_type = "HEALTH",
        service_date = date(2026, 8, 15),
        provider_name = "Siloam Hospital",
        claim_amount = 1500000.0,
        currency = "IDR",
        description = "Routine outpatient consultation and lab work",
        blob_url = "claims/receipt_siloam_emp0001.pdf"
    )

    res_benefit = service.process_benefit_claim(req_benefit)
    print(f"\n2. Health Benefit Claim Result:")
    print(f"Is Success: {res_benefit.is_success}")
    if res_benefit.payload:
        res_b = res_benefit.payload
        print(f"Request Number: {res_b.request_number}")
        print(f"Status: {res_b.request_status} | Recommendation: {res_b.recommendation} | Eligibility: {res_b.eligibility_result}")
        print(f"Claim Amount: {res_b.currency} {res_b.claim_amount:,.2f} | Eligible Amount: {res_b.currency} {res_b.eligible_amount:,.2f}")
        print(f"Reasoning: {res_b.reasoning_summary}")
        for r in res_b.rule_results:
            symbol = "✓" if r.passed else "✗"
            print(f"  [{symbol}] {r.rule_name}: {r.details}")

    req_expense = ProcessExpenseClaimRequest(
        employee_number = "EMP-0001",
        expense_category = "TRAVEL",
        expense_date = date(2026, 8, 20),
        merchant = "Garuda Indonesia",
        claim_amount = 2500000.0,
        currency = "IDR",
        description = "Business flight ticket for client meeting",
        blob_url = "expenses/flight_garuda_emp0001.pdf"
    )

    res_expense = service.process_expense_claim(req_expense)
    print(f"\n3. Expense Claim Result:")
    print(f"Is Success: {res_expense.is_success}")
    if res_expense.payload:
        res_e = res_expense.payload
        print(f"Request Number: {res_e.request_number}")
        print(f"Status: {res_e.request_status} | Recommendation: {res_e.recommendation} | Eligibility: {res_e.eligibility_result}")
        print(f"Claim Amount: {res_e.currency} {res_e.claim_amount:,.2f} | Eligible Amount: {res_e.currency} {res_e.eligible_amount:,.2f}")
        print(f"Reasoning: {res_e.reasoning_summary}")
        for r in res_e.rule_results:
            symbol = "✓" if r.passed else "✗"
            print(f"  [{symbol}] {r.rule_name}: {r.details}")


def test_agent_request_tools():
    print("\n==================================================")
    print("      Testing Agent Integration with Request Tools")
    print("==================================================")
    
    agent_service = AgentService()
    
    queries = [
        "I am employee EMP-0001. I want to request annual leave from 2026-10-01 to 2026-10-05 (5 days) for annual family vacation. Can you evaluate and submit this leave request for me?",
        "I am employee EMP-0001. I spent IDR 1,500,000 at Siloam Hospital on 2026-08-15 for HEALTH consultation. The receipt blob URL is claims/receipt_siloam_emp0001.pdf. Please evaluate and submit my health claim.",
        "I am employee EMP-0001. I paid IDR 2,500,000 to Garuda Indonesia on 2026-08-20 for TRAVEL. The receipt URL is expenses/flight_garuda_emp0001.pdf. Can you submit my expense reimbursement claim?"
    ]
    
    for query in queries:
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
    test_agent_request_tools()
