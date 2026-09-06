from langchain_core.tools import tool
from typing import Optional

from ..models.retrieval_model import SearchQueryRequest
from ..services.retrieval_service import RetrievalService

@tool("search_hr_policies")
def search_hr_policies(query: str, policy_id: Optional[str] = None) -> str:
    """
    Use this tool to retrieve relevant HR policy sections based on the user's query and optional policy ID.
    """
    retrieval_service = RetrievalService()
    request = SearchQueryRequest(
        query = query,
        policy_id = policy_id
    )

    response = retrieval_service.retrieve(request)
    if not response.payload or not response.payload.results:
        return "No relevant HR policy sections found for the query."

    formatted_chunks = []
    for i, res in enumerate(response.payload.results, start = 1):
        section = res.metadata.section_title if res.metadata else "N/A"
        page = res.metadata.page_number if res.metadata else "N/A"
        formatted_chunks.append(
            f"--- Result #{i} (Page {page} | Section: {section}) ---\n{res.content}"
        )

    return "\n\n".join(formatted_chunks)
