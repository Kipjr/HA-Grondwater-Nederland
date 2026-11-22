"""Tests for BRO ID type detection and input validation."""
from custom_components.grondwater_nederland.config_flow import identify_bro_id


def test_identify_gmw_id():
    """Recognize the GMW test well near Sterrenwacht Leiden."""
    assert identify_bro_id("GMW000000081887") == "grondwatermonitoringsput (GMW)"
