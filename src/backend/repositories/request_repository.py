from datetime import date
import json
import logging
import random
from typing import Dict, List, Optional

from ..clients.postgres_client import PostgresClient
from ..models.request_model import LeaveRequestDecisionResponse, ProcessLeaveRequest, RuleCheckResult


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

    def _check_overlapping_leave(self, employee_id: str, start_date: date, end_date: date) -> bool:
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

