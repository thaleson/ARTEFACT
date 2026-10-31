import sys
from pathlib import Path

import pytest

from app.infrastructure.policy_extractor import PdfPolicyExtractor


class FakePage:
    def get_text(self, mode: str) -> str:
        assert mode == "text"
        return "Heading\n\nPolicy paragraph"


class FakeDocument:
    def __iter__(self):
        return iter([FakePage()])

    def close(self) -> None:
        pass


class FakeFitz:
    @staticmethod
    def open(pdf_path: Path) -> FakeDocument:
        return FakeDocument()


def test_pdf_extractor_creates_page_aware_chunks(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(sys.modules, "fitz", FakeFitz())

    chunks = PdfPolicyExtractor().extract(Path("policy.pdf"))

    assert [(chunk.page_number, chunk.content) for chunk in chunks] == [
        (1, "Heading"),
        (1, "Policy paragraph"),
    ]


def test_pdf_extractor_reports_missing_dependency(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(sys.modules, "fitz", None)

    with pytest.raises(RuntimeError, match="PyMuPDF"):
        PdfPolicyExtractor().extract(Path("policy.pdf"))
