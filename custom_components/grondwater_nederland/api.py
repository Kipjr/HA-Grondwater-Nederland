"""BRO API client for GMW relation lookup and GLD CSV measurements."""
from __future__ import annotations

import csv
import io
from datetime import datetime
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import GLD_CSV_URL, GMW_RELATIONS_URL, LOGGER


class BroApi:
    """Asynchronous client for BRO GMW relations and GLD measurements."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Create a client using Home Assistant's shared HTTP session."""
        self._session = async_get_clientsession(hass)

    async def async_get_measurements(self, gmw_id: str) -> dict[str, Any]:
        """Fetch a GMW's relations, then measurements for a linked GLD."""
        relations_url = f"{GMW_RELATIONS_URL}/{gmw_id}?inclMetadata=true"
        LOGGER.debug("Requesting GMW relations: %s", relations_url)
        async with self._session.get(relations_url, timeout=30) as response:
            LOGGER.debug("GMW relations HTTP status: %s for %s", response.status, gmw_id)
            response.raise_for_status()
            relations = await response.json()

        gld_id, gld_name, tube_number = find_latest_gld(relations)\n        ground_level_position = (relations.get("characteristics") or {}).get(\n            "groundLevelPosition"\n        )
        if not gld_id:
            LOGGER.warning("No GLD relation found for GMW %s", gmw_id)
            return {
                "gmw_id": gmw_id, "name": gmw_id, "gld_id": None,
                "tube_number": None, "ground_level_position": ground_level_position,\n                "measurements": [], "latest": None, "count": 0,
            }

        csv_url = f"{GLD_CSV_URL}/{gld_id}"
        LOGGER.debug("Requesting GLD CSV %s (GMW=%s, tube=%s)", gld_id, gmw_id, tube_number)
        async with self._session.get(csv_url, timeout=30) as response:
            LOGGER.debug("GLD CSV HTTP status: %s for %s", response.status, gld_id)
            response.raise_for_status()
            csv_content = await response.text()
        parsed = parse_csv_measurements(csv_content)
        return {
            **parsed, "gmw_id": gmw_id, "gld_id": gld_id,
            "tube_number": tube_number, "name": gld_name or gmw_id,\n            "ground_level_position": ground_level_position,
        }


def find_latest_gld(relations: dict[str, Any]) -> tuple[str | None, str | None, int | None]:
    """Choose the GLD relation with the latest researchLastDate across tubes."""
    candidates: list[tuple[str, str | None, int | None, str]] = []
    for tube in relations.get("monitoringTubeReferences", []):
        tube_number = tube.get("tubeNumber")
        for gld in tube.get("gldReferences", []):
            characteristics = gld.get("characteristics") or {}
            gld_id = gld.get("broId")
            if not gld_id:
                continue
            last_date = str(characteristics.get("researchLastDate") or characteristics.get("researchFirstDate") or "")
            gmn_name = None
            for gmn in tube.get("gmnReferences", []):
                gmn_name = (gmn.get("characteristics") or {}).get("name") or gmn_name
            candidates.append((gld_id, gmn_name, tube_number, last_date))
    if not candidates:
        return None, None, None
    candidates.sort(key=lambda item: item[3], reverse=True)
    selected = candidates[0]
    return selected[0], selected[1], selected[2]


def parse_csv_measurements(content: str) -> dict[str, Any]:
    """Parse BRO's embedded observation table and preserve its real columns."""
    rows = list(csv.reader(io.StringIO(content.lstrip("\\ufeff"))))
    measurements: list[dict[str, Any]] = []
    observation_header: list[str] | None = None

    for row in rows:
        if not row:
            continue
        first = row[0].strip().lower()
        second = row[1].strip().lower() if len(row) > 1 else ""
        if first == "tijdstip meting" and second == "waterstand":
            observation_header = [column.strip() for column in row]
            LOGGER.debug("Found BRO observation table columns: %s", observation_header)
            continue
        if observation_header is None or len(row) < 2:
            continue

        timestamp_text = row[0].strip()
        value_text = row[1].strip()
        try:
            timestamp = datetime.fromisoformat(timestamp_text.replace("Z", "+00:00"))
            height = float(value_text.replace(",", "."))
        except (ValueError, TypeError):
            LOGGER.debug("Skipping non-measurement row in observation table: %s", row)
            continue

        raw = {
            observation_header[index]: value.strip() if index < len(row) else ""
            for index, value in enumerate(row[:len(observation_header)])
        }
        measurements.append({"time": timestamp.isoformat(), "value": height, "raw": raw})

    measurements.sort(key=lambda item: item["time"])
    LOGGER.debug("Parsed %d BRO groundwater observations", len(measurements))
    return {
        "measurements": measurements,
        "latest": measurements[-1] if measurements else None,
        "count": len(measurements),
    }
