from datetime import date, datetime
import logging
from typing import List, Optional

from ..models.api_model import APIResponseModel
from ..models.request_model import LeaveRequestDecisionResponse, ProcessLeaveRequest, RuleCheckResult
from ..repositories.employee_repository import EmployeeRepository
from ..repositories.request_repository import RequestRepository


class RequestService:
    def __init__(
        self,
        request_repository: Optional[RequestRepository] = None,
        employee_repository: Optional[EmployeeRepository] = None
    ):
        self._request_repository = request_repository if request_repository else RequestRepository()
        self._employee_repository = employee_repository if employee_repository else EmployeeRepository()

    def process_leave_request(self, request_data: ProcessLeaveRequest) -> APIResponseModel[Optional[LeaveRequestDecisionResponse]]:
        logging.info(f"[INFO][request_service.py][process_leave_request] Processing leave request for employee_number: {request_data.employee_number}")
        try:
            profile = self._employee_repository.get_employee_profile(request_data.employee_number)
            if not profile:
                return APIResponseModel[Optional[LeaveRequestDecisionResponse]](
                    is_success = False,
                    error = f"Employee '{request_data.employee_number}' not found.",
                    status_code = 404,
                    message = f"Employee '{request_data.employee_number}' not found.",
                    payload = None
                )

            balance_resp = self._employee_repository.get_leave_balance(request_data.employee_number, year = request_data.start_date.year)
            available_balance = 0.0
            if balance_resp and balance_resp.balances:
                for b in balance_resp.balances:
                    if b.leave_type.upper() == request_data.leave_type.upper():
                        available_balance = b.remaining_days
                        break

            rule_results: List[RuleCheckResult] = []

            is_active = profile.employment_status.upper() == "ACTIVE"
            rule_results.append(
                RuleCheckResult(
                    rule_name = "Employment Eligibility",
                    passed = is_active,
                    details = f"Employee status is '{profile.employment_status}'. Must be 'ACTIVE'."
                )
            )

            has_enough_balance = request_data.requested_days <= available_balance
            rule_results.append(
                RuleCheckResult(
                    rule_name = "Leave Balance Availability",
                    passed = has_enough_balance,
                    details = f"Requested: {request_data.requested_days} days. Available balance: {available_balance} days."
                )
            )

            policy_max_consecutive = 14.0
            consecutive_valid = request_data.requested_days <= policy_max_consecutive
            rule_results.append(
                RuleCheckResult(
                    rule_name = "Maximum Consecutive Days",
                    passed = consecutive_valid,
                    details = f"Requested: {request_data.requested_days} days. Maximum allowed policy limit: {policy_max_consecutive} days."
                )
            )

            today = date.today()
            notice_days = (request_data.start_date - today).days
            min_notice_period = 3
            notice_valid = notice_days >= min_notice_period
            rule_results.append(
                RuleCheckResult(
                    rule_name = "Advanced Notice Period",
                    passed = notice_valid,
                    details = f"Notice provided: {notice_days} days prior to leave start. Minimum required notice: {min_notice_period} days."
                )
            )

            has_overlap = self._request_repository._check_overlapping_leave(
                employee_id = profile.employee_id,
                start_date = request_data.start_date,
                end_date = request_data.end_date
            )
            rule_results.append(
                RuleCheckResult(
                    rule_name = "Overlapping Leave Protection",
                    passed = not has_overlap,
                    details = "Overlap detected with existing leave request." if has_overlap else "No overlapping approved or pending leave detected."
                )
            )

            all_passed = all(r.passed for r in rule_results)
            if all_passed:
                recommendation = "APPROVE"
                eligibility_result = "ELIGIBLE"
                status = "PENDING_REVIEW"
                reasoning = "All business rule checks passed successfully. Recommendation: APPROVE."
            else:
                recommendation = "REJECT"
                eligibility_result = "NOT_ELIGIBLE"
                status = "REJECTED"
                failed_rules = [r.rule_name for r in rule_results if not r.passed]
                reasoning = f"Failed deterministic business rules: {', '.join(failed_rules)}."

            decision = self._request_repository.create_and_evaluate_leave_request(
                request_data = request_data,
                employee_id = profile.employee_id,
                recommendation = recommendation,
                eligibility_result = eligibility_result,
                rule_results = rule_results,
                reasoning_summary = reasoning,
                status = status
            )

            return APIResponseModel[Optional[LeaveRequestDecisionResponse]](
                is_success = True,
                status_code = 200,
                message = "Leave request processed and evaluated successfully",
                payload = decision
            )
        except Exception as e:
            logging.error(f"[ERROR][request_service.py][process_leave_request] Failed processing leave request. Error: {e}")
            return APIResponseModel[Optional[LeaveRequestDecisionResponse]](
                is_success = False,
                error = str(e),
                status_code = 500,
                message = f"Failed to process leave request: {str(e)}",
                payload = None
            )

