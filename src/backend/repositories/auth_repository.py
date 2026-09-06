import logging
from typing import Dict, Optional

from ..clients.postgres_client import PostgresClient

class AuthRepository:
    def __init__(self):
        self._postgres_client = PostgresClient()

    def get_user_by_email(self, email: str) -> Optional[Dict[str, str]]:
        logging.info(f"[INFO][auth_repository.py][get_user_by_email] Querying user for email: {email}")
        conn = self._postgres_client.get_connection()
        cursor = conn.cursor()

        query = """
            SELECT u.id, u.employee_id, e.employee_number, u.email, u.password_hash, u.role, e.first_name, e.last_name
            FROM users u
            JOIN employees e ON u.employee_id = e.id
            WHERE LOWER(u.email) = LOWER(%s);
        """

        try:
            cursor.execute(query, (email,))
            row = cursor.fetchone()
            if not row:
                return None

            u_id, emp_id, emp_num, u_email, pwd_hash, u_role, f_name, l_name = row
            return {
                "user_id": str(u_id),
                "employee_id": str(emp_id),
                "employee_number": emp_num,
                "email": u_email,
                "password_hash": pwd_hash,
                "role": u_role,
                "first_name": f_name,
                "last_name": l_name
            }
        except Exception as e:
            logging.error(f"[ERROR][auth_repository.py][get_user_by_email] Query failed. Error: {e}")
            raise e
        finally:
            cursor.close()
            conn.close()

    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, str]]:
        logging.info(f"[INFO][auth_repository.py][get_user_by_id] Querying user for user_id: {user_id}")
        conn = self._postgres_client.get_connection()
        cursor = conn.cursor()

        query = """
            SELECT u.id, u.employee_id, e.employee_number, u.email, u.password_hash, u.role, e.first_name, e.last_name
            FROM users u
            JOIN employees e ON u.employee_id = e.id
            WHERE u.id = %s::uuid;
        """

        try:
            cursor.execute(query, (user_id,))
            row = cursor.fetchone()
            if not row:
                return None

            u_id, emp_id, emp_num, u_email, pwd_hash, u_role, f_name, l_name = row
            return {
                "user_id": str(u_id),
                "employee_id": str(emp_id),
                "employee_number": emp_num,
                "email": u_email,
                "password_hash": pwd_hash,
                "role": u_role,
                "first_name": f_name,
                "last_name": l_name
            }
        except Exception as e:
            logging.error(f"[ERROR][auth_repository.py][get_user_by_id] Query failed. Error: {e}")
            raise e
        finally:
            cursor.close()
            conn.close()

