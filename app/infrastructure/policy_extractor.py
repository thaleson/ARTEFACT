import re
from pathlib import Path
from typing import Protocol

from app.domain.models import PolicyChunk


class PolicyExtractor(Protocol):
    def extract(self, pdf_path: Path) -> list[PolicyChunk]:
        ...


class PdfPolicyExtractor:
    def extract(self, pdf_path: Path) -> list[PolicyChunk]:
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
    normalized = re.sub(r"[ \t]+", " ", text)
    return [
        paragraph.strip()
        for paragraph in re.split(r"\n\s*\n", normalized)
        if paragraph.strip()
    ]
