"""
DetectionService — orchestrates the full change-detection pipeline.

Flow:
  1.  Fetch imagery metadata (NASA CMR / ESA Dataspace)
  2.  Compute spectral indices (NDVI, NDWI) per epoch
  3.  Classify change types  →  ML model if loaded, heuristic fallback otherwise
  4.  Generate AI narrative  →  Claude via Anthropic API
  5.  Persist result in in-memory history (ring buffer, last 200 entries)
"""

import asyncio
import random
import uuid
import time
import httpx
import os
from collections import deque
from typing import List, Optional, Dict

from app.core.schemas import (
    BoundingBox,
    ChangeDetectionRequest,
    ChangeDetectionResult,
    DataSource,
    DatasetInfo,
    DetectedChange,
    ChangeType,
)
from app.core.config import settings


# ─────────────────────────────────────────────────────────────────────────────
# Dataset catalogue
# ─────────────────────────────────────────────────────────────────────────────

CATALOGUE: Dict[DataSource, DatasetInfo] = {
    DataSource.NASA_LANDSAT: DatasetInfo(
        source=DataSource.NASA_LANDSAT,
        name="Landsat 8/9 OLI-TIRS",
        description=(
            "NASA/USGS Collection 2 Level-2 surface reflectance. "
            "30 m multispectral + 100 m thermal."
        ),
        resolution_m=30,
        revisit_days=16,
        bands=["B1 Coastal", "B2 Blue", "B3 Green", "B4 Red",
               "B5 NIR", "B6 SWIR1", "B7 SWIR2", "B10 TIRS1"],
        coverage="Global land (WRS-2)",
        api_endpoint="https://cmr.earthdata.nasa.gov/search/granules.json",
        requires_auth=True,
    ),
    DataSource.ESA_SENTINEL2: DatasetInfo(
        source=DataSource.ESA_SENTINEL2,
        name="Sentinel-2 MSI L2A",
        description=(
            "ESA Copernicus Sentinel-2 multispectral. "
            "13 bands, 10–60 m resolution."
        ),
        resolution_m=10,
        revisit_days=5,
        bands=["B02 Blue", "B03 Green", "B04 Red", "B05 RE1",
               "B06 RE2", "B07 RE3", "B08 NIR", "B8A Narrow NIR",
               "B09 WV", "B11 SWIR1", "B12 SWIR2"],
        coverage="Global land 84°N–56°S",
        api_endpoint="https://catalogue.dataspace.copernicus.eu/odata/v1/Products",
        requires_auth=True,
    ),
    DataSource.NASA_MODIS: DatasetInfo(
        source=DataSource.NASA_MODIS,
        name="MODIS Terra/Aqua MOD09A1",
        description=(
            "NASA MODIS 8-day composite, 500 m. "
            "Best for rapid time-series and fire monitoring."
        ),
        resolution_m=500,
        revisit_days=8,
        bands=["Band1 Red", "Band2 NIR", "Band3 Blue", "Band4 Green",
               "Band5 SWIR1", "Band6 SWIR2", "Band7 SWIR3"],
        coverage="Global daily",
        api_endpoint="https://cmr.earthdata.nasa.gov/search/granules.json",
        requires_auth=True,
    ),
    DataSource.ESA_SENTINEL1: DatasetInfo(
        source=DataSource.ESA_SENTINEL1,
        name="Sentinel-1 SAR GRD",
        description=(
            "ESA C-band SAR — cloud-penetrating radar. "
            "Ideal for flood mapping and ground deformation."
        ),
        resolution_m=10,
        revisit_days=6,
        bands=["VV Polarisation", "VH Polarisation"],
        coverage="Global land + ocean",
        api_endpoint="https://catalogue.dataspace.copernicus.eu/odata/v1/Products",
        requires_auth=True,
    ),
}


# ─────────────────────────────────────────────────────────────────────────────
# Service class
# ─────────────────────────────────────────────────────────────────────────────

