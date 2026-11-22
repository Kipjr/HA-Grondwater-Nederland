"""BRO API client for GMW relation lookup and GLD CSV measurements."""
from __future__ import annotations

import csv
import io
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

        gld_id, gld_name, tube_number = find_latest_gld(relations)
        if not gld_id:
            LOGGER.warning("No GLD relation found for GMW %s", gmw_id)
            return {"gmw_id": gmw_id, "name": gmw_id, "gld_id": None, "tube_number": None, "measurements": [], "latest": None, "count": 0}

        csv_url = f"{GLD_CSV_URL}/{gld_id}"
        LOGGER.debug("Requesting GLD CSV %s (GMW=%s, tube=%s)", gld_id, gmw_id, tube_number)
        async with self._session.get(csv_url, timeout=30) as response:
            LOGGER.debug("GLD CSV HTTP status: %s for %s", response.status, gld_id)
            response.raise_for_status()
            csv_content = await response.text()
        parsed = parse_csv_measurements(csv_content)
        return {
            **parsed,
            "gmw_id": gmw_id,
            "gld_id": gld_id,
            "tube_number": tube_number,
            "name": gld_name or gmw_id,
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
    """Extract measurement rows from BRO CSV without assuming unit semantics."""
    rows = list(csv.DictReader(io.StringIO(content)))
    measurements: list[dict[str, Any]] = []
    LOGGER.debug("Parsing GLD CSV payload: %d rows", len(rows))
    for row in rows:
        normalized = {str(key).strip().lower(): value for key, value in row.items() if key}
        date_value = next(
            (value for key, value in normalized.items() if any(term in key for term in ("time", "datum", "date")) and value),
            None,
        )
        value_text = next(
            (value for key, value in normalized.items() if any(term in key for term in ("value", "waarde", "level", "stand")) and value),
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
    LOGGER.debug("CSV parsing complete: %d measurements", len(measurements))
    return {"measurements": measurements, "latest": measurements[-1] if measurements else None, "count": len(measurements)}
