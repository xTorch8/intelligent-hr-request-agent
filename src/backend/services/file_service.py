import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, Optional
from azure.storage.blob import generate_blob_sas, BlobSasPermissions

from ..clients.azure_blob_client import AzureBlobClient
from ..models.api_model import APIResponseModel


class FileService:
    def __init__(self, azure_blob_client: Optional[AzureBlobClient] = None):
        self._azure_blob_client = azure_blob_client if azure_blob_client else AzureBlobClient()

    def upload_file(self, file_bytes: bytes, original_filename: str, content_type: str) -> APIResponseModel[Optional[Dict[str, str]]]:
        logging.info(f"[INFO][file_service.py][upload_file] Processing file upload for '{original_filename}'")
        try:
            unique_filename = f"{uuid.uuid4().hex}_{original_filename}"
            blob_service_client = self._azure_blob_client.get_client()
            container_client = blob_service_client.get_container_client("uploads")
            try:
                container_client.create_container()
            except Exception:
                pass

            blob_client = container_client.get_blob_client(unique_filename)
            blob_client.upload_blob(file_bytes, overwrite = True, content_type = content_type or "application/octet-stream")
            
            blob_url = blob_client.url
            try:
                account_name = blob_service_client.account_name
                account_key = getattr(blob_service_client.credential, "account_key", None)
                if account_name and account_key:
                    sas_token = generate_blob_sas(
                        account_name = account_name,
                        container_name = "uploads",
                        blob_name = unique_filename,
                        account_key = account_key,
                        permission = BlobSasPermissions(read = True),
                        expiry = datetime.utcnow() + timedelta(days = 365)
                    )
                    blob_url = f"{blob_client.url}?{sas_token}"
            except Exception as sas_err:
                logging.warning(f"[WARN][file_service.py] SAS generation skipped: {sas_err}")

            return APIResponseModel[Optional[Dict[str, str]]](
                is_success = True,
                status_code = 200,
                message = "File uploaded successfully to Azure Blob Storage",
                payload = {
                    "blob_url": blob_url,
                    "filename": unique_filename,
                    "original_filename": original_filename
                }
            )
        except Exception as e:
            logging.error(f"[ERROR][file_service.py][upload_file] Failed to upload file. Error: {e}")
            error_msg = str(e) if "Please contact developer" in str(e) else "Please contact developer"
            return APIResponseModel[Optional[Dict[str, str]]](
                is_success = False,
                error = error_msg,
                status_code = 500,
                message = error_msg,
                payload = None
            )

