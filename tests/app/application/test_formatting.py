from decimal import Decimal

from app.application.formatting import format_brl


def test_format_brl_uses_brazilian_separators() -> None:
    assert format_brl(Decimal("1234567.895")) == "R$ 1.234.567,90"
