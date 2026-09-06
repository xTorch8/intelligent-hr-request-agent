import logging
from uuid import UUID

from ..models.retrieval_model import SearchQueryRequest
from ..services.retrieval_service import RetrievalService


def run_retrieval_test():
    logging.basicConfig(level = logging.INFO)
    retrieval_service = RetrievalService()

    sample_queries = [
        "What is the maximum duration for an annual leave request?",
        "How many days in advance should annual leave be submitted?",
        "Is medical documentation required for sick leave?",
        "POL-LEAVE-001 policy code document details"
    ]

    print("==================================================")
    print("      RAG Hybrid Search & Reranking Test         ")
    print("==================================================\n")

    for query in sample_queries:
        print(f"🔍 Query: '{query}'")
        print("-" * 60)
        request = SearchQueryRequest(query = query)
        try:
            response = retrieval_service.retrieve(request)
            print(f"Is Success: {response.is_success}")
            print(f"Message: {response.message}")
            if response.payload:
                for rank, result in enumerate(response.payload.results, start = 1):
                    section = result.metadata.section_title if result.metadata else "N/A"
                    page = result.metadata.page_number if result.metadata else "N/A"
                    print(f"  [Rank #{rank}] RerankScore={result.rerank_score} | RRF={result.rrf_score:.4f} | Vector={result.vector_score:.4f} | Text={result.text_score:.4f}")
                    print(f"             Page {page} | Section: '{section}'")
                    snippet = result.content.replace("\n", " ")[:120]
                    print(f"             Snippet: {snippet}...")
                    print()
        except Exception as e:
            print(f"  Error retrieving for query: {e}")
        print("=" * 60 + "\n")


if __name__ == "__main__":
    run_retrieval_test()
