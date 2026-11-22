"""BRO groundwater monitor integration."""
from __future__ import annotations

from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import BroApi
from .const import DOMAIN, LOGGER, UPDATE_INTERVAL

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    api = BroApi(hass)
    async def update_data():
        try:
            return await api.async_get_measurements(entry.data["bro_id"])
        except Exception as err:  # noqa: BLE001
            raise UpdateFailed(f"BRO request failed: {err}") from err
    coordinator = DataUpdateCoordinator(hass, LOGGER, name=entry.title, update_method=update_data, update_interval=timedelta(hours=24))
    await coordinator.async_config_entry_first_refresh()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, ["sensor"])
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    if not await hass.config_entries.async_unload_platforms(entry, ["sensor"]):
        return False
    hass.data[DOMAIN].pop(entry.entry_id, None)
    return True