class DetectionService:
    def __init__(self):
        self._history: deque = deque(maxlen=200)
        self._history_index: Dict[str, ChangeDetectionResult] = {}
        self.ml_model_loaded: bool = self._try_load_model()

    # ── Model ──────────────────────────────────────────────────────────────

    def _try_load_model(self) -> bool:
        """Attempt to load a serialised sklearn / joblib model from disk."""
        if not settings.USE_ML_MODEL:
            return False
        path = settings.MODEL_WEIGHTS_PATH
        if not os.path.exists(path):
            print(f"[DetectionService] No weights found at {path} — using heuristic fallback")
            return False
        try:
            import joblib  # type: ignore
            self._model = joblib.load(path)
            print(f"[DetectionService] ML model loaded from {path}")
            return True
        except Exception as e:
            print(f"[DetectionService] Failed to load model: {e}")
            return False

    # ── Catalogue ──────────────────────────────────────────────────────────

    def get_all_datasets(self) -> List[DatasetInfo]:
        return list(CATALOGUE.values())

    def get_dataset(self, source: DataSource) -> Optional[DatasetInfo]:
        return CATALOGUE.get(source)

    # ── History ────────────────────────────────────────────────────────────

    def _save(self, result: ChangeDetectionResult):
        self._history.appendleft(result)
        self._history_index[result.request_id] = result

    def get_history(self, limit: int = 20) -> List[dict]:
        return [r.model_dump() for r in list(self._history)[:limit]]

    def get_result(self, request_id: str) -> Optional[ChangeDetectionResult]:
        return self._history_index.get(request_id)

    # ── Main pipeline ──────────────────────────────────────────────────────

    async def run_detection(self, req: ChangeDetectionRequest) -> ChangeDetectionResult:
        t0 = time.monotonic()
        request_id = str(uuid.uuid4())[:8].upper()

        # 1. Fetch imagery metadata for both epochs concurrently
        meta_before, meta_after = await asyncio.gather(
            self._fetch_imagery_meta(req.bbox, req.date_before, req.source, req.cloud_cover_max),
            self._fetch_imagery_meta(req.bbox, req.date_after, req.source, req.cloud_cover_max),
        )

        # 2. Compute spectral indices
        idx_before, idx_after = await asyncio.gather(
            self._compute_indices(req.bbox, req.date_before, req.source),
            self._compute_indices(req.bbox, req.date_after, req.source),
        )

        ndvi_delta = round(idx_after["ndvi"] - idx_before["ndvi"], 4)
        ndwi_delta = round(idx_after["ndwi"] - idx_before["ndwi"], 4)
        change_pct = round(
            min(100.0, abs(ndvi_delta) * 150 + abs(ndwi_delta) * 80 + random.uniform(0, 5)), 1
        )

        # 3. Classify
        if self.ml_model_loaded:
            changes = self._ml_classify(ndvi_delta, ndwi_delta, req)
        else:
            changes = self._heuristic_classify(ndvi_delta, ndwi_delta, req.source, req.sensitivity)

        # 4. AI narrative
        ai_summary = await self._generate_summary(
            req, ndvi_delta, ndwi_delta, change_pct, changes
        )

        elapsed = int((time.monotonic() - t0) * 1000)

        result = ChangeDetectionResult(
            request_id=request_id,
            status="completed",
            source=req.source,
            date_before=req.date_before,
            date_after=req.date_after,
            bbox=req.bbox,
            ndvi_before=idx_before["ndvi"],
            ndvi_after=idx_after["ndvi"],
            ndwi_before=idx_before["ndwi"],
            ndwi_after=idx_after["ndwi"],
            ndvi_delta=ndvi_delta,
            ndwi_delta=ndwi_delta,
            change_percentage=change_pct,
            detected_changes=changes,
            ai_summary=ai_summary,
            processing_time_ms=elapsed,
        )
        self._save(result)
        return result

    # ── Imagery fetch (mock → replace with real HTTP) ──────────────────────

    async def _fetch_imagery_meta(
        self, bbox: BoundingBox, date: str, source: DataSource, cloud_max: float
    ) -> dict:
        """
        Production: call NASA CMR or ESA Dataspace search endpoint.
        Replace this method body with real httpx calls + auth headers.

        NASA CMR example:
            GET https://cmr.earthdata.nasa.gov/search/granules.json
                ?short_name=LANDSAT_OT_L2
                &temporal[]={date},{date}
                &bounding_box={min_lon},{min_lat},{max_lon},{max_lat}
                &cloud_cover[]=-1,{cloud_max}

        ESA Dataspace example:
            GET https://catalogue.dataspace.copernicus.eu/odata/v1/Products
                ?$filter=Collection/Name eq 'SENTINEL-2'
                  and ContentDate/Start gt {date}T00:00:00.000Z
                  and OData.CSC.Intersects(...)
        """
        await asyncio.sleep(random.uniform(0.25, 0.75))
        prefix = {
            DataSource.NASA_LANDSAT: "LC09_L2SP",
            DataSource.ESA_SENTINEL2: "S2B_MSIL2A",
            DataSource.NASA_MODIS: "MOD09A1.A",
            DataSource.ESA_SENTINEL1: "S1A_IW_GRDH",
        }[source]
        return {
            "scene_id": f"{prefix}_{date.replace('-','')}_{random.randint(100000,999999)}",
            "date": date,
            "cloud_cover_pct": round(random.uniform(0, cloud_max * 0.8), 1),
            "source": source,
        }

    # ── Spectral indices (mock → replace with rasterio band math) ──────────

    async def _compute_indices(
        self, bbox: BoundingBox, date: str, source: DataSource
    ) -> dict:
        """
        Production: download GeoTIFF bands via GDAL/rasterio, then:
            NDVI = (NIR - Red) / (NIR + Red)
            NDWI = (Green - NIR) / (Green + NIR)
        """
        await asyncio.sleep(random.uniform(0.15, 0.45))
        nir   = random.uniform(0.30, 0.55)
        red   = random.uniform(0.05, 0.18)
        green = random.uniform(0.10, 0.22)
        ndvi  = (nir - red)   / (nir + red)   if (nir + red)   else 0.0
        ndwi  = (green - nir) / (green + nir) if (green + nir) else 0.0
        return {"ndvi": round(ndvi, 4), "ndwi": round(ndwi, 4)}

    # ── ML classifier ──────────────────────────────────────────────────────

    def _ml_classify(
        self,
        ndvi_delta: float,
        ndwi_delta: float,
        req: ChangeDetectionRequest,
    ) -> List[DetectedChange]:
        """
        Use loaded sklearn / joblib model.
        Feature vector: [ndvi_delta, ndwi_delta, sensitivity, source_idx]
        """
        source_idx = list(DataSource).index(req.source)
        features = [[ndvi_delta, ndwi_delta, req.sensitivity, source_idx]]
        try:
            pred   = self._model.predict(features)[0]
            proba  = max(self._model.predict_proba(features)[0])
            ct = ChangeType(pred) if pred in ChangeType._value2member_map_ else ChangeType.UNKNOWN
            return [DetectedChange(
                change_type=ct,
                confidence=round(float(proba), 3),
                area_km2=round(abs(ndvi_delta) * 500 + random.uniform(1, 50), 1),
                centroid_lon=round(random.uniform(-80, 140), 4),
                centroid_lat=round(random.uniform(-40, 60), 4),
                description=f"ML model prediction: {ct.value} (p={proba:.2f})",
            )]
        except Exception:
            return self._heuristic_classify(ndvi_delta, ndwi_delta, req.source, req.sensitivity)

    # ── Heuristic classifier ────────────────────────────────────────────────

    def _heuristic_classify(
        self,
        ndvi_delta: float,
        ndwi_delta: float,
        source: DataSource,
        sensitivity: float,
    ) -> List[DetectedChange]:
        threshold = 0.08 * (1.5 - sensitivity)
        changes: List[DetectedChange] = []

        # SAR source: use backscatter for flood detection
        if source == DataSource.ESA_SENTINEL1:
            if abs(ndwi_delta) > threshold * 0.6:
                changes.append(self._make_change(
                    ChangeType.FLOOD,
                    min(0.95, abs(ndwi_delta) * 3.5),
                    abs(ndwi_delta) * 400,
                    "SAR backscatter anomaly consistent with surface water inundation.",
                ))
            return changes or [self._unknown()]

        # Strong NDVI loss
        if ndvi_delta < -threshold:
            mag = abs(ndvi_delta)
            ct = ChangeType.WILDFIRE if mag > 0.25 else (
                 ChangeType.FLOOD if ndwi_delta > 0.05 else ChangeType.DEFORESTATION)
            desc = {
                ChangeType.DEFORESTATION: f"Canopy loss (ΔNDVI={ndvi_delta:.3f}). Probable clearing.",
                ChangeType.WILDFIRE:      f"Severe burn scar (ΔNDVI={ndvi_delta:.3f}).",
                ChangeType.FLOOD:         "NDVI decline + elevated NDWI → likely inundation.",
            }.get(ct, "Spectral anomaly.")
            changes.append(self._make_change(ct, min(0.97, mag * 2.8), mag * 300, desc))

        # Urban expansion
        if ndvi_delta < -threshold * 0.6 and ndwi_delta < -0.02:
            changes.append(self._make_change(
                ChangeType.URBAN_EXPANSION,
                min(0.90, abs(ndvi_delta) * 2.2),
                abs(ndvi_delta) * 120,
                "NDVI loss + low NDWI → probable impervious surface expansion.",
            ))

        # Glacial / snow
        if ndwi_delta > threshold and ndvi_delta > 0.05:
            changes.append(self._make_change(
                ChangeType.GLACIAL_RETREAT,
                min(0.88, ndwi_delta * 2.5),
                ndwi_delta * 200,
                "Water signal increase with greening → glacial melt exposure.",
            ))

        # Agricultural cycle
        if threshold * 0.3 < abs(ndvi_delta) < threshold:
            changes.append(self._make_change(
                ChangeType.AGRICULTURAL, 0.65,
                abs(ndvi_delta) * 180,
                "Moderate NDVI shift consistent with crop rotation or harvest.",
            ))

        return changes if changes else [self._unknown()]

    def _make_change(
        self, ct: ChangeType, conf: float, area: float, desc: str
    ) -> DetectedChange:
        return DetectedChange(
            change_type=ct,
            confidence=round(conf, 3),
            area_km2=round(max(0.5, area + random.uniform(-5, 10)), 1),
            centroid_lon=round(random.uniform(-80, 140), 4),
            centroid_lat=round(random.uniform(-40, 60), 4),
            description=desc,
        )

    def _unknown(self) -> DetectedChange:
        return DetectedChange(
            change_type=ChangeType.UNKNOWN,
            confidence=0.40,
            area_km2=round(random.uniform(0.5, 15), 1),
            centroid_lon=round(random.uniform(-80, 140), 4),
            centroid_lat=round(random.uniform(-40, 60), 4),
            description="Spectral anomaly detected; insufficient signal to classify change type.",
        )

    # ── Claude AI summary ──────────────────────────────────────────────────

    async def _generate_summary(
        self,
        req: ChangeDetectionRequest,
        ndvi_delta: float,
        ndwi_delta: float,
        change_pct: float,
        changes: List[DetectedChange],
    ) -> str:
        change_str = ", ".join(c.change_type.value for c in changes)
        best_conf  = max(c.confidence for c in changes)

        prompt = (
            "You are a senior remote sensing analyst. Write a concise 3-sentence expert "
            "summary of this change detection result for a technical audience. "
            "Be specific about index values and their physical meaning.\n\n"
            f"Source: {req.source.value}\n"
            f"Period: {req.date_before} → {req.date_after}\n"
            f"ΔNDVI: {ndvi_delta:+.4f}\n"
            f"ΔNDWI: {ndwi_delta:+.4f}\n"
            f"Change coverage: {change_pct:.1f}% of AOI\n"
            f"Change types: {change_str}\n"
            f"Peak confidence: {best_conf:.0%}\n"
        )

        api_key = settings.ANTHROPIC_API_KEY
        if not api_key:
            return self._fallback_summary(req, ndvi_delta, ndwi_delta, change_pct, changes)

        try:
            async with httpx.AsyncClient(timeout=20) as client:
                resp = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "Content-Type": "application/json",
                        "x-api-key": api_key,
                        "anthropic-version": "2023-06-01",
                    },
                    json={
                        "model": "claude-sonnet-4-20250514",
                        "max_tokens": 300,
                        "messages": [{"role": "user", "content": prompt}],
                    },
                )
                data = resp.json()
                return data["content"][0]["text"].strip()
        except Exception:
            return self._fallback_summary(req, ndvi_delta, ndwi_delta, change_pct, changes)

    def _fallback_summary(
        self, req, ndvi_delta, ndwi_delta, change_pct, changes
    ) -> str:
        types = ", ".join(c.change_type.value for c in changes)
        return (
            f"Analysis of {req.source.value} imagery ({req.date_before} → {req.date_after}) "
            f"identified {types} across {change_pct:.1f}% of the AOI. "
            f"ΔNDVI of {ndvi_delta:+.3f} and ΔNDWI of {ndwi_delta:+.3f} support these classifications "
            f"with peak confidence of {max(c.confidence for c in changes):.0%}. "
            "Set ANTHROPIC_API_KEY in .env for AI-generated narratives."
        )
