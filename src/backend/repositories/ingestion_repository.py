import logging
from typing import List, Optional

from ..clients.postgres_client import PostgresClient
from ..models.ingestion_model import DocumentChunk

class IngestionRepository:
    def __init__(self):
        self._postgres_client = PostgresClient()

    def get_blob_url_by_policy_id(self, policy_id: str) -> Optional[str]:
        logging.info(f"[INFO][ingestion_repository.py][get_blob_url_by_policy_id] Fetching blob_url for policy_id: {policy_id}")
        conn = self._postgres_client.get_connection()
        cursor = conn.cursor()

        query = "SELECT blob_url FROM hr_policies WHERE id = %s;"
        try:
            cursor.execute(query, (str(policy_id),))
            result = cursor.fetchone()
            if result and result[0]:
                blob_url = result[0]
                return blob_url
            return None
        except Exception as e:
            logging.error(f"[ERROR][ingestion_repository.py][get_blob_url_by_policy_id] Failed to fetch blob_url for policy_id: {policy_id}. Error: {e}")
            raise e
        finally:
            cursor.close()
            conn.close()

    def save_policy_chunks(self, policy_id: str, chunks: List[DocumentChunk]) -> None:
        logging.info(f"[INFO][ingestion_repository.py][save_policy_chunks] Saving {len(chunks)} chunks for policy_id: {policy_id}")
        if not chunks:
            return

        conn = self._postgres_client.get_connection()
        cursor = conn.cursor()

        query = """
            INSERT INTO policy_chunks (policy_id, chunk_index, content, embedding, metadata)
            VALUES (%s, %s, %s, %s::vector, %s::jsonb)
            ON CONFLICT (policy_id, chunk_index) DO UPDATE SET
                content = EXCLUDED.content,
                embedding = EXCLUDED.embedding,
                metadata = EXCLUDED.metadata;
        """

        try:
            for chunk in chunks:
                embedding_str = str(chunk.embedding) if chunk.embedding else None
                metadata_json = chunk.metadata.model_dump_json()

                cursor.execute(
                    query,
                    (
                        str(policy_id),
                        chunk.metadata.chunk_index,
                        chunk.content,
                        embedding_str,
                        metadata_json
                    )
                )
            conn.commit()
            logging.info(f"[INFO][ingestion_repository.py][save_policy_chunks] Successfully saved {len(chunks)} chunk embeddings in database.")
        except Exception as e:
            conn.rollback()
            logging.error(f"[ERROR][ingestion_repository.py][save_policy_chunks] Failed to save chunks in database. Error: {e}")
            raise e
        finally:
            cursor.close()
            conn.close()

