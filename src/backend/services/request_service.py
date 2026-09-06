from datetime import date, datetime
import logging
from typing import List, Optional

from ..models.api_model import APIResponseModel
from ..models.request_model import (
    BenefitClaimDecisionResponse,
    ExpenseClaimDecisionResponse,
    LeaveRequestDecisionResponse,
    ProcessBenefitClaimRequest,
    ProcessExpenseClaimRequest,
    ProcessLeaveRequest,
    RuleCheckResult
)
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

            has_overlap = self._request_repository.check_overlapping_leave(
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

    def process_benefit_claim(self, request_data: ProcessBenefitClaimRequest) -> APIResponseModel[Optional[BenefitClaimDecisionResponse]]:
        logging.info(f"[INFO][request_service.py][process_benefit_claim] Processing benefit claim for employee_number: {request_data.employee_number}")
        try:
            profile = self._employee_repository.get_employee_profile(request_data.employee_number)
            if not profile:
                return APIResponseModel[Optional[BenefitClaimDecisionResponse]](
                    is_success = False,
                    error = f"Employee '{request_data.employee_number}' not found.",
                    status_code = 404,
                    message = f"Employee '{request_data.employee_number}' not found.",
                    payload = None
                )

            benefit_resp = self._employee_repository.get_health_benefit(
                employee_number = request_data.employee_number,
                benefit_type = request_data.benefit_type
            )

            target_benefit = None
            if benefit_resp and benefit_resp.benefits:
                target_benefit = benefit_resp.benefits[0]

            rule_results: List[RuleCheckResult] = []

            is_active = profile.employment_status.upper() == "ACTIVE"
            rule_results.append(
                RuleCheckResult(
                    rule_name = "III.A Employee Eligibility",
                    passed = is_active,
                    details = f"Employee status is '{profile.employment_status}'. Must be 'ACTIVE'."
                )
            )

            has_plan = target_benefit is not None and target_benefit.status.upper() == "ACTIVE"
            rule_results.append(
                RuleCheckResult(
                    rule_name = "III.B Benefit Plan Eligibility",
                    passed = has_plan,
                    details = f"Active '{request_data.benefit_type}' benefit plan found." if has_plan else f"No active '{request_data.benefit_type}' benefit plan found for employee."
                )
            )

            coverage_percentage = (target_benefit.coverage_percentage / 100.0) if (target_benefit and target_benefit.coverage_percentage is not None) else 1.0
            eligible_amount = round(request_data.claim_amount * coverage_percentage, 2)
            rule_results.append(
                RuleCheckResult(
                    rule_name = "III.C Coverage Percentage Calculation",
                    passed = True,
                    details = f"Claim Amount ({request_data.claim_amount}) * Coverage ({coverage_percentage * 100}%) = Eligible Amount ({eligible_amount})."
                )
            )

            remaining_limit = target_benefit.remaining_limit if (target_benefit and target_benefit.remaining_limit is not None) else float("inf")
            within_annual_limit = eligible_amount <= remaining_limit
            rule_results.append(
                RuleCheckResult(
                    rule_name = "III.D Annual Limit Check",
                    passed = within_annual_limit,
                    details = f"Eligible Amount ({eligible_amount}) <= Remaining Limit ({remaining_limit})."
                )
            )

            effective_date = target_benefit.effective_date if target_benefit else request_data.service_date
            waiting_period_valid = request_data.service_date >= effective_date
            rule_results.append(
                RuleCheckResult(
                    rule_name = "III.E Waiting Period Check",
                    passed = waiting_period_valid,
                    details = f"Service Date ({request_data.service_date}) >= Benefit Effective Date ({effective_date})."
                )
            )

            has_documentation = bool(request_data.blob_url and request_data.blob_url.strip())
            rule_results.append(
                RuleCheckResult(
                    rule_name = "III.F Required Documentation",
                    passed = has_documentation,
                    details = "Medical receipt document blob URL exists." if has_documentation else "Required medical documentation receipt is missing."
                )
            )

            all_passed = all(r.passed for r in rule_results)
            if all_passed:
                recommendation = "APPROVE"
                eligibility_result = "ELIGIBLE"
                status = "PENDING_REVIEW"
                reasoning = "All health benefit claim eligibility rules passed. Recommendation: APPROVE."
            else:
                recommendation = "REJECT"
                eligibility_result = "NOT_ELIGIBLE"
                status = "REJECTED"
                failed_rules = [r.rule_name for r in rule_results if not r.passed]
                reasoning = f"Benefit claim failed deterministic rules: {', '.join(failed_rules)}. Recommendation: REJECT."

            decision = self._request_repository.create_and_evaluate_benefit_claim(
                request_data = request_data,
                employee_id = profile.employee_id,
                eligible_amount = eligible_amount,
                recommendation = recommendation,
                eligibility_result = eligibility_result,
                rule_results = rule_results,
                reasoning_summary = reasoning,
                status = status
            )

            return APIResponseModel[Optional[BenefitClaimDecisionResponse]](
                is_success = True,
                status_code = 200,
                message = "Health/Benefit claim processed and evaluated successfully",
                payload = decision
            )
        except Exception as e:
            logging.error(f"[ERROR][request_service.py][process_benefit_claim] Failed processing benefit claim. Error: {e}")
            return APIResponseModel[Optional[BenefitClaimDecisionResponse]](
                is_success = False,
                error = str(e),
                status_code = 500,
                message = f"Failed to process benefit claim: {str(e)}",
                payload = None
            )

    def process_expense_claim(self, request_data: ProcessExpenseClaimRequest) -> APIResponseModel[Optional[ExpenseClaimDecisionResponse]]:
        logging.info(f"[INFO][request_service.py][process_expense_claim] Processing expense claim for employee_number: {request_data.employee_number}")
        try:
            profile = self._employee_repository.get_employee_profile(request_data.employee_number)
            if not profile:
                return APIResponseModel[Optional[ExpenseClaimDecisionResponse]](
                    is_success = False,
                    error = f"Employee '{request_data.employee_number}' not found.",
                    status_code = 404,
                    message = f"Employee '{request_data.employee_number}' not found.",
                    payload = None
                )

            rule_results: List[RuleCheckResult] = []

            is_active = profile.employment_status.upper() == "ACTIVE"
            rule_results.append(
                RuleCheckResult(
                    rule_name = "II.A Employee Eligibility",
                    passed = is_active,
                    details = f"Employee status is '{profile.employment_status}'. Must be 'ACTIVE'."
                )
            )

            allowed_categories = ["TRAVEL", "MEALS", "SUPPLIES", "INTERNET", "TRANSPORT", "TRAINING"]
            is_allowed_category = request_data.expense_category.upper() in allowed_categories
            rule_results.append(
                RuleCheckResult(
                    rule_name = "II.B Supported Category",
                    passed = is_allowed_category,
                    details = f"Expense Category '{request_data.expense_category}' is supported." if is_allowed_category else f"Expense Category '{request_data.expense_category}' is not in allowed categories: {allowed_categories}."
                )
            )

            category_limits = {
                "TRAVEL": 15000000.0,
                "MEALS": 1000000.0,
                "SUPPLIES": 5000000.0,
                "INTERNET": 1000000.0,
                "TRANSPORT": 2000000.0,
                "TRAINING": 10000000.0
            }
            category_limit = category_limits.get(request_data.expense_category.upper(), 5000000.0)
            within_limit = request_data.claim_amount <= category_limit
            rule_results.append(
                RuleCheckResult(
                    rule_name = "II.C Maximum Claim Limit",
                    passed = within_limit,
                    details = f"Claim Amount ({request_data.claim_amount}) <= Category Limit ({category_limit})."
                )
            )

            reimbursement_rates = {
                "TRAVEL": 1.0,
                "MEALS": 0.8,
                "SUPPLIES": 1.0,
                "INTERNET": 1.0,
                "TRANSPORT": 1.0,
                "TRAINING": 1.0
            }
            rate = reimbursement_rates.get(request_data.expense_category.upper(), 1.0)
            eligible_amount = round(request_data.claim_amount * rate, 2)
            rule_results.append(
                RuleCheckResult(
                    rule_name = "II.D Reimbursement Percentage",
                    passed = True,
                    details = f"Claim Amount ({request_data.claim_amount}) * Rate ({rate * 100}%) = Eligible Amount ({eligible_amount})."
                )
            )

            is_duplicate = self._request_repository.check_duplicate_expense_claim(
                employee_id = profile.employee_id,
                expense_date = request_data.expense_date,
                claim_amount = request_data.claim_amount,
                expense_category = request_data.expense_category
            )
            rule_results.append(
                RuleCheckResult(
                    rule_name = "II.E Duplicate Claim Check",
                    passed = not is_duplicate,
                    details = "Duplicate claim detected for same date, amount, and category." if is_duplicate else "No duplicate claim detected."
                )
            )

            has_receipt = bool(request_data.blob_url and request_data.blob_url.strip())
            rule_results.append(
                RuleCheckResult(
                    rule_name = "II.F Required Documentation",
                    passed = has_receipt,
                    details = "Receipt document blob URL exists." if has_receipt else "Required receipt documentation is missing."
                )
            )

            all_passed = all(r.passed for r in rule_results)
            if all_passed:
                recommendation = "APPROVE"
                eligibility_result = "ELIGIBLE"
                status = "PENDING_REVIEW"
                reasoning = "All expense claim eligibility rules passed. Recommendation: APPROVE."
            else:
                recommendation = "REJECT"
                eligibility_result = "NOT_ELIGIBLE"
                status = "REJECTED"
                failed_rules = [r.rule_name for r in rule_results if not r.passed]
                reasoning = f"Expense claim failed deterministic rules: {', '.join(failed_rules)}. Recommendation: REJECT."

            decision = self._request_repository.create_and_evaluate_expense_claim(
                request_data = request_data,
                employee_id = profile.employee_id,
                eligible_amount = eligible_amount,
                recommendation = recommendation,
                eligibility_result = eligibility_result,
                rule_results = rule_results,
                reasoning_summary = reasoning,
                status = status
            )

            return APIResponseModel[Optional[ExpenseClaimDecisionResponse]](
                is_success = True,
                status_code = 200,
                message = "Expense claim processed and evaluated successfully",
                payload = decision
            )
        except Exception as e:
            logging.error(f"[ERROR][request_service.py][process_expense_claim] Failed processing expense claim. Error: {e}")
            return APIResponseModel[Optional[ExpenseClaimDecisionResponse]](
                is_success = False,
                error = str(e),
                status_code = 500,
                message = f"Failed to process expense claim: {str(e)}",
                payload = None
            )
