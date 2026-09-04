from azure.storage.blob import BlobServiceClient
from ..configs.azure_blob_config import AzureBlobConfig
import logging

class AzureBlobClient:
    def __init__(self):
        self._connection_string = AzureBlobConfig.CONNECTION_STRING

    def get_client(self):
        logging.info("[INFO][azure_blob_client.py][get_client] Attempting to create BlobServiceClient instance.")
        try:
            blob_service_client = BlobServiceClient.from_connection_string(self._connection_string)
            return blob_service_client
        except Exception as e:
            logging.error("[ERROR][azure_blob_client.py][get_client] Failed to create BlobServiceClient instance.")
            raise e