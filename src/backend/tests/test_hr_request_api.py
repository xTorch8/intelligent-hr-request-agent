import logging
from datetime import date
from fastapi.testclient import TestClient

from src.backend.main import app
from src.backend.models.request_model import (
    GetRequestListFilterRequest,
    ProcessLeaveRequest,
    UpdateRequestStatusRequest
)
from src.backend.repositories.employee_repository import EmployeeRepository
from src.backend.services.request_service import RequestService

client = TestClient(app)


def test_hr_request_workflow():
    print("\n==================================================")
    print("      Testing HR Request APIs (List/Accept/Reject)")
    print("==================================================")

    service = RequestService()
    emp_repo = EmployeeRepository()

    init_bal = emp_repo.get_leave_balance("EMP-0001", year = 2026)
    init_used = 0.0
    if init_bal and init_bal.balances:
        for b in init_bal.balances:
            if b.leave_type.upper() == "ANNUAL":
                init_used = b.used_days
                break

    req_leave = ProcessLeaveRequest(
        employee_number = "EMP-0001",
        leave_type = "ANNUAL",
        start_date = date(2026, 11, 1),
        end_date = date(2026, 11, 5),
        requested_days = 5.0,
        reason = "HR API test leave request"
    )
    leave_resp = service.process_leave_request(req_leave)
    assert leave_resp.is_success is True
    assert leave_resp.payload is not None
    target_request_id = leave_resp.payload.request_id
    print(f"Created Test Request ID: {target_request_id}")

    list_resp = client.get("/api/request/list")
    assert list_resp.status_code == 200
    list_json = list_resp.json()
    assert list_json["is_success"] is True
    print(f"1. GET /api/request/list total count: {list_json['payload']['total_count']}")

    list_filtered = client.get("/api/request/list?status=PENDING_REVIEW&employee_number=EMP-0001")
    assert list_filtered.status_code == 200
    filtered_json = list_filtered.json()
    assert filtered_json["is_success"] is True
    print(f"2. GET /api/request/list with filters total count: {filtered_json['payload']['total_count']}")

    accept_body = {
        "request_id": target_request_id,
        "actor_id": None,
        "reason": "HR Admin approval test"
    }
    accept_resp = client.post("/api/request/accept", json = accept_body)
    assert accept_resp.status_code == 200
    accept_json = accept_resp.json()
    assert accept_json["is_success"] is True
    assert accept_json["payload"] is True
    print(f"3. POST /api/request/accept result: {accept_json['message']}")

    post_accept_bal = emp_repo.get_leave_balance("EMP-0001", year = 2026)
    post_accept_used = 0.0
    if post_accept_bal and post_accept_bal.balances:
        for b in post_accept_bal.balances:
            if b.leave_type.upper() == "ANNUAL":
                post_accept_used = b.used_days
                break
    print(f"   Leave balance used_days after accept: {post_accept_used} (was {init_used})")

    reject_body = {
        "request_id": target_request_id,
        "actor_id": None,
        "reason": "HR Admin rejection test"
    }
    reject_resp = client.post("/api/request/reject", json = reject_body)
    assert reject_resp.status_code == 200
    reject_json = reject_resp.json()
    assert reject_json["is_success"] is True
    assert reject_json["payload"] is True
    print(f"4. POST /api/request/reject result: {reject_json['message']}")

    post_reject_bal = emp_repo.get_leave_balance("EMP-0001", year = 2026)
    post_reject_used = 0.0
    if post_reject_bal and post_reject_bal.balances:
        for b in post_reject_bal.balances:
            if b.leave_type.upper() == "ANNUAL":
                post_reject_used = b.used_days
                break
    print(f"   Leave balance used_days after reject: {post_reject_used}")


if __name__ == "__main__":
    test_hr_request_workflow()

