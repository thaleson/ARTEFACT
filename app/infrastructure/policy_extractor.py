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
    return [
        paragraph.strip()
        for paragraph in re.split(r"\n\s*\n", normalized)
        if paragraph.strip()
    ]
