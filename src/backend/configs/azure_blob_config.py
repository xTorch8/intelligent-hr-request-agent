from dotenv import load_dotenv
import os

load_dotenv()

class AzureBlobConfig:
    CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
    CONTAINER_NAME = os.getenv("AZURE_STORAGE_CONTAINER_NAME")