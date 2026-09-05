from enum import Enum
from pydantic import BaseModel
from typing import List, Optional

#region Document Parsing
class ElementType(str, Enum):
    HEADING = "heading"
    PARAGRAPH = "paragraph"
    LIST_ITEM = "list_item"
    TABLE = "table"
    UNKNOWN = "unknown"

class DocumentMetadata(BaseModel):
    blob_name: str
    file_name: str
    total_pages: int
    title: Optional[str] = None
    author: Optional[str] = None
    creation_date: Optional[str] = None
    format: Optional[str] = None

class TableElement(BaseModel):
    page_number: int
    row_count: int
    col_count: int
    headers: List[str] = []
    rows: List[List[str]] = []
    bbox: Optional[List[float]] = None

class DocumentElement(BaseModel):
    page_number: int
    type: ElementType
    text: str
    font_size: Optional[float] = None
    is_bold: Optional[bool] = False
    bbox: Optional[List[float]] = None
    table_data: Optional[TableElement] = None

class ParsedPage(BaseModel):
    page_number: int
    width: float
    height: float
    elements: List[DocumentElement] = []
    tables: List[TableElement] = []

class ParsedDocument(BaseModel):
    metadata: DocumentMetadata
    pages: List[ParsedPage]

    def __len__(self) -> int:
        return len(self.pages)
#endregion

class IngestDocumentRequest(BaseModel):
    blob_name: str
