"""Tests for BRO ID type detection and input validation."""
from custom_components.grondwater_nederland.config_flow import identify_bro_id


def test_identify_gmw_id():
    """Recognize the GMW test well near Sterrenwacht Leiden."""
    assert identify_bro_id("GMW000000081887") == "grondwatermonitoringsput (GMW)"


def test_identify_other_bro_types():
    """Recognize non-GMW BRO ID types for user feedback."""
    assert identify_bro_id("GMN000000000000") == "grondwatermonitoringnetwork (GMN)"
    assert identify_bro_id("GLD000000000000") == "grondwaterstandendossier (GLD)"
    assert identify_bro_id("GAR000000000000") == "grondwatersamenstellingsonderzoek (GAR)"
    assert identify_bro_id("FRD000000000000") == "formatieweerstandsonderzoek (FRD)"


def test_unknown_prefix():
    """Return None for unknown prefixes."""
    assert identify_bro_id("XYZ000000000000") is None
