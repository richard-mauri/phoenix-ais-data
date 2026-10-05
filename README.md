# Phoenix Do Mar AIS Data

Public AIS track-history data for **PHOENIX DO MAR**, the sailing vessel associated with Oliver Widger.

## Vessel identity

- **Vessel:** PHOENIX DO MAR
- **MMSI:** 368448560
- **Callsign:** WDQ6966
- **Flag:** United States

The identity above has been corroborated from public AIS sources. The repository deliberately distinguishes verified AIS data from observations that do not contain enough information to become geographic track points.

## Purpose

Public AIS websites often expose only a vessel's latest position or a limited amount of track history. This repository provides a small, persistent data store for accumulating reliable PHOENIX DO MAR position reports over time.

The resulting history is intended to be consumed by **Mauri's Weather & Water Conditions / pittsburg-saildata**, where it can be rendered as a longer historical vessel track on the sailing map.

## Architecture

```text
Reliable public AIS sources
          |
          v
ChatGPT Phoenix AIS Track Watch
(hourly condition watch)
          |
          | verified coordinate-bearing observations only
          v
phoenix-ais-data GitHub repository
          |
          | phoenix-do-mar-track.json
          v
Render-hosted Go service
          |
          | HTTPS / cached proxy endpoint
          v
pittsburg-saildata / Leaflet sailing map
```

The data repository is intentionally separate from the application source repository. The AIS collection process therefore does not need write access to the production `pittsburg-saildata` repository.

## Collection rules

The Phoenix AIS Track Watch checks reliable public AIS sources hourly.

A report is eligible for `track_points` only when the source exposes a real coordinate-bearing observation. A track point should contain, when available:

- AIS observation timestamp in UTC
- latitude
- longitude
- speed over ground (SOG), knots
- course over ground (COG), degrees
- source
- MMSI and callsign

The AIS observation time must be kept separate from the time the monitoring process discovers or collects the report.

Coordinates, timestamps, course, or other navigation values must **never be inferred, interpolated, geocoded, or fabricated** merely to fill gaps.

A report containing only a speed, course, or relative statement such as “position received 10 minutes ago” is not sufficient to create a geographic track point.

Duplicate observations should not be appended.

## JSON data model

The primary asset is:

```text
phoenix-do-mar-track.json
```

At a high level it contains:

```json
{
  "schema_version": 1,
  "vessel": {
    "name": "PHOENIX DO MAR",
    "mmsi": "368448560",
    "callsign": "WDQ6966",
    "flag": "US"
  },
  "track_points": [],
  "observations_without_coordinates": []
}
```

### `track_points`

This is the authoritative geographic track. Entries belong here only when actual latitude and longitude have been obtained from a reliable source.

A typical future entry will look like:

```json
{
  "observed_at_utc": "2026-10-05T13:25:00Z",
  "lat": 37.000000,
  "lon": -123.000000,
  "sog_kn": 6.2,
  "cog_deg": 210.0,
  "source": "AIS source",
  "mmsi": "368448560",
  "callsign": "WDQ6966"
}
```

The coordinates above are illustrative only and are **not** an actual PHOENIX DO MAR observation.

### `observations_without_coordinates`

This section preserves useful historical evidence that cannot safely be plotted. Examples include ChatGPT AIS notifications that reported a new speed or report age but did not expose the underlying latitude and longitude.

Keeping these observations allows later reconciliation if trustworthy historical coordinates become available.

## Runtime integration

The intended application architecture is for the Render-hosted Go service to retrieve the raw JSON asset from this public repository over HTTPS.

Rather than having browser-side Leaflet code depend directly on GitHub, the Go service can expose an application endpoint such as:

```text
/api/phoenix-track
```

The Go service can periodically refresh and cache the GitHub JSON. The map then requests the local API endpoint and renders `track_points` as a Leaflet polyline.

Caching also allows the service to continue serving the last successfully retrieved track if GitHub is temporarily unavailable.

## Security boundary

This repository is intentionally data-only.

The desired permissions model is:

```text
AIS collection process
    -> write access to phoenix-ais-data only

Render service
    -> public read-only HTTPS access to phoenix-ais-data

pittsburg-saildata
    -> no AIS collector write access required
```

This isolates automated AIS data collection from the production application's source code.

## Current status

The initial JSON was created from seven Phoenix AIS Watch notification emails plus publicly available corroborating observations.

Those historical notifications did not expose trustworthy latitude/longitude coordinates, so no coordinates were manufactured from them. Consequently the initial `track_points` array is intentionally empty.

The collection system is designed to populate that array only as reliable coordinate-bearing observations become available.

## Data-quality principle

**No position is better than a false position.**

The purpose of this repository is to build a defensible vessel track. Missing history is therefore retained as missing rather than being filled through estimation.
