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
    """Create entities for the configured BRO GMW well."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    keys = ("latest_value", "latest_time", "measurement_count")
    async_add_entities([GroundwaterSensor(coordinator, entry, key) for key in keys])


class GroundwaterSensor(CoordinatorEntity, SensorEntity):
    """Sensor based on the latest linked GLD measurement."""

    _attr_has_entity_name = True

    def __init__(self, coordinator, entry: ConfigEntry, key: str) -> None:
        """Initialize the entity and device metadata."""
        super().__init__(coordinator)
        self._key = key
        self._entry = entry

    @property
    def unique_id(self) -> str:
        """Return the stable GMW ID and sensor key."""
        return f"{self._entry.data['bro_id']}_{self._key}"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device metadata, including the linked GMN name and GMW ID."""
        data = self.coordinator.data or {}
        gmw_id = self._entry.data["bro_id"]
        well_name = data.get("name") or gmw_id
        return DeviceInfo(
            identifiers={(DOMAIN, gmw_id)},
            name=f"{well_name} ({gmw_id})",
            manufacturer="BRO / TNO",
            model="Groundwater monitoring well (GMW)",
        )

    @property
    def name(self) -> str:
        """Return the sensor display name."""
        return {"latest_value": "Latest groundwater measurement", "latest_time": "Latest measurement time", "measurement_count": "Measurement count"}[self._key]

    @property
    def native_unit_of_measurement(self) -> str | None:
        """Return metres for groundwater height measurements."""
        return "m" if self._key == "latest_value" else None

    @property
    def device_class(self) -> SensorDeviceClass | None:
        """Return the timestamp device class when needed."""
        return SensorDeviceClass.TIMESTAMP if self._key == "latest_time" else None

    @property
    def state_class(self) -> SensorStateClass | None:
        """Return state class for numeric sensor entities."""
        if self._key == "latest_value":
            return SensorStateClass.MEASUREMENT
        if self._key == "measurement_count":
            return SensorStateClass.TOTAL
        return None

    @property
    def entity_category(self) -> EntityCategory | None:
        """Mark the count sensor as diagnostic."""
        return EntityCategory.DIAGNOSTIC if self._key == "measurement_count" else None

    @property
    def native_value(self) -> Any:
        """Return the latest value from the coordinator data."""
        data = self.coordinator.data or {}
        latest = data.get("latest")
        if self._key == "latest_value":
            return latest.get("value") if latest else None
        if self._key == "latest_time":
            if latest:
                try:
                    return datetime.fromisoformat(str(latest["time"]).replace("Z", "+00:00"))
                except (ValueError, TypeError, KeyError):
                    return None
            return None
        return data.get("count", 0)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Expose identifiers, ground level, recent raw rows and height history."""
        data = self.coordinator.data or {}
        measurements = data.get("measurements", [])
        recent = list(reversed(measurements[-14:]))
        return {
            "gmw_id": data.get("gmw_id"),
            "gld_id": data.get("gld_id"),
            "tube_number": data.get("tube_number"),
            "groundLevelPosition": data.get("ground_level_position"),
            "raw": [item.get("raw", {}) for item in recent],
            "raw30": [item.get("value") for item in reversed(measurements[-30:])],
        }
