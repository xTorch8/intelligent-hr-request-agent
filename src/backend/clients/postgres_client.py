import logging
import psycopg2

from ..configs.postgres_config import PostgresConfig

class PostgresClient:
    def __init__(self):
        self._host = PostgresConfig.HOST
        self._port = PostgresConfig.PORT
        self._user = PostgresConfig.USER
        self._password = PostgresConfig.PASSWORD
        self._dbname = PostgresConfig.DBNAME

    def get_connection(self):
        logging.info("[INFO][postgres_client.py][get_connection] Connecting to PostgreSQL database.")
        try:
            conn = psycopg2.connect(
                host = self._host,
                port = self._port,
                user = self._user,
                password = self._password,
                dbname = self._dbname
            )

            return conn
        except Exception as e:
            logging.error(f"[ERROR][postgres_client.py][get_connection] Failed to connect to PostgreSQL database. Error: {e}")
            raise e

