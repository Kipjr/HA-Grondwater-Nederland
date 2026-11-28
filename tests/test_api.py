"""Tests for BRO relation lookup helpers and CSV parsing."""
from grondwater_nederland.api import (
    find_latest_gld,
    get_ground_level_position,
    parse_csv_measurements,
)


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


def test_parse_bro_observation_table_with_correct_raw_columns():
    """Parse the embedded table and preserve the actual observation headers."""
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
    latest = result["latest"]
    assert latest["time"] == "2026-04-30T04:00:26+02:00"
    assert latest["value"] == -0.846
    assert latest["raw"] == {
        "tijdstip meting": "2026-04-30T04:00:26+02:00",
        "waterstand": "-0.846",
        "status kwaliteitscontrole": "goedgekeurd",
        "censuurreden": "",
        "censuurlimietwaarde": "",
        "interpolatietype": "discontinu",
    }


def test_get_ground_level_position():
    """Read groundLevelPosition from GMW characteristics."""
    assert get_ground_level_position({"characteristics": {"groundLevelPosition": 0.42}}) == 0.42


def test_get_ground_level_position_missing():
    """Return None when the GMW has no ground level position."""
    assert get_ground_level_position({}) is None
