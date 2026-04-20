from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import datetime

from app.core.schemas import (
    ChangeDetectionRequest,
    ChangeDetectionResult,
    DatasetInfo,
    DataSource,
    HealthResponse,
)
from app.core.config import settings
from app.services.detection_service import DetectionService

router = APIRouter()
_service = DetectionService()


# ── Health ────────────────────────────────────────────────────────────────────

@router.get("/health", response_model=HealthResponse, tags=["health"])
async def health():
    """System liveness check. Returns loaded sources and model status."""
    return HealthResponse(
        status="ok",
        version=settings.VERSION,
        timestamp=datetime.utcnow().isoformat(),
        sources=["NASA Landsat 8/9", "ESA Sentinel-2", "NASA MODIS", "ESA Sentinel-1"],
        ml_model_loaded=_service.ml_model_loaded,
    )


# ── Datasets ──────────────────────────────────────────────────────────────────

@router.get("/datasets", response_model=List[DatasetInfo], tags=["datasets"])
async def list_datasets():
    """Return the full catalogue of supported satellite data sources."""
    return _service.get_all_datasets()


@router.get("/datasets/{source}", response_model=DatasetInfo, tags=["datasets"])
async def get_dataset(source: DataSource):
    """Return detailed metadata for a single satellite source."""
    ds = _service.get_dataset(source)
    if not ds:
        raise HTTPException(status_code=404, detail=f"Dataset '{source}' not found")
    return ds


# ── Analysis ──────────────────────────────────────────────────────────────────

@router.post("/analysis/detect", response_model=ChangeDetectionResult, tags=["analysis"])
async def detect_changes(req: ChangeDetectionRequest):
    """
    Run AI-powered change detection between two dates for a bounding box.

    **Pipeline**
    1. Fetch imagery metadata from NASA CMR / ESA Dataspace catalogues
    2. Compute NDVI + NDWI spectral indices for each epoch
    3. Classify detected change types (ML model or heuristic fallback)
    4. Generate expert narrative via Claude AI

    **Supported change types**
    - Deforestation · Urban expansion · Flooding · Wildfire
    - Glacial retreat · Agricultural change · Coastline shift
    """
    try:
        return await _service.run_detection(req)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analysis/history", tags=["analysis"])
async def get_history(limit: int = Query(default=20, ge=1, le=100)):
    """Return the last N completed detection results (in-memory, resets on restart)."""
    return _service.get_history(limit)


@router.get("/analysis/history/{request_id}", response_model=ChangeDetectionResult, tags=["analysis"])
async def get_result(request_id: str):
    """Retrieve a single past result by its request ID."""
    result = _service.get_result(request_id)
    if not result:
        raise HTTPException(status_code=404, detail=f"Result '{request_id}' not found")
    return result
