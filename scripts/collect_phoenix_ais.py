#!/usr/bin/env python3
"""Collect PHOENIX DO MAR AIS track points from Open Waters.

The collector never invents navigation data. A point is accepted only when
Open Waters supplies a timestamp plus valid latitude/longitude coordinates.
"""

import json
import math
import pathlib
import sys
import urllib.request
from datetime import datetime, timezone

MMSI = "368448560"
CALLSIGN = "WDQ6966"
SOURCE = "Open Waters AIS"
TRACK_URL = f"https://ais.openwaters.io/v1/vessels/{MMSI}/track"
DATA_FILE = pathlib.Path(__file__).resolve().parents[1] / "phoenix-do-mar-track.json"


def fetch_track():
    req = urllib.request.Request(
        TRACK_URL,
        headers={"Accept": "application/json", "User-Agent": "phoenix-ais-data-collector/1"},
    )
    with urllib.request.urlopen(req, timeout=30) as response:
        if response.status < 200 or response.status >= 300:
            raise RuntimeError(f"Open Waters HTTP {response.status}")
        return json.load(response)


def valid_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def normalize_time(value):
    if not isinstance(value, str) or not value.strip():
        return None
    text = value.strip()
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def optional_number(values, index):
    if not isinstance(values, list) or index >= len(values):
        return None
    value = values[index]
    return float(value) if valid_number(value) else None


def extract_points(payload):
    geometry = payload.get("geometry") if isinstance(payload, dict) else None
    props = payload.get("properties") if isinstance(payload, dict) else None
    if not isinstance(geometry, dict) or not isinstance(props, dict):
        raise RuntimeError("Open Waters track response is missing geometry/properties")

    coordinates = geometry.get("coordinates")
    times = props.get("times")
    sog = props.get("sog")
    cog = props.get("cog")
    if not isinstance(coordinates, list) or not isinstance(times, list):
        raise RuntimeError("Open Waters track response is missing coordinates/times")

    points = []
    for i, coord in enumerate(coordinates):
        if i >= len(times) or not isinstance(coord, list) or len(coord) < 2:
            continue
        lon, lat = coord[0], coord[1]
        observed = normalize_time(times[i])
        if not observed or not valid_number(lat) or not valid_number(lon):
            continue
        lat, lon = float(lat), float(lon)
        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            continue
        points.append({
            "observed_at_utc": observed,
            "lat": lat,
            "lon": lon,
            "sog_kn": optional_number(sog, i),
            "cog_deg": optional_number(cog, i),
            "source": SOURCE,
            "mmsi": MMSI,
            "callsign": CALLSIGN,
        })
    return points


def key(point):
    return (
        str(point.get("mmsi", MMSI)),
        point.get("observed_at_utc"),
        point.get("lat"),
        point.get("lon"),
    )


def main():
    with DATA_FILE.open("r", encoding="utf-8") as f:
        archive = json.load(f)

    vessel = archive.get("vessel", {})
    if str(vessel.get("mmsi", "")) != MMSI:
        raise RuntimeError("archive vessel MMSI does not match PHOENIX DO MAR")

    existing = archive.setdefault("track_points", [])
    seen = {key(p) for p in existing if isinstance(p, dict)}
    candidates = extract_points(fetch_track())
    added = []
    for point in candidates:
        if key(point) not in seen:
            existing.append(point)
            seen.add(key(point))
            added.append(point)

    existing.sort(key=lambda p: p.get("observed_at_utc", ""))
    if added:
        with DATA_FILE.open("w", encoding="utf-8") as f:
            json.dump(archive, f, indent=2, ensure_ascii=False)
            f.write("\n")

    newest = max(added, key=lambda p: p["observed_at_utc"]) if added else None
    print(json.dumps({"added": len(added), "newest": newest}, separators=(",", ":")))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"collector error: {exc}", file=sys.stderr)
        sys.exit(1)
