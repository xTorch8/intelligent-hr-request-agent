from datetime import date
import json
import logging
import random
from typing import Dict, List, Optional

from ..clients.postgres_client import PostgresClient
from ..models.request_model import (
    BenefitClaimDecisionResponse,
    ExpenseClaimDecisionResponse,
    GetRequestListFilterRequest,
    LeaveRequestDecisionResponse,
    ProcessBenefitClaimRequest,
    ProcessExpenseClaimRequest,
    ProcessLeaveRequest,
    RequestListResponse,
    RequestSummaryItem,
    RuleCheckResult,
    UpdateRequestStatusRequest
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

    def get_requests(self, filter_req: GetRequestListFilterRequest) -> RequestListResponse:
        logging.info(f"[INFO][request_repository.py][get_requests] Querying request list with filters: {filter_req}")
        conn = self._postgres_client.get_connection()
        cursor = conn.cursor()

        query = """
            SELECT r.id, r.request_number, r.employee_id, e.employee_number,
                   e.first_name || ' ' || e.last_name AS employee_name, e.department,
                   r.request_type, r.status, r.title, r.description,
                   rd.recommendation, rd.eligibility_result, rd.reasoning_summary,
                   r.submitted_at, r.updated_at
            FROM requests r
            JOIN employees e ON r.employee_id = e.id
            LEFT JOIN request_decisions rd ON rd.request_id = r.id
            WHERE (%s::text IS NULL OR r.request_type = %s::text)
              AND (%s::text IS NULL OR r.status = %s::text)
              AND (%s::text IS NULL OR e.employee_number = %s::text)
            ORDER BY r.submitted_at DESC;
        """

        try:
            cursor.execute(
                query,
                (
                    filter_req.request_type, filter_req.request_type,
                    filter_req.status, filter_req.status,
                    filter_req.employee_number, filter_req.employee_number
                )
            )
            rows = cursor.fetchall()
            items: List[RequestSummaryItem] = []

            for row in rows:
                req_id, req_num, emp_id, emp_num, emp_name, dept, req_type, st, title, desc, rec, elig, reason, sub_at, up_at = row
                items.append(
                    RequestSummaryItem(
                        request_id = str(req_id),
                        request_number = req_num,
                        employee_id = str(emp_id),
                        employee_number = emp_num,
                        employee_name = emp_name,
                        department = dept,
                        request_type = req_type,
                        status = st,
                        title = title,
                        description = desc,
                        recommendation = rec,
                        eligibility_result = elig,
                        reasoning_summary = reason,
                        submitted_at = sub_at,
                        updated_at = up_at
                    )
                )

            return RequestListResponse(
                total_count = len(items),
                requests = items
            )
        except Exception as e:
            logging.error(f"[ERROR][request_repository.py][get_requests] Failed query. Error: {e}")
            raise e
        finally:
            cursor.close()
            conn.close()

    def update_request_status(
        self,
        request_id: str,
        new_status: str,
        actor_id: Optional[str] = None,
        reason: Optional[str] = None
    ) -> bool:
        logging.info(f"[INFO][request_repository.py][update_request_status] Updating request {request_id} status to {new_status}")
        conn = self._postgres_client.get_connection()
        cursor = conn.cursor()

        try:
            select_sql = "SELECT status, employee_id, request_type FROM requests WHERE id = %s::uuid;"
            cursor.execute(select_sql, (request_id,))
            row = cursor.fetchone()
            if not row:
                return False

            prev_status, employee_id, request_type = row

            update_sql = """
                UPDATE requests
                SET status = %s,
                    completed_at = CASE WHEN %s IN ('APPROVED', 'REJECTED', 'COMPLETED', 'CANCELLED') THEN CURRENT_TIMESTAMP ELSE completed_at END
                WHERE id = %s::uuid;
            """
            cursor.execute(update_sql, (new_status, new_status, request_id))

            if prev_status != "APPROVED" and new_status == "APPROVED":
                if request_type == "LEAVE":
                    leave_sql = """
                        SELECT leave_type, requested_days, start_date
                        FROM leave_requests
                        WHERE request_id = %s::uuid;
                    """
                    cursor.execute(leave_sql, (request_id,))
                    l_row = cursor.fetchone()
                    if l_row:
                        leave_type, req_days, start_date = l_row
                        req_year = start_date.year
                        update_lb_sql = """
                            UPDATE leave_balances
                            SET used_days = used_days + %s,
                                remaining_days = GREATEST(0, remaining_days - %s)
                            WHERE employee_id = %s::uuid
                              AND UPPER(leave_type) = UPPER(%s)
                              AND year = %s;
                        """
                        cursor.execute(update_lb_sql, (req_days, req_days, employee_id, leave_type, req_year))
                elif request_type == "BENEFIT":
                    benefit_sql = """
                        SELECT bc.benefit_type, COALESCE(rd.eligible_amount, bc.claim_amount)
                        FROM benefit_claims bc
                        LEFT JOIN request_decisions rd ON rd.request_id = bc.request_id
                        WHERE bc.request_id = %s::uuid;
                    """
                    cursor.execute(benefit_sql, (request_id,))
                    b_row = cursor.fetchone()
                    if b_row:
                        b_type, el_amt = b_row
                        update_eb_sql = """
                            UPDATE employee_benefits
                            SET used_amount = used_amount + %s
                            WHERE employee_id = %s::uuid
                              AND UPPER(benefit_type) = UPPER(%s)
                              AND status = 'ACTIVE';
                        """
                        cursor.execute(update_eb_sql, (el_amt, employee_id, b_type))
            elif prev_status == "APPROVED" and new_status in ("REJECTED", "CANCELLED"):
                if request_type == "LEAVE":
                    leave_sql = """
                        SELECT leave_type, requested_days, start_date
                        FROM leave_requests
                        WHERE request_id = %s::uuid;
                    """
                    cursor.execute(leave_sql, (request_id,))
                    l_row = cursor.fetchone()
                    if l_row:
                        leave_type, req_days, start_date = l_row
                        req_year = start_date.year
                        update_lb_sql = """
                            UPDATE leave_balances
                            SET used_days = GREATEST(0, used_days - %s),
                                remaining_days = remaining_days + %s
                            WHERE employee_id = %s::uuid
                              AND UPPER(leave_type) = UPPER(%s)
                              AND year = %s;
                        """
                        cursor.execute(update_lb_sql, (req_days, req_days, employee_id, leave_type, req_year))
                elif request_type == "BENEFIT":
                    benefit_sql = """
                        SELECT bc.benefit_type, COALESCE(rd.eligible_amount, bc.claim_amount)
                        FROM benefit_claims bc
                        LEFT JOIN request_decisions rd ON rd.request_id = bc.request_id
                        WHERE bc.request_id = %s::uuid;
                    """
                    cursor.execute(benefit_sql, (request_id,))
                    b_row = cursor.fetchone()
                    if b_row:
                        b_type, el_amt = b_row
                        update_eb_sql = """
                            UPDATE employee_benefits
                            SET used_amount = GREATEST(0, used_amount - %s)
                            WHERE employee_id = %s::uuid
                              AND UPPER(benefit_type) = UPPER(%s)
                              AND status = 'ACTIVE';
                        """
                        cursor.execute(update_eb_sql, (el_amt, employee_id, b_type))

            audit_meta = json.dumps({"reason": reason or f"HR decision: {new_status}"})
            insert_audit_sql = """
                INSERT INTO audit_logs (request_id, actor_type, actor_id, action, previous_status, new_status, metadata)
                VALUES (%s::uuid, 'HR_ADMIN', %s::uuid, %s, %s, %s, %s::jsonb);
            """
            actor_uuid = actor_id if actor_id else None
            action_name = f"HR_{new_status}_REQUEST"
            cursor.execute(
                insert_audit_sql,
                (request_id, actor_uuid, action_name, prev_status, new_status, audit_meta)
            )

            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            logging.error(f"[ERROR][request_repository.py][update_request_status] Update failed. Error: {e}")
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
