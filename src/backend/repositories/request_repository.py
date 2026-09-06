from datetime import date
import json
import logging
import random
from typing import Dict, List, Optional

from ..clients.postgres_client import PostgresClient
from ..models.request_model import (
    BenefitClaimDecisionResponse,
    ExpenseClaimDecisionResponse,
    LeaveRequestDecisionResponse,
    ProcessBenefitClaimRequest,
    ProcessExpenseClaimRequest,
    ProcessLeaveRequest,
    RuleCheckResult
)


class RequestRepository:
    def __init__(self):
        self._postgres_client = PostgresClient()

    def create_and_evaluate_leave_request(
        self,
        request_data: ProcessLeaveRequest,
        employee_id: str,
        recommendation: str,
        eligibility_result: str,
        rule_results: List[RuleCheckResult],
        reasoning_summary: str,
        status: str = "PENDING_REVIEW"
    ) -> LeaveRequestDecisionResponse:
        logging.info(f"[INFO][request_repository.py][create_and_evaluate_leave_request] Persisting leave request for employee_id: {employee_id}")
        conn = self._postgres_client.get_connection()
        cursor = conn.cursor()

        try:
            request_number = f"REQ-LEAVE-{random.randint(10000, 99999)}"
            request_title = f"{request_data.leave_type.capitalize()} Leave Request ({request_data.requested_days} days)"

            insert_request_sql = """
                INSERT INTO requests (employee_id, request_number, request_type, status, title, description)
                VALUES (%s::uuid, %s, 'LEAVE', %s, %s, %s)
                RETURNING id, request_number, status, submitted_at;
            """
            cursor.execute(
                insert_request_sql,
                (employee_id, request_number, status, request_title, request_data.reason)
            )
            req_row = cursor.fetchone()
            req_id, req_num, req_status, submitted_at = req_row

            insert_leave_req_sql = """
                INSERT INTO leave_requests (request_id, leave_type, start_date, end_date, requested_days, reason)
                VALUES (%s::uuid, %s, %s, %s, %s, %s);
            """
            cursor.execute(
                insert_leave_req_sql,
                (
                    str(req_id),
                    request_data.leave_type,
                    request_data.start_date,
                    request_data.end_date,
                    request_data.requested_days,
                    request_data.reason
                )
            )

            insert_agent_run_sql = """
                INSERT INTO agent_runs (request_id, agent_version, status, input_tokens, output_tokens, error_message)
                VALUES (%s::uuid, 'v1.0', 'COMPLETED', 150, 200, NULL)
                RETURNING id;
            """
            cursor.execute(insert_agent_run_sql, (str(req_id),))
            run_id = cursor.fetchone()[0]

            rule_results_json = json.dumps([r.model_dump() for r in rule_results])
            insert_decision_sql = """
                INSERT INTO request_decisions (
                    request_id, agent_run_id, recommendation, eligibility_result,
                    rule_results, policy_references, reasoning_summary
                )
                VALUES (%s::uuid, %s::uuid, %s, %s, %s::jsonb, '{"policy_code": "POL-LEAVE-001"}'::jsonb, %s);
            """
            cursor.execute(
                insert_decision_sql,
                (
                    str(req_id),
                    str(run_id),
                    recommendation,
                    eligibility_result,
                    rule_results_json,
                    reasoning_summary
                )
            )

            audit_metadata = json.dumps({
                "recommendation": recommendation,
                "eligibility_result": eligibility_result,
                "requested_days": float(request_data.requested_days)
            })
            insert_audit_sql = """
                INSERT INTO audit_logs (request_id, actor_type, actor_id, action, previous_status, new_status, metadata)
                VALUES (%s::uuid, 'AGENT', %s::uuid, 'EVALUATE_LEAVE_ELIGIBILITY', 'SUBMITTED', %s, %s::jsonb);
            """
            cursor.execute(
                insert_audit_sql,
                (str(req_id), employee_id, req_status, audit_metadata)
            )

            conn.commit()

            return LeaveRequestDecisionResponse(
                request_id = str(req_id),
                request_number = req_num,
                employee_number = request_data.employee_number,
                leave_type = request_data.leave_type,
                start_date = request_data.start_date,
                end_date = request_data.end_date,
                requested_days = request_data.requested_days,
                request_status = req_status,
                recommendation = recommendation,
                eligibility_result = eligibility_result,
                rule_results = rule_results,
                reasoning_summary = reasoning_summary,
                agent_run_id = str(run_id),
                submitted_at = submitted_at
            )
        except Exception as e:
            conn.rollback()
            logging.error(f"[ERROR][request_repository.py][create_and_evaluate_leave_request] Failed transaction. Error: {e}")
            raise e
        finally:
            cursor.close()
            conn.close()

    def create_and_evaluate_benefit_claim(
        self,
        request_data: ProcessBenefitClaimRequest,
        employee_id: str,
        eligible_amount: float,
        recommendation: str,
        eligibility_result: str,
        rule_results: List[RuleCheckResult],
        reasoning_summary: str,
        status: str = "PENDING_REVIEW"
    ) -> BenefitClaimDecisionResponse:
        logging.info(f"[INFO][request_repository.py][create_and_evaluate_benefit_claim] Persisting benefit claim for employee_id: {employee_id}")
        conn = self._postgres_client.get_connection()
        cursor = conn.cursor()

        try:
            request_number = f"REQ-BEN-{random.randint(10000, 99999)}"
            request_title = f"{request_data.benefit_type.capitalize()} Benefit Claim ({request_data.currency} {request_data.claim_amount:,.2f})"

            insert_request_sql = """
                INSERT INTO requests (employee_id, request_number, request_type, status, title, description)
                VALUES (%s::uuid, %s, 'BENEFIT', %s, %s, %s)
                RETURNING id, request_number, status, submitted_at;
            """
            cursor.execute(
                insert_request_sql,
                (employee_id, request_number, status, request_title, request_data.description)
            )
            req_row = cursor.fetchone()
            req_id, req_num, req_status, submitted_at = req_row

            insert_benefit_claim_sql = """
                INSERT INTO benefit_claims (request_id, benefit_type, service_date, provider_name, claim_amount, currency, description, blob_url)
                VALUES (%s::uuid, %s, %s, %s, %s, %s, %s, %s);
            """
            cursor.execute(
                insert_benefit_claim_sql,
                (
                    str(req_id),
                    request_data.benefit_type,
                    request_data.service_date,
                    request_data.provider_name,
                    request_data.claim_amount,
                    request_data.currency,
                    request_data.description,
                    request_data.blob_url
                )
            )

            insert_agent_run_sql = """
                INSERT INTO agent_runs (request_id, agent_version, status, input_tokens, output_tokens, error_message)
                VALUES (%s::uuid, 'v1.0', 'COMPLETED', 160, 210, NULL)
                RETURNING id;
            """
            cursor.execute(insert_agent_run_sql, (str(req_id),))
            run_id = cursor.fetchone()[0]

            rule_results_json = json.dumps([r.model_dump() for r in rule_results])
            insert_decision_sql = """
                INSERT INTO request_decisions (
                    request_id, agent_run_id, recommendation, eligibility_result,
                    eligible_amount, currency, rule_results, policy_references, reasoning_summary
                )
                VALUES (%s::uuid, %s::uuid, %s, %s, %s, %s, %s::jsonb, '{"policy_code": "POL-BEN-001"}'::jsonb, %s);
            """
            cursor.execute(
                insert_decision_sql,
                (
                    str(req_id),
                    str(run_id),
                    recommendation,
                    eligibility_result,
                    eligible_amount,
                    request_data.currency,
                    rule_results_json,
                    reasoning_summary
                )
            )

            audit_metadata = json.dumps({
                "recommendation": recommendation,
                "eligibility_result": eligibility_result,
                "claim_amount": float(request_data.claim_amount),
                "eligible_amount": float(eligible_amount)
            })
            insert_audit_sql = """
                INSERT INTO audit_logs (request_id, actor_type, actor_id, action, previous_status, new_status, metadata)
                VALUES (%s::uuid, 'AGENT', %s::uuid, 'EVALUATE_BENEFIT_ELIGIBILITY', 'SUBMITTED', %s, %s::jsonb);
            """
            cursor.execute(
                insert_audit_sql,
                (str(req_id), employee_id, req_status, audit_metadata)
            )

            conn.commit()

            return BenefitClaimDecisionResponse(
                request_id = str(req_id),
                request_number = req_num,
                employee_number = request_data.employee_number,
                benefit_type = request_data.benefit_type,
                service_date = request_data.service_date,
                provider_name = request_data.provider_name,
                claim_amount = request_data.claim_amount,
                eligible_amount = eligible_amount,
                currency = request_data.currency,
                request_status = req_status,
                recommendation = recommendation,
                eligibility_result = eligibility_result,
                rule_results = rule_results,
                reasoning_summary = reasoning_summary,
                agent_run_id = str(run_id),
                submitted_at = submitted_at
            )
        except Exception as e:
            conn.rollback()
            logging.error(f"[ERROR][request_repository.py][create_and_evaluate_benefit_claim] Failed transaction. Error: {e}")
            raise e
        finally:
            cursor.close()
            conn.close()

    def create_and_evaluate_expense_claim(
        self,
        request_data: ProcessExpenseClaimRequest,
        employee_id: str,
        eligible_amount: float,
        recommendation: str,
        eligibility_result: str,
        rule_results: List[RuleCheckResult],
        reasoning_summary: str,
        status: str = "PENDING_REVIEW"
    ) -> ExpenseClaimDecisionResponse:
        logging.info(f"[INFO][request_repository.py][create_and_evaluate_expense_claim] Persisting expense claim for employee_id: {employee_id}")
        conn = self._postgres_client.get_connection()
        cursor = conn.cursor()

        try:
            request_number = f"REQ-EXP-{random.randint(10000, 99999)}"
            request_title = f"{request_data.expense_category.capitalize()} Expense Claim ({request_data.currency} {request_data.claim_amount:,.2f})"

            insert_request_sql = """
                INSERT INTO requests (employee_id, request_number, request_type, status, title, description)
                VALUES (%s::uuid, %s, 'EXPENSE', %s, %s, %s)
                RETURNING id, request_number, status, submitted_at;
            """
            cursor.execute(
                insert_request_sql,
                (employee_id, request_number, status, request_title, request_data.description)
            )
            req_row = cursor.fetchone()
            req_id, req_num, req_status, submitted_at = req_row

            insert_expense_claim_sql = """
                INSERT INTO expense_claims (request_id, expense_category, expense_date, merchant, claim_amount, currency, description, blob_url)
                VALUES (%s::uuid, %s, %s, %s, %s, %s, %s, %s);
            """
            cursor.execute(
                insert_expense_claim_sql,
                (
                    str(req_id),
                    request_data.expense_category,
                    request_data.expense_date,
                    request_data.merchant,
                    request_data.claim_amount,
                    request_data.currency,
                    request_data.description,
                    request_data.blob_url
                )
            )

            insert_agent_run_sql = """
                INSERT INTO agent_runs (request_id, agent_version, status, input_tokens, output_tokens, error_message)
                VALUES (%s::uuid, 'v1.0', 'COMPLETED', 155, 205, NULL)
                RETURNING id;
            """
            cursor.execute(insert_agent_run_sql, (str(req_id),))
            run_id = cursor.fetchone()[0]

            rule_results_json = json.dumps([r.model_dump() for r in rule_results])
            insert_decision_sql = """
                INSERT INTO request_decisions (
                    request_id, agent_run_id, recommendation, eligibility_result,
                    eligible_amount, currency, rule_results, policy_references, reasoning_summary
                )
                VALUES (%s::uuid, %s::uuid, %s, %s, %s, %s, %s::jsonb, '{"policy_code": "POL-EXP-001"}'::jsonb, %s);
            """
            cursor.execute(
                insert_decision_sql,
                (
                    str(req_id),
                    str(run_id),
                    recommendation,
                    eligibility_result,
                    eligible_amount,
                    request_data.currency,
                    rule_results_json,
                    reasoning_summary
                )
            )

            audit_metadata = json.dumps({
                "recommendation": recommendation,
                "eligibility_result": eligibility_result,
                "claim_amount": float(request_data.claim_amount),
                "eligible_amount": float(eligible_amount)
            })
            insert_audit_sql = """
                INSERT INTO audit_logs (request_id, actor_type, actor_id, action, previous_status, new_status, metadata)
                VALUES (%s::uuid, 'AGENT', %s::uuid, 'EVALUATE_EXPENSE_ELIGIBILITY', 'SUBMITTED', %s, %s::jsonb);
            """
            cursor.execute(
                insert_audit_sql,
                (str(req_id), employee_id, req_status, audit_metadata)
            )

            conn.commit()

            return ExpenseClaimDecisionResponse(
                request_id = str(req_id),
                request_number = req_num,
                employee_number = request_data.employee_number,
                expense_category = request_data.expense_category,
                expense_date = request_data.expense_date,
                merchant = request_data.merchant,
                claim_amount = request_data.claim_amount,
                eligible_amount = eligible_amount,
                currency = request_data.currency,
                request_status = req_status,
                recommendation = recommendation,
                eligibility_result = eligibility_result,
                rule_results = rule_results,
                reasoning_summary = reasoning_summary,
                agent_run_id = str(run_id),
                submitted_at = submitted_at
            )
        except Exception as e:
            conn.rollback()
            logging.error(f"[ERROR][request_repository.py][create_and_evaluate_expense_claim] Failed transaction. Error: {e}")
            raise e
        finally:
            cursor.close()
            conn.close()

    def check_duplicate_expense_claim(self, employee_id: str, expense_date: date, claim_amount: float, expense_category: str) -> bool:
        conn = self._postgres_client.get_connection()
        cursor = conn.cursor()

        query = """
            SELECT COUNT(ec.id)
            FROM expense_claims ec
            JOIN requests r ON ec.request_id = r.id
            WHERE r.employee_id = %s::uuid
              AND ec.expense_date = %s
              AND ec.claim_amount = %s
              AND ec.expense_category = %s
              AND r.status IN ('SUBMITTED', 'PROCESSING', 'PENDING_REVIEW', 'APPROVED');
        """

        try:
            cursor.execute(query, (employee_id, expense_date, claim_amount, expense_category))
            count = cursor.fetchone()[0]
            return count > 0
        except Exception as e:
            logging.error(f"[ERROR][request_repository.py][check_duplicate_expense_claim] Query failed. Error: {e}")
            return False
        finally:
            cursor.close()
            conn.close()

    def check_overlapping_leave(self, employee_id: str, start_date: date, end_date: date) -> bool:
        conn = self._postgres_client.get_connection()
        cursor = conn.cursor()

        query = """
            SELECT COUNT(lr.id)
            FROM leave_requests lr
            JOIN requests r ON lr.request_id = r.id
            WHERE r.employee_id = %s::uuid
              AND r.status IN ('APPROVED', 'PROCESSING', 'PENDING_REVIEW')
              AND lr.start_date <= %s
              AND lr.end_date >= %s;
        """

        try:
            cursor.execute(query, (employee_id, end_date, start_date))
            count = cursor.fetchone()[0]
            return count > 0
        except Exception as e:
            logging.error(f"[ERROR][request_repository.py][check_overlapping_leave] Query failed. Error: {e}")
            return False
        finally:
            cursor.close()
            conn.close()
