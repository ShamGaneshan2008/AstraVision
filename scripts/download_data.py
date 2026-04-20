"""
scripts/download_data.py — Download sample satellite imagery for development.

Sources:
  - NASA EarthData (Landsat / MODIS) via CMR API
  - ESA Copernicus Dataspace (Sentinel-1 / Sentinel-2) via OData API

Usage:
    # Download Sentinel-2 sample over Amazon deforestation hotspot
    python scripts/download_data.py --source esa_sentinel2 --preset amazon

    # Download Landsat over urban expansion area
    python scripts/download_data.py --source nasa_landsat --preset dubai

    # Custom bbox + dates
    python scripts/download_data.py \\
        --source esa_sentinel2 \\
        --bbox "-3.0,51.0,-2.0,52.0" \\
        --date-before 2022-06-01 \\
        --date-after  2023-06-01 \\
        --out data/raw/

Credentials: set NASA_EARTHDATA_USER/PASS and ESA_DATASPACE_USER/PASS in .env
"""

import argparse
import asyncio
import json
import os
import sys

# Make project root importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False

from app.core.config import settings


# ── Preset AOIs ───────────────────────────────────────────────────────────────

PRESETS = {
    "amazon": {
        "bbox": "-62.0,-10.0,-58.0,-7.0",
        "description": "Amazon deforestation hotspot, Pará state, Brazil",
        "change_type": "deforestation",
    },
    "dubai": {
        "bbox": "55.1,25.0,55.5,25.4",
        "description": "Dubai urban expansion corridor",
        "change_type": "urban_expansion",
    },
    "california_fire": {
        "bbox": "-121.5,38.5,-120.5,39.5",
        "description": "California wildfire scar, Sierra Nevada",
        "change_type": "wildfire",
    },
    "aral_sea": {
        "bbox": "58.0,43.5,61.0,45.5",
        "description": "Aral Sea shrinkage — water body change",
        "change_type": "flood/drought",
    },
    "greenland": {
        "bbox": "-50.0,67.0,-45.0,69.0",
        "description": "Greenland glacial retreat zone",
        "change_type": "glacial_retreat",
    },
}


# ── ESA Dataspace token ───────────────────────────────────────────────────────

async def get_esa_token() -> str:
    if not HTTPX_AVAILABLE:
        raise RuntimeError("httpx not installed: pip install httpx")
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            settings.ESA_TOKEN_ENDPOINT,
            data={
                "grant_type": "password",
                "username": settings.ESA_DATASPACE_USER,
                "password": settings.ESA_DATASPACE_PASS,
                "client_id": "cdse-public",
            },
        )
        resp.raise_for_status()
        return resp.json()["access_token"]


# ── NASA CMR search ───────────────────────────────────────────────────────────

async def search_nasa(
    short_name: str,
    bbox: str,
    date_before: str,
    date_after: str,
    cloud_max: int = 20,
) -> list:
    """Search NASA CMR for granules matching bbox + date range."""
    if not HTTPX_AVAILABLE:
        raise RuntimeError("httpx not installed: pip install httpx")
    min_lon, min_lat, max_lon, max_lat = bbox.split(",")
    params = {
        "short_name": short_name,
        "temporal[]": f"{date_before}T00:00:00Z,{date_after}T23:59:59Z",
        "bounding_box": f"{min_lon},{min_lat},{max_lon},{max_lat}",
        "cloud_cover[]": f"-1,{cloud_max}",
        "page_size": 5,
        "sort_key": "-start_date",
    }
    auth = (settings.NASA_EARTHDATA_USER, settings.NASA_EARTHDATA_PASS)
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(settings.NASA_CMR_ENDPOINT, params=params, auth=auth)
        resp.raise_for_status()
        return resp.json().get("feed", {}).get("entry", [])


# ── ESA Dataspace search ──────────────────────────────────────────────────────

