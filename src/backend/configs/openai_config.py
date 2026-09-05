from dotenv import load_dotenv
import os

load_dotenv()

class OpenAIConfig:
    API_KEY = os.getenv("OPENAI_API_KEY")
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL")

