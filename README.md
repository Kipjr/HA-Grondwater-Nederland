# Groundwater Monitor Nederland (Home Assistant)

Early development integration for Dutch BRO groundwater-monitoring data.

## Current flow

- Configure a GMW registration ID.
- Query the BRO GMW relations endpoint to locate linked GMN and GLD references.
- Select the GLD relation with the latest research end/start date across the tubes.
- Fetch measurements from the BRO GLD CSV endpoint.
- Create sensors on a device named after the GMN name followed by the GMW ID, e.g. `Leiden grondwatermeetnet (GMW000000029500)`.

The CSV interpretation and measurement units remain provisional until validated against real fixtures. Polling is daily and does not imply daily measurements.

## Sources

- GMW relations: https://publiek.broservices.nl/gm/v1/gmw-relations/{GMW-ID}?inclMetadata=true
- GLD CSV: https://publiek.broservices.nl/gm/gld/v1/objectsAsCsv/{GLD-ID}
