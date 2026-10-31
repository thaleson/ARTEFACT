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


def test_pdf_extractor_keeps_opening_hours_table_together() -> None:
    from app.infrastructure.policy_extractor import _paragraphs

    chunks = _paragraphs(
        "2. Horário de Funcionamento\n\n"
        "Dia Horário\n\n"
        "Segunda a Sexta-feira 09:00 às 18:00\n\n"
        "Sábado 09:00 às 13:00\n\n"
        "Domingo e Feriados Fechado\n\n"
        "Em datas especiais, o horário pode ser estendido."
    )

    assert len(chunks) == 2
    assert "09:00 às 18:00" in chunks[0]
    assert "09:00 às 13:00" in chunks[0]
    assert "Fechado" in chunks[0]


def test_pdf_extractor_keeps_delivery_table_together() -> None:
    from app.infrastructure.policy_extractor import _paragraphs

    chunks = _paragraphs(
        "Modalidade Prazo Estimado Rastreamento Seguro\n\n"
        "PAC (Correios) 5 a 12 dias úteis Sim Incluído\n\n"
        "SEDEX (Correios) 2 a 5 dias úteis Sim Incluído\n\n"
        "Jadlog (.package) 3 a 8 dias úteis Sim Incluído\n\n"
        "O valor do frete é calculado pelo CEP."
    )

    assert len(chunks) == 2
    assert "PAC (Correios)" in chunks[0]
    assert "SEDEX (Correios)" in chunks[0]
    assert "Jadlog" in chunks[0]


def test_pdf_extractor_keeps_payment_table_together() -> None:
    from app.infrastructure.policy_extractor import _paragraphs

    chunks = _paragraphs(
        "3. Formas de Pagamento\n\n"
        "Forma Condições Observações\n\n"
        "PIX Pagamento à vista 5% de desconto\n\n"
        "Cartão de Débito Pagamento à vista Todas as bandeiras\n\n"
        "Cartão de Crédito Até 12x sem juros Parcela mínima de R$ 100,00\n\n"
        "Boleto Bancário Pagamento à vista Compensação em até 3 dias úteis\n\n"
        "3.1 Regras de Parcelamento\n"
    )

    assert len(chunks) == 2
    assert "PIX" in chunks[0]
    assert "Cartão de Crédito" in chunks[0]
    assert "Boleto Bancário" in chunks[0]


def test_pdf_extractor_splits_numbered_sections_without_blank_lines() -> None:
    from app.infrastructure.policy_extractor import _paragraphs

    chunks = _paragraphs(
        "1. Sobre a loja\nTexto geral.\n"
        "1.2 Dados da Empresa\nEndereço Rua 14 de Maio, 3200.\n"
        "2. Horário de Funcionamento\n09:00 às 18:00."
    )

    assert len(chunks) == 3
    assert "Endereço Rua 14 de Maio" in chunks[1]
