"""BRO API client. Parsing is deliberately conservative until response fixtures are verified."""
from __future__ import annotations

import csv
import io
import xml.etree.ElementTree as ET
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import GLD_URL

class BroApi:
    def __init__(self, hass: HomeAssistant) -> None:
        self._session = async_get_clientsession(hass)

    async def async_get_measurements(self, bro_id: str) -> dict[str, Any]:
        """Fetch one GLD dossier via the experimental CSV output where available."""
        url = f"{GLD_URL}?broId={bro_id}&format=csv"
        async with self._session.get(url, timeout=30) as response:
            response.raise_for_status()
            content = await response.text()
        return parse_csv_measurements(content)

def parse_csv_measurements(content: str) -> dict[str, Any]:
    """Extract a measurement series from CSV without guessing unsupported units."""
    rows = list(csv.DictReader(io.StringIO(content)))
    measurements: list[dict[str, Any]] = []
    for row in rows:
        normalized = {str(k).strip().lower(): v for k, v in row.items() if k}
        date_value = next((v for k, v in normalized.items() if any(term in k for term in ("time", "datum", "date")) and v), None)
        value_text = next((v for k, v in normalized.items() if any(term in k for term in ("value", "waarde", "level", "stand")) and v), None)
        if date_value is None or value_text is None:
            continue
        try:
            value = float(value_text.replace(",", "."))
        except (ValueError, AttributeError):
            continue
        measurements.append({"time": date_value, "value": value, "raw": row})
    measurements.sort(key=lambda item: str(item["time"]))
    return {"measurements": measurements, "latest": measurements[-1] if measurements else None, "count": len(measurements)}

# Reserved for a future fixture-backed XML parser; current sensor values come from CSV.
def parse_xml_payload(content: str) -> ET.Element:
    """Parse XML payloads safely with the standard-library parser."""
    return ET.fromstring(content)
