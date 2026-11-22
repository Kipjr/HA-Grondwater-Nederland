# Groundwater Monitor Nederland (Home Assistant)

Early development integration for Dutch BRO groundwater-monitoring data.

## Status

This PR is an initial scaffold. It accepts a **GLD dossier BRO-ID** directly and polls the experimental GLD CSV endpoint once per day. It does not yet discover wells from a postcode or select a GMW/tube automatically. The CSV endpoint and returned column structure must be verified against real response fixtures before treating measurements or units as reliable.

## Install

Install through HACS as a custom repository (Integration), or copy `custom_components/grondwater_nederland` into Home Assistant's `custom_components` directory. Restart Home Assistant and add **Groundwater Monitor Nederland**.

## Entities

- Latest groundwater measurement (unit intentionally unset until response semantics are verified)
- Latest measurement time
- Measurement count (diagnostic)

Updates are requested every 24 hours. This does not imply that BRO records a daily observation.

## Sources

- BRO GLD service: https://publiek.broservices.nl/gm/gld/v1/
- PDOK/TNO BRO GM characteristics dataset: https://service.pdok.nl/tno/bro-grondwatermonitoring-in-samenhang-karakteristieken/atom/index.xml

## Roadmap

- Verify experimental GLD CSV endpoint and response fixtures / unit semantics.
- Add GMW tube and GLD dossier discovery.
- Add postcode geocoding, nearby-well ranking and selection.
- Add diagnostics and more robust history retrieval.
