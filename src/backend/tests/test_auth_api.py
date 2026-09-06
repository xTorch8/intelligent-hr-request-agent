from fastapi.testclient import TestClient

from src.backend.main import app
from src.backend.utils.auth_utils import create_access_token, hash_password, verify_password

client = TestClient(app)


def test_auth_utils():
    print("\n==================================================")
    print("      Testing Password Hashing & JWT Utils")
    print("==================================================")

    raw_pwd = "password123"
    hashed = hash_password(raw_pwd)
    assert verify_password(raw_pwd, hashed) is True
    assert verify_password("wrongpassword", hashed) is False
    print("✓ Password hashing & verification passed")

    token_data = {"sub": "test_user_id", "email": "test@company.com", "role": "EMPLOYEE"}
    token = create_access_token(token_data)
    assert token is not None
    print(f"✓ Created JWT Token: {token[:30]}...")


def test_auth_endpoints_and_guardrails():
    print("\n==================================================")
    print("      Testing Auth Endpoints & Security Guardrails")
    print("==================================================")

    emp_token_payload = {
        "sub": "20000000-0000-0000-0000-000000000001",
        "employee_id": "10000000-0000-0000-0000-000000000001",
        "employee_number": "EMP-0001",
        "email": "andi.pratama@company.com",
        "role": "EMPLOYEE"
    }
    emp_token = create_access_token(emp_token_payload)

    hr_token_payload = {
        "sub": "20000000-0000-0000-0000-000000000004",
        "employee_id": "10000000-0000-0000-0000-000000000004",
        "employee_number": "EMP-0004",
        "email": "rina.wijaya@company.com",
        "role": "HR_ADMIN"
    }
    hr_token = create_access_token(hr_token_payload)

    me_no_token = client.get("/api/auth/me")
    assert me_no_token.status_code == 401
    print("✓ Unauthenticated /api/auth/me correctly rejected with 401")

    me_emp = client.get("/api/auth/me", headers = {"Authorization": f"Bearer {emp_token}"})
    assert me_emp.status_code == 200
    assert me_emp.json()["payload"]["role"] == "EMPLOYEE"
    print("✓ Authenticated /api/auth/me returned EMPLOYEE payload")

    list_no_token = client.get("/api/request/list")
    assert list_no_token.status_code == 401
    print("✓ Unauthenticated /api/request/list rejected with 401")

    list_emp = client.get("/api/request/list", headers = {"Authorization": f"Bearer {emp_token}"})
    assert list_emp.status_code == 403
    print("✓ Non-HR user accessing /api/request/list correctly rejected with 403")

    list_hr = client.get("/api/request/list", headers = {"Authorization": f"Bearer {hr_token}"})
    assert list_hr.status_code == 200
    assert list_hr.json()["is_success"] is True
    print("✓ HR_ADMIN user accessing /api/request/list succeeded with 200")


if __name__ == "__main__":
    test_auth_utils()
    test_auth_endpoints_and_guardrails()

