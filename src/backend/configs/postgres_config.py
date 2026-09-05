from dotenv import load_dotenv
import os

load_dotenv()

class PostgresConfig:
    HOST = os.getenv("POSTGRES_HOST")
    PORT = int(os.getenv("POSTGRES_PORT"))
    USER = os.getenv("POSTGRES_USER")
    PASSWORD = os.getenv("POSTGRES_PASSWORD")
    DBNAME = os.getenv("POSTGRES_DB")

