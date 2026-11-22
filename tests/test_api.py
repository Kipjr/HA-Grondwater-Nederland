"""Tests for the BRO API parsing helpers."""
from custom_components.grondwater_nederland.api import parse_csv_measurements


def test_parse_csv_measurements():
    """Parse rows and identify the most recent measurement."""
    result = parse_csv_measurements(
        "time,value\\n2024-01-01,12.3\\n2024-01-02,13.2\\n"
    )
    assert result["count"] == 2
    assert result["latest"]["value"] == 13.2
    assert result["latest"]["time"] == "2024-01-02"


def test_parse_csv_empty_or_unrecognized():
    """Return an empty result for empty or unrecognized data."""
    assert parse_csv_measurements("")["latest"] is None
    assert parse_csv_measurements("x,y\\nfoo,bar\\n")["count"] == 0


def test_parse_csv_decimal_comma():
    """Ignore malformed CSV rows instead of raising parsing errors."""
    result = parse_csv_measurements("datum,waarde\\n2024-01-01,1,2\\n")
    assert result["count"] == 0
