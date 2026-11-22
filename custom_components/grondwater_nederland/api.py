"""BRO API client. Parsing is deliberately conservative until fixtures are verified."""
from __future__ import annotations

import csv
import io
import xml.etree.ElementTree as ET
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import GLD_URL, LOGGER


class BroApi:
    """Asynchronous client for the BRO groundwater service."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Create a client using Home Assistant's shared HTTP session."""
        self._session = async_get_clientsession(hass)

    async def async_get_measurements(self, bro_id: str) -> dict[str, Any]:
        """Fetch one GLD dossier via the experimental CSV output."""
        url = f"{GLD_URL}/objectsAsCsv/{bro_id}"
        LOGGER.debug("Requesting BRO data: %s", url)
        async with self._session.get(url, timeout=30) as response:
            LOGGER.debug("BRO HTTP response status: %s for %s", response.status, bro_id)
            response.raise_for_status()
            content = await response.text()
        result = self.parse_measurements(content)
        LOGGER.debug("Parsed BRO response for %s: %s measurements", bro_id, result.get("count", 0))
        return result

    @staticmethod
    def parse_measurements(content: str) -> dict[str, Any]:
        """Parse the CSV response into measurement records."""
        return parse_csv_measurements(content)


def parse_csv_measurements(content: str) -> dict[str, Any]:
    """Extract measurement rows without guessing unsupported units."""
    rows = list(csv.DictReader(io.StringIO(content)))
    measurements: list[dict[str, Any]] = []
    LOGGER.debug("Parsing CSV payload: %d rows", len(rows))
    for row in rows:
        normalized = {str(k).strip().lower(): v for k, v in row.items() if k}
        date_value = next(
            (
                value
                for key, value in normalized.items()
                if any(term in key for term in ("time", "datum", "date"))
                and value
            ),
            None,
        )
        value_text = next(
            (
                value
                for key, value in normalized.items()
                if any(term in key for term in ("value", "waarde", "level", "stand"))
                and value
            ),
            None,
        )
        if date_value is None or value_text is None:
            LOGGER.debug("Skipping row missing timestamp/value fields: %s", row)
            continue
        try:
            value = float(value_text.replace(",", "."))
        except (ValueError, AttributeError):
            LOGGER.debug("Skipping row with invalid numeric value: %s", value_text)
            continue
        measurements.append({"time": date_value, "value": value, "raw": row})
    measurements.sort(key=lambda item: str(item["time"]))
    LOGGER.debug("CSV parsing complete: %d valid measurements", len(measurements))
    return {
        "measurements": measurements,
        "latest": measurements[-1] if measurements else None,
        "count": len(measurements),
    }


def parse_xml_payload(content: str) -> ET.Element:
    """Parse XML payloads with the standard-library parser."""
    LOGGER.debug("Parsing XML payload (%d bytes)", len(content))
    return ET.fromstring(content)
