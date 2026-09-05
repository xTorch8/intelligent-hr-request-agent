import logging
from openai import OpenAI

from ..configs.openai_config import OpenAIConfig

class OpenAIClient:
    def __init__(self):
        self._api_key = OpenAIConfig.API_KEY

    def get_client(self) -> OpenAI:
        logging.info("[INFO][openai_client.py][get_client] Creating OpenAI client instance.")
        try:
            client = OpenAI(api_key = self._api_key)
            return client
        except Exception as e:
            logging.error(f"[ERROR][openai_client.py][get_client] Failed to create OpenAI client instance. Error: {e}")
            raise e

