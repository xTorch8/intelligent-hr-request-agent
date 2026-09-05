from io import BytesIO
import logging
import re
from typing import List, Optional, Tuple
import uuid

from langchain_text_splitters import RecursiveCharacterTextSplitter
import pymupdf

from ..clients.azure_blob_client import AzureBlobClient
from ..configs.azure_blob_config import AzureBlobConfig
from ..models.ingestion_model import (
    ChunkMetadata,
    DocumentChunk,
    DocumentElement,
    DocumentMetadata,
    ElementType,
    IngestDocumentRequest,
    ParsedDocument,
    ParsedPage,
    TableElement
)


class IngestionService:
    def __init__(self):
        self._azure_blob_client = AzureBlobClient().get_client()
        self._azure_blob_container_name = AzureBlobConfig.CONTAINER_NAME

        self._chunk_size = 2000
        self._chunk_overlap = 200

    def ingest_document(self, request: IngestDocumentRequest) -> List[DocumentChunk]:
        logging.info(f"[INFO][ingestion_service.py][ingest_document] Attempting to ingest document from blob: {request.blob_name}")
        try:
            file = self._read_file_from_blob(request.blob_name)
            parsed_document = self._parse_pdf(file, request.blob_name)
            chunks = self._create_chunks(parsed_document)
            return chunks
        except Exception as e:
            logging.error(f"[ERROR][ingestion_service.py][ingest_document] Failed to ingest document from blob: {request.blob_name}. Error: {e}")
            raise e

    #region Chunking
    def _create_chunks(self, parsed_doc: ParsedDocument) -> List[DocumentChunk]:
        logging.info("[INFO][ingestion_service.py][_create_chunks] Creating section-grouped semantic chunks.")
        chunks: List[DocumentChunk] = []

        blob_name = parsed_doc.metadata.blob_name
        file_name = parsed_doc.metadata.file_name

        current_major_section = "Overview"
        active_section = "Overview"

        current_buffer: List[str] = []
        current_buffer_length = 0
        current_page_number = 1
        has_table = False
        chunk_index = 0

        for page in parsed_doc.pages:
            current_page_number = page.page_number
            for elem in page.elements:
                text_content = elem.text.strip()
                if not text_content:
                    continue

                if self._is_header_or_footer(text_content):
                    continue

                if elem.type == ElementType.HEADING:
                    formatted_heading, is_major, section_name = self._format_heading_markdown(text_content)

                    if is_major and current_buffer and current_major_section != section_name:
                        chunk, current_buffer, current_buffer_length = self._flush_buffer(
                            buffer = current_buffer,
                            file_name = file_name,
                            blob_name = blob_name,
                            page_number = current_page_number,
                            section_title = active_section,
                            chunk_index = chunk_index,
                            has_table = has_table
                        )
                        if chunk:
                            chunks.append(chunk)
                            chunk_index = chunk_index + 1
                        has_table = False
                        current_major_section = section_name

                    active_section = section_name
                    current_buffer.append(formatted_heading)
                    current_buffer_length = current_buffer_length + len(formatted_heading)

                elif elem.type == ElementType.TABLE:
                    has_table = True
                    current_buffer.append(text_content)
                    current_buffer_length = current_buffer_length + len(text_content)

                else:
                    current_buffer.append(text_content)
                    current_buffer_length = current_buffer_length + len(text_content)

                if current_buffer_length >= self._chunk_size:
                    chunk, current_buffer, current_buffer_length = self._flush_buffer(
                        buffer = current_buffer,
                        file_name = file_name,
                        blob_name = blob_name,
                        page_number = current_page_number,
                        section_title = active_section,
                        chunk_index = chunk_index,
                        has_table = has_table
                    )
                    if chunk:
                        chunks.append(chunk)
                        chunk_index = chunk_index + 1
                    has_table = False

        if current_buffer:
            chunk, current_buffer, current_buffer_length = self._flush_buffer(
                buffer = current_buffer,
                file_name = file_name,
                blob_name = blob_name,
                page_number = current_page_number,
                section_title = active_section,
                chunk_index = chunk_index,
                has_table = has_table
            )
            if chunk:
                chunks.append(chunk)
                chunk_index = chunk_index + 1

        total_count = len(chunks)
        for chunk in chunks:
            chunk.metadata.total_chunks = total_count

        return chunks

    def _flush_buffer(self, buffer: List[str], file_name: str, blob_name: str, page_number: int, section_title: str, chunk_index: int, has_table: bool = False) -> Tuple[Optional[DocumentChunk], List[str], int]:
        if not buffer:
            return None, [], 0

        raw_text = "\n\n".join(buffer).strip()
        if not raw_text:
            return None, [], 0

        prefix = f"[Document: {file_name} | Page: {page_number} | Section: {section_title}]"
        contextualized_content = f"{prefix}\n\n{raw_text}"
        token_est = len(contextualized_content) // 4

        chunk_id = f"{file_name}_chunk_{chunk_index}"
        metadata = ChunkMetadata(
            blob_name = blob_name,
            file_name = file_name,
            page_number = page_number,
            section_title = section_title,
            chunk_index = chunk_index,
            char_count = len(contextualized_content),
            token_estimate = token_est,
            has_table = has_table
        )

        chunk = DocumentChunk(
            chunk_id = chunk_id,
            content = contextualized_content,
            raw_content = raw_text,
            metadata = metadata
        )

        new_buffer: List[str] = []
        new_buffer_length = 0

        return chunk, new_buffer, new_buffer_length

    def _format_heading_markdown(self, heading_text: str) -> Tuple[str, bool, str]:
        cleaned = heading_text.strip()

        major_match = re.match(r"^(\d+)\.\s+(.+)$", cleaned)
        if major_match:
            formatted = f"# {cleaned}"
            return formatted, True, cleaned

        sub_match = re.match(r"^(\d+\.\d+)\s+(.+)$", cleaned)
        if sub_match:
            formatted = f"## {cleaned}"
            return formatted, False, cleaned

        formatted = f"# {cleaned}"
        return formatted, True, cleaned

    def _is_header_or_footer(self, text: str) -> bool:
        cleaned = text.strip()
        if re.match(r"^POL-LEAVE-\d+\s*\|\s*Version\s*[\d\.]+\s*Page\s*\d+$", cleaned, re.IGNORECASE):
            return True
        if re.match(r"^Page\s*\d+$", cleaned, re.IGNORECASE):
            return True
        return False
    #endregion

    #region Document Parsing
    def _parse_pdf(self, file: BytesIO, blob_name: str) -> ParsedDocument:
        logging.info("[INFO][ingestion_service.py][_parse_pdf] Attempting to parse PDF file.")
        try:
            pdf = pymupdf.open(stream = file, filetype = "pdf")

            metadata = self._extract_metadata(pdf, blob_name)
            pages: List[ParsedPage] = []

            for page_idx in range(len(pdf)):
                page = pdf.load_page(page_idx)
                page_number = page_idx + 1

                parsed_page = self._parse_page(page, page_number)
                pages.append(parsed_page)

            pdf.close()

            parsed_doc = ParsedDocument(
                metadata = metadata,
                pages = pages
            )
            return parsed_doc
        except Exception as e:
            logging.error(f"[ERROR][ingestion_service.py][_parse_pdf] Failed to parse PDF file. Error: {e}")
            raise e

    def _classify_element_type(self, text: str, font_size: float, is_bold: bool) -> ElementType:
        stripped = text.strip()
        if font_size >= 13.0 or (is_bold and len(stripped) < 100):
            return ElementType.HEADING

        list_prefixes = ("- ", "* ", "• ", "1. ", "2. ", "3. ", "4. ", "5. ")
        if stripped.startswith(list_prefixes):
            return ElementType.LIST_ITEM

        return ElementType.PARAGRAPH

    def _extract_elements(self, page: pymupdf.Page, page_number: int, tables: List[TableElement] = []) -> List[DocumentElement]:
        elements: List[DocumentElement] = []
        text_page = page.get_text("dict")
        blocks = text_page.get("blocks", [])

        for block in blocks:
            if block.get("type") != 0:
                continue

            bbox = [float(c) for c in block.get("bbox", [])]
            if self._is_bbox_inside_tables(bbox, tables):
                continue

            block_text = ""
            max_font_size = 0.0
            is_bold = False

            for line in block.get("lines", []):
                line_text = ""
                for span in line.get("spans", []):
                    span_text = span.get("text", "")
                    line_text = line_text + span_text
                    font_size = float(span.get("size", 0.0))
                    if font_size > max_font_size:
                        max_font_size = font_size
                    flags = span.get("flags", 0)
                    if flags & 2 or "bold" in str(span.get("font", "")).lower():
                        is_bold = True
                block_text = block_text + line_text.strip() + "\n"

            cleaned_text = block_text.strip()
            if not cleaned_text:
                continue

            element_type = self._classify_element_type(cleaned_text, max_font_size, is_bold)

            element = DocumentElement(
                page_number = page_number,
                type = element_type,
                text = cleaned_text,
                font_size = max_font_size,
                is_bold = is_bold,
                bbox = bbox
            )
            elements.append(element)

        return elements

    def _extract_metadata(self, pdf: pymupdf.Document, blob_name: str) -> DocumentMetadata:
        logging.info("[INFO][ingestion_service.py][_extract_metadata] Extracting metadata from PDF.")
        pdf_metadata = pdf.metadata or {}
        file_name = blob_name.split("/")[-1] if "/" in blob_name else blob_name

        metadata = DocumentMetadata(
            blob_name = blob_name,
            file_name = file_name,
            total_pages = len(pdf),
            title = pdf_metadata.get("title"),
            author = pdf_metadata.get("author"),
            creation_date = pdf_metadata.get("creationDate"),
            format = pdf_metadata.get("format")
        )
        return metadata

    def _extract_tables(self, page: pymupdf.Page, page_number: int) -> List[TableElement]:
        tables: List[TableElement] = []
        try:
            found_tables = page.find_tables()
            if found_tables:
                for tab in found_tables:
                    raw_data = tab.extract()
                    if not raw_data:
                        continue
                    headers = [str(cell or "").strip() for cell in raw_data[0]] if len(raw_data) > 0 else []
                    rows = [[str(cell or "").strip() for cell in row] for row in raw_data[1:]] if len(raw_data) > 1 else []
                    bbox = [float(coord) for coord in tab.bbox] if hasattr(tab, "bbox") else None

                    table_element = TableElement(
                        page_number = page_number,
                        row_count = len(raw_data),
                        col_count = len(headers),
                        headers = headers,
                        rows = rows,
                        bbox = bbox
                    )
                    tables.append(table_element)
        except Exception as e:
            logging.warning(f"[WARNING][ingestion_service.py][_extract_tables] Failed table extraction on page {page_number}. Error: {e}")

        return tables

    def _format_table_as_markdown(self, headers: List[str], rows: List[List[str]]) -> str:
        lines: List[str] = []
        if headers:
            lines.append("| " + " | ".join(headers) + " |")
            lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
        for row in rows:
            lines.append("| " + " | ".join(row) + " |")
        return "\n".join(lines)

    def _is_bbox_inside_tables(self, bbox: List[float], tables: List[TableElement]) -> bool:
        if not bbox or len(bbox) < 4 or not tables:
            return False

        bx0, by0, bx1, by1 = bbox
        cx = (bx0 + bx1) / 2.0
        cy = (by0 + by1) / 2.0

        for table in tables:
            if not table.bbox or len(table.bbox) < 4:
                continue
            tx0, ty0, tx1, ty1 = table.bbox
            if tx0 <= cx <= tx1 and ty0 <= cy <= ty1:
                return True

        return False

    def _parse_page(self, page: pymupdf.Page, page_number: int) -> ParsedPage:
        rect = page.rect
        width = float(rect.width)
        height = float(rect.height)

        tables = self._extract_tables(page, page_number)
        text_elements = self._extract_elements(page, page_number, tables = tables)

        all_elements: List[DocumentElement] = list(text_elements)

        for table in tables:
            table_md = self._format_table_as_markdown(table.headers, table.rows)
            table_doc_element = DocumentElement(
                page_number = page_number,
                type = ElementType.TABLE,
                text = table_md,
                bbox = table.bbox,
                table_data = table
            )
            all_elements.append(table_doc_element)

        # Sort elements sequentially by vertical reading order (y0 position on page)
        all_elements.sort(key = lambda elem: elem.bbox[1] if elem.bbox and len(elem.bbox) >= 2 else 0.0)

        parsed_page = ParsedPage(
            page_number = page_number,
            width = width,
            height = height,
            elements = all_elements,
            tables = tables
        )
        return parsed_page
    #endregion

    def _read_file_from_blob(self, blob_name: str) -> BytesIO:
        logging.info(f"[INFO][ingestion_service.py][_read_file_from_blob] Attempting to read file from blob: {blob_name}")
        try:
            blob_client = self._azure_blob_client.get_blob_client(
                container = self._azure_blob_container_name,
                blob = blob_name
            )

            blob_data = blob_client.download_blob().readall()
            return BytesIO(blob_data)
        except Exception as e:
            logging.error(f"[ERROR][ingestion_service.py][_read_file_from_blob] Failed to read file from blob: {blob_name}. Error: {e}")
            raise e