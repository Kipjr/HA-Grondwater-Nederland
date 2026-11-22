"""Groundwater sensors."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([GroundwaterSensor(coordinator, entry, key) for key in ("latest_value", "latest_time", "measurement_count")])

class GroundwaterSensor(CoordinatorEntity, SensorEntity):
    """Sensor based on the most recent BRO data update."""
    _attr_has_entity_name = True

    def __init__(self, coordinator, entry: ConfigEntry, key: str) -> None:
        super().__init__(coordinator)
        self._key = key
        self._entry = entry
        self._attr_unique_id = f"{entry.data['bro_id']}_{key}"
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, entry.data["bro_id"])}, name=f"BRO {entry.data['bro_id']}", manufacturer="BRO / TNO", model="Groundwater level dossier (GLD)")
        if key == "latest_value":
            self._attr_name = "Latest groundwater measurement"
            self._attr_native_unit_of_measurement = None
            self._attr_state_class = SensorStateClass.MEASUREMENT
        elif key == "latest_time":
            self._attr_name = "Latest measurement time"
            self._attr_device_class = SensorDeviceClass.TIMESTAMP
        else:
            self._attr_name = "Measurement count"
            self._attr_entity_category = EntityCategory.DIAGNOSTIC
            self._attr_state_class = SensorStateClass.TOTAL

    @property
    def native_value(self) -> Any:
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
        latest = (self.coordinator.data or {}).get("latest")
        return {"bro_id": self._entry.data["bro_id"], "raw_latest": latest.get("raw") if latest else None}
