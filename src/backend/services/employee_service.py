import logging
from typing import Optional

from ..models.api_model import APIResponseModel
from ..models.employee_model import (
    EmployeeProfileRequest,
    EmployeeProfileResponse,
    HealthBenefitRequest,
    HealthBenefitResponse,
    LeaveBalanceRequest,
    LeaveBalanceResponse
)
from ..repositories.employee_repository import EmployeeRepository


class EmployeeService:
    def __init__(self, repository: Optional[EmployeeRepository] = None):
        self._repository = repository if repository else EmployeeRepository()

    def get_employee_profile(self, request: EmployeeProfileRequest) -> APIResponseModel[Optional[EmployeeProfileResponse]]:
        logging.info(f"[INFO][employee_service.py][get_employee_profile] Fetching profile for employee_number: {request.employee_number}")
        try:
            profile = self._repository.get_employee_profile(request.employee_number)
            if not profile:
                return APIResponseModel[Optional[EmployeeProfileResponse]](
                    is_success = False,
                    error = f"Employee profile for employee_number '{request.employee_number}' not found.",
                    status_code = 404,
                    message = f"Employee profile for employee_number '{request.employee_number}' not found.",
                    payload = None
                )
            
            return APIResponseModel[Optional[EmployeeProfileResponse]](
                is_success = True,
                status_code = 200,
                message = f"Employee profile for employee_number '{request.employee_number}' retrieved successfully.",
                payload = profile
            )
        except Exception as e:
            logging.error(f"[ERROR][employee_service.py][get_employee_profile] Error: {e}")
            return APIResponseModel[Optional[EmployeeProfileResponse]](
                is_success = False,
                error = str(e),
                status_code = 500,
                message = f"Failed to fetch employee profile: {str(e)}",
                payload = None
            )

    def get_leave_balance(self, request: LeaveBalanceRequest) -> APIResponseModel[Optional[LeaveBalanceResponse]]:
        logging.info(f"[INFO][employee_service.py][get_leave_balance] Fetching leave balance for employee_number: {request.employee_number}, year: {request.year}")
        try:
            balance = self._repository.get_leave_balance(request.employee_number, year = request.year)
            if not balance:
                return APIResponseModel[Optional[LeaveBalanceResponse]](
                    is_success = False,
                    error = f"Leave balance for employee_number '{request.employee_number}' not found.",
                    status_code = 404,
                    message = f"Leave balance for employee_number '{request.employee_number}' not found.",
                    payload = None
                )
            return APIResponseModel[Optional[LeaveBalanceResponse]](
                is_success = True,
                status_code = 200,
                message = f"Leave balance for employee_number '{request.employee_number}' retrieved successfully.",
                payload = balance
            )
        except Exception as e:
            logging.error(f"[ERROR][employee_service.py][get_leave_balance] Error: {e}")
            return APIResponseModel[Optional[LeaveBalanceResponse]](
                is_success = False,
                error = str(e),
                status_code = 500,
                message = f"Failed to fetch leave balance: {str(e)}",
                payload = None
            )

    def get_health_benefit(self, request: HealthBenefitRequest) -> APIResponseModel[Optional[HealthBenefitResponse]]:
        logging.info(f"[INFO][employee_service.py][get_health_benefit] Fetching health benefits for employee_number: {request.employee_number}")
        try:
            benefit = self._repository.get_health_benefit(request.employee_number, benefit_type = request.benefit_type)
            if not benefit:
                return APIResponseModel[Optional[HealthBenefitResponse]](
                    is_success = False,
                    error = f"Health benefits for employee_number '{request.employee_number}' not found.",
                    status_code = 404,
                    message = f"Health benefits for employee_number '{request.employee_number}' not found.",
                    payload = None
                )
            return APIResponseModel[Optional[HealthBenefitResponse]](
                is_success = True,
                status_code = 200,
                message = f"Health benefits for employee_number '{request.employee_number}' retrieved successfully.",
                payload = benefit
            )
        except Exception as e:
            logging.error(f"[ERROR][employee_service.py][get_health_benefit] Error: {e}")
            return APIResponseModel[Optional[HealthBenefitResponse]](
                is_success = False,
                error = str(e),
                status_code = 500,
                message = f"Failed to fetch health benefits: {str(e)}",
                payload = None
            )
