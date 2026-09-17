from azure.storage.blob import BlobServiceClient
from ..configs.azure_blob_config import AzureBlobConfig
import logging

class AzureBlobClient:
    def __init__(self):
        self._connection_string = AzureBlobConfig.CONNECTION_STRING

    def get_client(self):
        logging.info("[INFO][azure_blob_client.py][get_client] Attempting to create BlobServiceClient instance.")
        if not self._connection_string or not self._connection_string.strip():
            logging.error("[ERROR][azure_blob_client.py][get_client] Missing AZURE_STORAGE_CONNECTION_STRING.")
            raise ValueError("Please contact developer")
        try:
            blob_service_client = BlobServiceClient.from_connection_string(self._connection_string)
            return blob_service_client
        except Exception as e:
            logging.error(f"[ERROR][azure_blob_client.py][get_client] Failed to create BlobServiceClient: {e}")
            raise ValueError("Please contact developer") from e

    def upload_blob(self, file_bytes: bytes, filename: str, content_type: str, container_name: str) -> str:
        logging.info(f"[INFO][azure_blob_client.py][upload_blob] Uploading blob '{filename}' to container '{container_name}'.")
        blob_service_client = self.get_client()
        try:
            container_client = blob_service_client.get_container_client(container_name)
            try:
                container_client.create_container()
            except Exception:
                pass
            
            blob_client = container_client.get_blob_client(filename)
            blob_client.upload_blob(file_bytes, overwrite = True, content_type = content_type)
            return blob_client.url
        except Exception as e:
            logging.error(f"[ERROR][azure_blob_client.py][upload_blob] Failed to upload blob: {e}")
            raise ValueError("Please contact developer") from e