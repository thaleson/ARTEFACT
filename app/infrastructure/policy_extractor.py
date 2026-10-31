"""Extract page-aware text chunks from the store policy PDF."""

import re
from pathlib import Path
from typing import Protocol

from app.domain.models import PolicyChunk


class PolicyExtractor(Protocol):
    """Define the PDF-to-policy-chunk extraction boundary."""

    def extract(self, pdf_path: Path) -> list[PolicyChunk]:
        """Extract policy chunks from a PDF path.

        Args:
            pdf_path (Path): Source policy PDF.

        Returns:
            list[PolicyChunk]: Page-aware extracted chunks.
        """
        ...


class PdfPolicyExtractor:
    """Use PyMuPDF to extract non-empty paragraphs with page metadata."""

    def extract(self, pdf_path: Path) -> list[PolicyChunk]:
        """Extract policy paragraphs from the supplied PDF.

        Args:
            pdf_path (Path): Source policy PDF.

        Returns:
            list[PolicyChunk]: Ordered chunks with source page numbers.

        Raises:
            RuntimeError: If PyMuPDF is not installed.
        """
        try:
            import fitz
        except ModuleNotFoundError as exc:
            raise RuntimeError(
                "PyMuPDF is required to extract the store policy PDF"
            ) from exc

        chunks: list[PolicyChunk] = []
        document = fitz.open(pdf_path)
        chunk_id = 1
        for page_index, page in enumerate(document, start=1):
            page_text = page.get_text("text")
            for paragraph in _paragraphs(page_text):
                chunks.append(
                    PolicyChunk(
                        chunk_id=chunk_id,
                        page_number=page_index,
                        content=paragraph,
                    )
                )
                chunk_id += 1
        document.close()
        return chunks


def _paragraphs(text: str) -> list[str]:
    """Split extracted page text into normalized non-empty paragraphs.

    Args:
        text (str): Raw page text.

    Returns:
        list[str]: Cleaned paragraph values.
    """
    normalized = re.sub(r"[ \t]+", " ", text)
    paragraphs = [
        paragraph.strip()
        for paragraph in re.split(r"\n\s*\n", normalized)
        if paragraph.strip()
    ]
    return _merge_table_fragments(paragraphs)


def _merge_table_fragments(paragraphs: list[str]) -> list[str]:
    """Keep schedule and delivery table rows in searchable policy chunks.

    Args:
        paragraphs (list[str]): Paragraphs extracted from one PDF page.

    Returns:
        list[str]: Paragraphs with adjacent table rows merged into their heading.
    """
    merged: list[str] = []
    index = 0
    while index < len(paragraphs):
        paragraph = paragraphs[index]
        normalized = paragraph.casefold()
        if "horário de funcionamento" in normalized:
            fragment_matcher = _is_schedule_fragment
        elif "modalidade" in normalized and "prazo estimado" in normalized:
            fragment_matcher = _is_delivery_fragment
        else:
            merged.append(paragraph)
            index += 1
            continue
        table_parts = [paragraph]
        next_index = index + 1
        while next_index < len(paragraphs) and fragment_matcher(
            paragraphs[next_index]
        ):
            table_parts.append(paragraphs[next_index])
            next_index += 1
        merged.append(" ".join(table_parts))
        index = next_index
    return merged


def _is_schedule_fragment(paragraph: str) -> bool:
    """Identify a table header or row belonging to store opening hours.

    Args:
        paragraph (str): Extracted paragraph candidate.

    Returns:
        bool: Whether the paragraph is part of the opening-hours table.
    """
    normalized = paragraph.casefold()
    return (
        normalized in {"dia horário", "dia horario"}
        or bool(re.search(r"\b\d{2}:\d{2}\b", paragraph))
        or "fechado" in normalized
    )


def _is_delivery_fragment(paragraph: str) -> bool:
    """Identify a row belonging to the delivery-method table.

    Args:
        paragraph (str): Extracted paragraph candidate.

    Returns:
        bool: Whether the paragraph is part of the delivery table.
    """
    normalized = paragraph.casefold()
    return (
        normalized.startswith(("pac ", "sedex ", "jadlog "))
        or "dias úteis" in normalized
    )
