# Phoenix Do Mar AIS Data

Public AIS track-history data for **PHOENIX DO MAR**, the sailing vessel associated with Oliver Widger.

## Vessel identity

- **Vessel:** PHOENIX DO MAR
- **MMSI:** 368448560
- **Callsign:** WDQ6966
- **Flag:** United States

The repository deliberately distinguishes coordinate-bearing AIS observations from reports that do not contain enough information to become geographic track points.

## Purpose

Public AIS services can expose only limited track history. This repository provides a persistent data store for accumulating reliable PHOENIX DO MAR position reports over time.

The resulting history is intended to be consumed by **Mauri's Weather & Water Conditions / pittsburg-saildata**, where it can be rendered as a longer historical vessel track.

## Automated collection

Collection is controlled by this repository itself using GitHub Actions.

```text
Open Waters AIS
      |
      v
.github/workflows/collect-phoenix-ais.yml
      |
      v
scripts/collect_phoenix_ais.py
      |
      | verified coordinate-bearing observations only
      v
phoenix-do-mar-track.json
      |
      v
pittsburg-saildata / Leaflet map
```

The workflow runs hourly and can also be started manually from the repository's **Actions** tab. The collector requests the Open Waters track for MMSI `368448560`, examines every returned observation, deduplicates it against the archive, and commits the JSON only when new coordinate-bearing points are found.

The workflow uses GitHub's repository-scoped `GITHUB_TOKEN` with `contents: write`. No separate personal access token is required.

## Collection rules

A report is eligible for `track_points` only when the source supplies an actual observation timestamp and valid latitude/longitude coordinates.

When supplied by the source, the collector also preserves speed over ground (SOG) and course over ground (COG). Missing optional SOG/COG values are stored as `null`.

Coordinates, timestamps, course, speed, or other navigation values are **never inferred, interpolated, geocoded, or fabricated** to fill gaps.

Duplicate observations are not appended. Existing observations and `observations_without_coordinates` are preserved.

## JSON data model

The primary asset is `phoenix-do-mar-track.json`.

A coordinate-bearing entry has this form:

```json
{
  "observed_at_utc": "2026-10-05T13:25:00Z",
  "lat": 37.000000,
  "lon": -123.000000,
  "sog_kn": 6.2,
  "cog_deg": 210.0,
  "source": "Open Waters AIS",
  "mmsi": "368448560",
  "callsign": "WDQ6966"
}
```

The coordinates in this example are illustrative only and are not an actual PHOENIX DO MAR observation.

### `track_points`

This is the authoritative geographic track. Entries belong here only when actual latitude and longitude plus an observation timestamp have been obtained from a reliable source.

### `observations_without_coordinates`

This section preserves historical evidence that cannot safely be plotted. It is not converted into geographic track points unless trustworthy coordinates and timestamps later become available.

## Files controlling collection

- `.github/workflows/collect-phoenix-ais.yml` — hourly schedule, repository permissions, and commit step.
- `scripts/collect_phoenix_ais.py` — Open Waters retrieval, validation, deduplication, and JSON update logic.
- `phoenix-do-mar-track.json` — persistent AIS history.

Because these files live in GitHub, the collector is under the same version control as its data. Its behavior can be inspected, changed, disabled, or rolled back from the repository.

## Security boundary

The collector has write permission only in **phoenix-ais-data** through the workflow's repository token. It does not require write access to the production `pittsburg-saildata` repository.

The production application can consume this public repository read-only.

## Data-quality principle

**No position is better than a false position.**

Missing history remains missing rather than being filled through estimation.
