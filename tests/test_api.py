"""Tests for BRO relation lookup helpers and CSV parsing."""
from custom_components.grondwater_nederland.api import find_latest_gld, parse_csv_measurements


def test_find_latest_gld_and_gmn_name():
    """Select the most recent GLD relation and associated GMN name."""
    payload = {
        "monitoringTubeReferences": [{
            "tubeNumber": 1,
            "gmnReferences": [{"characteristics": {"name": "Leiden grondwatermeetnet"}}],
            "gldReferences": [
                {"broId": "GLD000000000001", "characteristics": {"researchLastDate": "2024-02-01"}},
                {"broId": "GLD000000000002", "characteristics": {"researchLastDate": "2025-02-01"}},
            ],
        }]
    }
    assert find_latest_gld(payload) == ("GLD000000000002", "Leiden grondwatermeetnet", 1)


def test_no_gld_relation():
    """Return no dossier when the GMW has no linked GLD entries."""
    assert find_latest_gld({"monitoringTubeReferences": []}) == (None, None, None)


def test_parse_csv_measurements():
    """Parse rows and identify the latest measurement."""
    result = parse_csv_measurements("time,value\\n2024-01-01,12.3\\n2024-01-02,13.2\\n")
    assert result["count"] == 2
    assert result["latest"]["value"] == 13.2
