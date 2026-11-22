"""Groundwater sensors."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN


async def async_setup_entry(hass, entry: ConfigEntry, async_add_entities) -> None:
    """Create entities for the configured BRO dossier."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    keys = ("latest_value", "latest_time", "measurement_count")
    async_add_entities([GroundwaterSensor(coordinator, entry, key) for key in keys])


class GroundwaterSensor(CoordinatorEntity, SensorEntity):
    """Sensor based on the latest BRO data update."""

    _attr_has_entity_name = True

    def __init__(self, coordinator, entry: ConfigEntry, key: str) -> None:
        """Initialize an entity and its device metadata."""
        super().__init__(coordinator)
        self._key = key
        self._entry = entry

    @property
    def unique_id(self) -> str:
        """Return a stable unique ID based on the dossier and sensor type."""
        return f"{self._entry.data['bro_id']}_{self._key}"

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device metadata for the selected dossier."""
        bro_id = self._entry.data["bro_id"]
        return DeviceInfo(
            identifiers={(DOMAIN, bro_id)},
            name=f"BRO {bro_id}",
            manufacturer="BRO / TNO",
            model="Groundwater level dossier (GLD)",
        )

    @property
    def name(self) -> str:
        """Return the sensor display name."""
        names = {
            "latest_value": "Latest groundwater measurement",
            "latest_time": "Latest measurement time",
            "measurement_count": "Measurement count",
        }
        return names[self._key]

    @property
    def native_unit_of_measurement(self) -> str | None:
        """Return the unit when measurement semantics are verified."""
        return None

    @property
    def device_class(self) -> SensorDeviceClass | None:
        """Return the device class for the timestamp entity."""
        if self._key == "latest_time":
            return SensorDeviceClass.TIMESTAMP
        return None

    @property
    def state_class(self) -> SensorStateClass | None:
        """Return the state class for numeric entities."""
        if self._key == "latest_value":
            return SensorStateClass.MEASUREMENT
        if self._key == "measurement_count":
            return SensorStateClass.TOTAL
        return None

    @property
    def entity_category(self) -> EntityCategory | None:
        """Return the category for diagnostic entities."""
        if self._key == "measurement_count":
            return EntityCategory.DIAGNOSTIC
        return None

    @property
    def native_value(self) -> Any:
        """Return the current value for this entity."""
        data = self.coordinator.data or {}
        latest = data.get("latest")
        if self._key == "latest_value":
            return latest.get("value") if latest else None
        if self._key == "latest_time":
            if latest:
                try:
                    time_value = str(latest["time"]).replace("Z", "+00:00")
                    return datetime.fromisoformat(time_value)
                except (ValueError, TypeError, KeyError):
                    return None
            return None
        return data.get("count", 0)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return diagnostic attributes for the latest measurement."""
        latest = (self.coordinator.data or {}).get("latest")
        return {
            "bro_id": self._entry.data["bro_id"],
            "raw_latest": latest.get("raw") if latest else None,
        }
