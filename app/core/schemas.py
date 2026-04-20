from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum


class DataSource(str, Enum):
    NASA_LANDSAT = "nasa_landsat"
    ESA_SENTINEL2 = "esa_sentinel2"
    NASA_MODIS = "nasa_modis"
    ESA_SENTINEL1 = "esa_sentinel1"


class ChangeType(str, Enum):
    DEFORESTATION = "deforestation"
    URBAN_EXPANSION = "urban_expansion"
    FLOOD = "flood"
    WILDFIRE = "wildfire"
    GLACIAL_RETREAT = "glacial_retreat"
    AGRICULTURAL = "agricultural"
    COASTLINE = "coastline"
    UNKNOWN = "unknown"


class BoundingBox(BaseModel):
    min_lon: float = Field(..., ge=-180, le=180)
    min_lat: float = Field(..., ge=-90, le=90)
    max_lon: float = Field(..., ge=-180, le=180)
    max_lat: float = Field(..., ge=-90, le=90)


class ChangeDetectionRequest(BaseModel):
    bbox: BoundingBox
    date_before: str = Field(..., description="ISO date, e.g. 2022-01-01")
    date_after: str = Field(..., description="ISO date, e.g. 2023-01-01")
    source: DataSource = DataSource.ESA_SENTINEL2
    cloud_cover_max: float = Field(default=20.0, ge=0, le=100)
    sensitivity: float = Field(default=0.5, ge=0.1, le=1.0)


class DetectedChange(BaseModel):
    change_type: ChangeType
    confidence: float
    area_km2: float
    centroid_lon: float
    centroid_lat: float
    description: str


class ChangeDetectionResult(BaseModel):
    request_id: str
    status: str
    source: DataSource
    date_before: str
    date_after: str
    bbox: BoundingBox
    ndvi_before: Optional[float] = None
    ndvi_after: Optional[float] = None
    ndwi_before: Optional[float] = None
    ndwi_after: Optional[float] = None
    ndvi_delta: Optional[float] = None
    ndwi_delta: Optional[float] = None
    change_percentage: float
    detected_changes: List[DetectedChange]
    ai_summary: str
    processing_time_ms: int


class DatasetInfo(BaseModel):
    source: DataSource
    name: str
    description: str
    resolution_m: int
    revisit_days: int
    bands: List[str]
    coverage: str
    api_endpoint: str
    requires_auth: bool


class HealthResponse(BaseModel):
    status: str
    version: str
    timestamp: str
    sources: List[str]
    ml_model_loaded: bool
