from dotenv import load_dotenv
import os

load_dotenv()

class RetrievalConfig:
    TOP_K = int(os.getenv("RETRIEVAL_TOP_K", "5"))
    FETCH_K = int(os.getenv("RETRIEVAL_FETCH_K", "20"))

