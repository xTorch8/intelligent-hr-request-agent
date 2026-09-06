import json
import logging
from typing import List, Optional

from ..clients.postgres_client import PostgresClient
from ..models.ingestion_model import ChunkMetadata
from ..models.retrieval_model import SearchResultChunk


class RetrievalRepository:
    def __init__(self):
        self._postgres_client = PostgresClient()

    def search_dense_vector(self, query_embedding: List[float], fetch_k: int, policy_id: Optional[str] = None) -> List[SearchResultChunk]:
        logging.info(f"[INFO][retrieval_repository.py][search_dense_vector] Executing dense vector search (fetch_k={fetch_k}).")
        conn = self._postgres_client.get_connection()
        cursor = conn.cursor()

        query = """
            SELECT id, policy_id, chunk_index, content, metadata,
                   1 - (embedding <=> %s::vector) AS vector_score
            FROM policy_chunks
            WHERE (%s::uuid IS NULL OR policy_id = %s::uuid)
            ORDER BY embedding <=> %s::vector
            LIMIT %s;
        """

        results: List[SearchResultChunk] = []
        try:
            embedding_str = str(query_embedding)
            policy_id_str = str(policy_id) if policy_id else None

            cursor.execute(
                query,
                (embedding_str, policy_id_str, policy_id_str, embedding_str, fetch_k)
            )
            rows = cursor.fetchall()

            for row in rows:
                chunk_uuid, pid, idx, content, meta_data, score = row
                parsed_meta = ChunkMetadata(**meta_data) if isinstance(meta_data, dict) else ChunkMetadata(**json.loads(meta_data))

                chunk = SearchResultChunk(
                    chunk_id = str(chunk_uuid),
                    policy_id = str(pid),
                    chunk_index = idx,
                    content = content,
                    vector_score = float(score) if score is not None else 0.0,
                    metadata = parsed_meta
                )
                results.append(chunk)

            return results
        except Exception as e:
            logging.error(f"[ERROR][retrieval_repository.py][search_dense_vector] Dense vector search failed. Error: {e}")
            raise e
        finally:
            cursor.close()
            conn.close()

    def search_sparse_text(self, query_text: str, fetch_k: int, policy_id: Optional[str] = None) -> List[SearchResultChunk]:
        logging.info(f"[INFO][retrieval_repository.py][search_sparse_text] Executing sparse full-text search for query: '{query_text}' (fetch_k={fetch_k}).")
        conn = self._postgres_client.get_connection()
        cursor = conn.cursor()

        query = """
            SELECT id, policy_id, chunk_index, content, metadata,
                   ts_rank_cd(to_tsvector('english', content), plainto_tsquery('english', %s)) AS text_score
            FROM policy_chunks
            WHERE (%s::uuid IS NULL OR policy_id = %s::uuid)
              AND to_tsvector('english', content) @@ plainto_tsquery('english', %s)
            ORDER BY text_score DESC
            LIMIT %s;
        """

        results: List[SearchResultChunk] = []
        try:
            policy_id_str = str(policy_id) if policy_id else None

            cursor.execute(
                query,
                (query_text, policy_id_str, policy_id_str, query_text, fetch_k)
            )
            rows = cursor.fetchall()

            for row in rows:
                chunk_uuid, pid, idx, content, meta_data, score = row
                parsed_meta = ChunkMetadata(**meta_data) if isinstance(meta_data, dict) else ChunkMetadata(**json.loads(meta_data))

                chunk = SearchResultChunk(
                    chunk_id = str(chunk_uuid),
                    policy_id = str(pid),
                    chunk_index = idx,
                    content = content,
                    text_score = float(score) if score is not None else 0.0,
                    metadata = parsed_meta
                )
                results.append(chunk)

            return results
        except Exception as e:
            logging.error(f"[ERROR][retrieval_repository.py][search_sparse_text] Sparse text search failed. Error: {e}")
            raise e
        finally:
            cursor.close()
            conn.close()

