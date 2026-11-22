"""Configuration flow."""
from __future__ import annotations

import re
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN

class GroundwaterConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Configure a BRO groundwater observation dossier."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        if user_input is not None:
            bro_id = user_input["bro_id"].strip().upper()
            await self.async_set_unique_id(bro_id)
            self._abort_if_unique_id_configured()
            return self.async_create_entry(title=bro_id, data={"bro_id": bro_id})
        schema = vol.Schema({vol.Required("bro_id"): str})
        return self.async_show_form(step_id="user", data_schema=schema, description_placeholders={"example": "GLD000000000000"})

    async def async_step_postcode(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Placeholder step kept for the planned postcode-to-well selection flow."""
        if user_input is not None:
            return self.async_abort(reason="postcode_discovery_not_implemented")
        return self.async_show_form(step_id="postcode", data_schema=vol.Schema({vol.Required("postcode"): str, vol.Optional("house_number"): str}))

    async def async_step_import(self, user_input: dict[str, Any]) -> FlowResult:
        return await self.async_step_user(user_input)
