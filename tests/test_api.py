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
    """Parse timestamp and water-level values from observation rows."""
    content = (
        "BRO-ID,bronhouder,,kwaliteitsregime,datum eerste meting,datum recentste meting\\n"
        "observatie ID,start observatieperiode,eind observatieperiode,observatietype,mate beoordeling,observatieproces ID\\n"
        "_03b4c70d,(2026-04-30, JJJJ-MM-DD),(2026-05-01, JJJJ-MM-DD),reguliereMeting,voorlopig,_4b4d\\n"
        "tijdstip meting,waterstand,status kwaliteitscontrole,censuurreden,censuurlimietwaarde,interpolatietype\\n"
        "2026-04-30T02:00:26+02:00,-0.851,goedgekeurd,,,discontinu\\n"
        "2026-04-30T03:00:26+02:00,-0.851,goedgekeurd,,,discontinu\\n"
        "2026-04-30T04:00:26+02:00,-0.846,goedgekeurd,,,discontinu\\n"
    )
    result = parse_csv_measurements(content)
    assert result["count"] == 3
    assert result["measurements"][0]["time"] == "2026-04-30T02:00:26+02:00"
    assert result["measurements"][0]["value"] == -0.851
    assert result["latest"]["value"] == -0.846


def test_parse_csv_skips_metadata_rows():
    """Ignore embedded CSV headers, metadata and invalid rows."""
    content = (
        "BRO-ID,bronhouder,,kwaliteitsregime,datum eerste meting,datum recentste meting\\n"
        "tijdstip meting,waterstand,status kwaliteitscontrole,censuurreden,censuurlimietwaarde,interpolatietype\\n"
        "observatie ID,start observatieperiode,eind observatieperiode,observatietype,mate beoordeling,observatieproces ID\\n"
        "2026-04-30T03:00:26+02:00,-0.851,goedgekeurd,,,discontinu\\n"
        "invalid,not-a-number,,,,\\n"
    )
    result = parse_csv_measurements(content)
    assert result["count"] == 1
    assert result["latest"]["value"] == -0.851
