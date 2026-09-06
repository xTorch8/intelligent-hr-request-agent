import logging
from typing import List, Optional

from ..clients.postgres_client import PostgresClient
from ..models.employee_model import EmployeeProfileResponse, LeaveBalanceResponse, LeaveTypeBalance


class EmployeeRepository:
    def __init__(self):
        self._postgres_client = PostgresClient()

    def get_employee_profile(self, employee_number: str) -> Optional[EmployeeProfileResponse]:
        logging.info(f"[INFO][employee_repository.py][get_employee_profile] Querying database for employee_number: {employee_number}")
        conn = self._postgres_client.get_connection()
        cursor = conn.cursor()

        query = """
            SELECT id, employee_number, first_name, last_name, email,
                   department, job_title, employment_type, employment_status, hire_date
            FROM employees
            WHERE employee_number = %s;
        """

        try:
            cursor.execute(query, (employee_number,))
            row = cursor.fetchone()
            if not row:
                logging.info(f"[INFO][employee_repository.py][get_employee_profile] Employee not found for employee_number: {employee_number}")
                return None

            emp_id, emp_num, first_name, last_name, email, dept, title, emp_type, emp_status, hire_date = row
            return EmployeeProfileResponse(
                employee_id = str(emp_id),
                employee_number = emp_num,
                first_name = first_name,
                last_name = last_name,
                email = email,
                department = dept,
                job_title = title,
                employment_type = emp_type,
                employment_status = emp_status,
                hire_date = hire_date
            )
        except Exception as e:
            logging.error(f"[ERROR][employee_repository.py][get_employee_profile] Database query failed. Error: {e}")
            raise e
        finally:
            cursor.close()
            conn.close()

    def get_leave_balance(self, employee_number: str, year: Optional[int] = 2026) -> Optional[LeaveBalanceResponse]:
        logging.info(f"[INFO][employee_repository.py][get_leave_balance] Querying leave_balances table for employee_number: {employee_number}, year: {year}")
        conn = self._postgres_client.get_connection()
        cursor = conn.cursor()

        query = """
            SELECT lb.employee_id, lb.leave_type, lb.total_days, lb.used_days, lb.remaining_days, lb.year
            FROM leave_balances lb
            JOIN employees e ON lb.employee_id = e.id
            WHERE e.employee_number = %s
              AND (%s::integer IS NULL OR lb.year = %s::integer);
        """

        try:
            cursor.execute(query, (employee_number, year, year))
            rows = cursor.fetchall()
            if not rows:
                logging.info(f"[INFO][employee_repository.py][get_leave_balance] No leave balances found for employee_number: {employee_number}")
                return None

            emp_uuid = str(rows[0][0])
            actual_year = rows[0][5]
            balances: List[LeaveTypeBalance] = []

            for row in rows:
                _, leave_type, total_days, used_days, remaining_days, row_year = row
                balances.append(
                    LeaveTypeBalance(
                        leave_type = leave_type,
                        total_days = float(total_days),
                        used_days = float(used_days),
                        remaining_days = float(remaining_days),
                        year = row_year
                    )
                )

            return LeaveBalanceResponse(
                employee_id = emp_uuid,
                year = actual_year,
                balances = balances
            )
        except Exception as e:
            logging.error(f"[ERROR][employee_repository.py][get_leave_balance] Database query failed. Error: {e}")
            raise e
        finally:
            cursor.close()
            conn.close()
