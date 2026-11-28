"""Configuration flow."""
from __future__ import annotations

import re
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN, LOGGER

BRO_PREFIX_TYPES = {
    "GMN": "grondwatermonitoringnetwork (GMN)",
    "GLD": "grondwaterstandendossier (GLD)",
    "GAR": "grondwatersamenstellingsonderzoek (GAR)",
    "FRD": "formatieweerstandsonderzoek (FRD)",
    "GMW": "grondwatermonitoringsput (GMW)",
}
GMW_ID_PATTERN = re.compile(r"^GMW\\d{12}$")


def identify_bro_id(bro_id: str) -> str | None:
    """Return the descriptive type for a known BRO ID prefix."""
    return BRO_PREFIX_TYPES.get(bro_id.strip().upper()[:3])


class GroundwaterConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Configure a BRO groundwater observation dossier."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle configuration by BRO ID, accepting only valid GMW identifiers."""
        errors: dict[str, str] = {}
        bro_type_placeholder = "unknown BRO ID type"
        if user_input is not None:
            bro_id = user_input["bro_id"].strip().upper()
            bro_type = identify_bro_id(bro_id)
            bro_type_placeholder = bro_type or bro_type_placeholder
            LOGGER.debug("Validating BRO identifier %s (type=%s)", bro_id, bro_type)
            if not GMW_ID_PATTERN.fullmatch(bro_id):
                errors["bro_id"] = "not_gmw"
            else:
                await self.async_set_unique_id(bro_id)
                self._abort_if_unique_id_configured()
                LOGGER.debug("Creating config entry for GMW identifier %s", bro_id)
                return self.async_create_entry(title=bro_id, data={"bro_id": bro_id})
        schema = vol.Schema({vol.Required("bro_id"): str})
        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
            description_placeholders={
                "example": "GMW000000081887",
                "bro_type": bro_type_placeholder,
            },
        )

    async def async_step_postcode(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Show the placeholder postcode-based well-selection step."""
        if user_input is not None:
            return self.async_abort(reason="postcode_discovery_not_implemented")
        schema = vol.Schema(
            {vol.Required("postcode"): str, vol.Optional("house_number"): str}
        )
        return self.async_show_form(step_id="postcode", data_schema=schema)

    async def async_step_import(self, user_input: dict[str, Any]) -> FlowResult:
        """Handle configuration imported from YAML."""
        return await self.async_step_user(user_input)
