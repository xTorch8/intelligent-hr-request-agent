from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr = Field(..., description = "User email address")
    password: str = Field(..., description = "User plain text password")


class UserPayload(BaseModel):
    user_id: str = Field(..., description = "User UUID")
    employee_id: Optional[str] = Field(default = None, description = "Employee UUID")
    employee_number: Optional[str] = Field(default = None, description = "Employee Number e.g. EMP-0001")
    email: str = Field(..., description = "User email address")
    role: str = Field(..., description = "User role: EMPLOYEE, HR_ADMIN")
    first_name: Optional[str] = Field(default = None, description = "First name")
    last_name: Optional[str] = Field(default = None, description = "Last name")


class LoginResponse(BaseModel):
    access_token: str = Field(..., description = "Bearer JWT access token")
    token_type: str = Field(default = "bearer", description = "Token type")
    user_id: str = Field(..., description = "User UUID")
    employee_id: Optional[str] = Field(default = None, description = "Employee UUID")
    employee_number: Optional[str] = Field(default = None, description = "Employee Number e.g. EMP-0001")
    email: str = Field(..., description = "User email address")
    role: str = Field(..., description = "User role: EMPLOYEE, HR_ADMIN")
    first_name: Optional[str] = Field(default = None, description = "First name")
    last_name: Optional[str] = Field(default = None, description = "Last name")

