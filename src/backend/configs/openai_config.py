from dotenv import load_dotenv
import os

load_dotenv()

class OpenAIConfig:
    API_KEY = os.getenv("OPENAI_API_KEY")
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL")
    OPENAI_SMALL_MODEL = os.getenv("OPENAI_SMALL_MODEL")
    OPENAI_MEDIUM_MODEL = os.getenv("OPENAI_MEDIUM_MODEL")
    OPENAI_LARGE_MODEL = os.getenv("OPENAI_LARGE_MODEL")