async def search_esa(
    collection: str,
    bbox: str,
    date_before: str,
    date_after: str,
    cloud_max: int = 20,
) -> list:
    """Search ESA Copernicus Dataspace for products."""
    if not HTTPX_AVAILABLE:
        raise RuntimeError("httpx not installed: pip install httpx")
    min_lon, min_lat, max_lon, max_lat = bbox.split(",")
    wkt = (
        f"POLYGON(({min_lon} {min_lat},{max_lon} {min_lat},"
        f"{max_lon} {max_lat},{min_lon} {max_lat},{min_lon} {min_lat}))"
    )
    filter_str = (
        f"Collection/Name eq '{collection}' "
        f"and ContentDate/Start gt {date_before}T00:00:00.000Z "
        f"and ContentDate/Start lt {date_after}T23:59:59.000Z "
        f"and Attributes/OData.CSC.DoubleAttribute/any(att:att/Name eq 'cloudCover' "
        f"and att/OData.CSC.DoubleAttribute/Value le {cloud_max}) "
        f"and OData.CSC.Intersects(area=geography'SRID=4326;{wkt}')"
    )
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(
            settings.ESA_DATASPACE_ENDPOINT,
            params={"$filter": filter_str, "$top": 5, "$orderby": "ContentDate/Start desc"},
        )
        resp.raise_for_status()
        return resp.json().get("value", [])


# ── Main ──────────────────────────────────────────────────────────────────────

async def main(args):
    out_dir = args.out
    os.makedirs(out_dir, exist_ok=True)

    bbox = args.bbox
    date_before = args.date_before
    date_after  = args.date_after

    if args.preset:
        preset = PRESETS.get(args.preset)
        if not preset:
            print(f"Unknown preset '{args.preset}'. Available: {list(PRESETS)}")
            return
        bbox = preset["bbox"]
        print(f"Using preset '{args.preset}': {preset['description']}")

    print(f"\nSource     : {args.source}")
    print(f"BBox       : {bbox}")
    print(f"Date range : {date_before} → {date_after}")
    print(f"Output dir : {out_dir}\n")

    results = []

    if args.source == "esa_sentinel2":
        if not settings.ESA_DATASPACE_USER:
            print("⚠  ESA_DATASPACE_USER not set in .env — showing mock results only")
        else:
            print("Searching ESA Copernicus Dataspace for Sentinel-2…")
            results = await search_esa("SENTINEL-2", bbox, date_before, date_after)

    elif args.source == "nasa_landsat":
        if not settings.NASA_EARTHDATA_USER:
            print("⚠  NASA_EARTHDATA_USER not set in .env — showing mock results only")
        else:
            print("Searching NASA CMR for Landsat…")
            results = await search_nasa("LANDSAT_OT_C2_L2", bbox, date_before, date_after)

    elif args.source == "nasa_modis":
        if not settings.NASA_EARTHDATA_USER:
            print("⚠  NASA_EARTHDATA_USER not set in .env")
        else:
            print("Searching NASA CMR for MODIS…")
            results = await search_nasa("MOD09A1", bbox, date_before, date_after)

    elif args.source == "esa_sentinel1":
        if not settings.ESA_DATASPACE_USER:
            print("⚠  ESA_DATASPACE_USER not set in .env")
        else:
            print("Searching ESA Copernicus Dataspace for Sentinel-1…")
            results = await search_esa("SENTINEL-1", bbox, date_before, date_after)

    if results:
        out_path = os.path.join(out_dir, f"{args.source}_search_results.json")
        with open(out_path, "w") as f:
            json.dump(results, f, indent=2)
        print(f"Found {len(results)} scene(s). Metadata saved → {out_path}")
        for r in results[:3]:
            name = r.get("title") or r.get("producer_granule_id") or r.get("Name", "unknown")
            print(f"  • {name}")
    else:
        print("No results (credentials not set or no scenes match). "
              "Register at https://urs.earthdata.nasa.gov or https://dataspace.copernicus.eu")

    # Always write a sample manifest so the pipeline has something to read
    manifest = {
        "query": {
            "source": args.source,
            "bbox": bbox,
            "date_before": date_before,
            "date_after": date_after,
        },
        "scenes_found": len(results),
        "note": "Set credentials in .env to download actual imagery.",
    }
    manifest_path = os.path.join(out_dir, "manifest.json")
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
    print(f"\nManifest written → {manifest_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download satellite imagery metadata")
    parser.add_argument("--source", choices=["esa_sentinel2", "nasa_landsat", "nasa_modis", "esa_sentinel1"],
                        default="esa_sentinel2")
    parser.add_argument("--preset", choices=list(PRESETS.keys()), default=None,
                        help="Use a predefined AOI preset")
    parser.add_argument("--bbox", default="-3.0,51.0,-2.0,52.0",
                        help="min_lon,min_lat,max_lon,max_lat")
    parser.add_argument("--date-before", default="2022-06-01")
    parser.add_argument("--date-after",  default="2023-06-01")
    parser.add_argument("--out", default="data/raw/", help="Output directory")
    args = parser.parse_args()
    asyncio.run(main(args))
