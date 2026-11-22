"""BRO groundwater monitor integration."""
from __future__ import annotations

from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import BroApi
from .const import DOMAIN, LOGGER


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up the configured BRO integration entry."""
    bro_id = entry.data["bro_id"]
    LOGGER.debug("Setting up integration for GMW ID %s", bro_id)
    api = BroApi(hass)

    async def update_data():
        """Fetch updated measurements from BRO."""
        LOGGER.debug("Coordinator refresh started for %s", bro_id)
        try:
            data = await api.async_get_measurements(bro_id)
            LOGGER.debug("Coordinator refresh succeeded for %s: %s records", bro_id, data.get("count", 0))
            return data
        except Exception as err:  # noqa: BLE001
            LOGGER.exception("Coordinator refresh failed for %s", bro_id)
            raise UpdateFailed(f"BRO request failed: {err}") from err

    coordinator = DataUpdateCoordinator(
        hass,
        LOGGER,
        name=entry.title,
        update_method=update_data,
        update_interval=timedelta(hours=24),
    )
    await coordinator.async_config_entry_first_refresh()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, ["sensor"])
    LOGGER.debug("Integration setup complete for %s", bro_id)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload an integration entry and its sensor platform."""
    LOGGER.debug("Unloading integration entry %s", entry.data.get("bro_id"))
    if not await hass.config_entries.async_unload_platforms(entry, ["sensor"]):
        LOGGER.debug("Platform unload failed for %s", entry.data.get("bro_id"))
        return False
    hass.data[DOMAIN].pop(entry.entry_id, None)
    LOGGER.debug("Integration entry unloaded: %s", entry.data.get("bro_id"))
    return True
