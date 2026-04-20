"""
tests/test_api.py — Unit and integration tests for the FastAPI routes.

Run:
    pytest tests/ -v
    pytest tests/ -v --cov=app --cov-report=term-missing
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


# ─────────────────────────────────────────────────────────────────────────────
# Health
# ─────────────────────────────────────────────────────────────────────────────

def test_health_ok():
    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "version" in data
    assert isinstance(data["sources"], list)
    assert len(data["sources"]) >= 4


# ─────────────────────────────────────────────────────────────────────────────
# Datasets
# ─────────────────────────────────────────────────────────────────────────────

def test_list_datasets():
    resp = client.get("/api/datasets")
    assert resp.status_code == 200
    datasets = resp.json()
    assert len(datasets) == 4
    sources = {d["source"] for d in datasets}
    assert "esa_sentinel2" in sources
    assert "nasa_landsat" in sources


def test_get_dataset_sentinel2():
    resp = client.get("/api/datasets/esa_sentinel2")
    assert resp.status_code == 200
    d = resp.json()
    assert d["resolution_m"] == 10
    assert d["revisit_days"] == 5


def test_get_dataset_not_found():
    resp = client.get("/api/datasets/unknown_source")
    assert resp.status_code == 422  # pydantic enum validation


# ─────────────────────────────────────────────────────────────────────────────
# Change detection
# ─────────────────────────────────────────────────────────────────────────────

VALID_PAYLOAD = {
    "bbox": {"min_lon": -3.0, "min_lat": 51.0, "max_lon": -2.0, "max_lat": 52.0},
    "date_before": "2022-06-01",
    "date_after": "2023-06-01",
    "source": "esa_sentinel2",
    "cloud_cover_max": 20,
    "sensitivity": 0.7,
}


def test_detect_returns_200():
    resp = client.post("/api/analysis/detect", json=VALID_PAYLOAD)
    assert resp.status_code == 200


def test_detect_result_structure():
    resp = client.post("/api/analysis/detect", json=VALID_PAYLOAD)
    data = resp.json()
    assert data["status"] == "completed"
    assert "request_id" in data
    assert "ndvi_delta" in data
    assert "ndwi_delta" in data
    assert 0.0 <= data["change_percentage"] <= 100.0
    assert len(data["detected_changes"]) >= 1
    assert data["ai_summary"]


def test_detect_change_confidence_range():
    resp = client.post("/api/analysis/detect", json=VALID_PAYLOAD)
    for change in resp.json()["detected_changes"]:
        assert 0.0 <= change["confidence"] <= 1.0
        assert change["area_km2"] >= 0


def test_detect_all_sources():
    for source in ["nasa_landsat", "esa_sentinel2", "nasa_modis", "esa_sentinel1"]:
        payload = {**VALID_PAYLOAD, "source": source}
        resp = client.post("/api/analysis/detect", json=payload)
        assert resp.status_code == 200, f"Failed for source: {source}"


def test_detect_invalid_bbox():
    payload = {**VALID_PAYLOAD, "bbox": {"min_lon": 200, "min_lat": 0, "max_lon": 201, "max_lat": 1}}
    resp = client.post("/api/analysis/detect", json=payload)
    assert resp.status_code == 422


def test_detect_invalid_sensitivity():
    payload = {**VALID_PAYLOAD, "sensitivity": 5.0}
    resp = client.post("/api/analysis/detect", json=payload)
    assert resp.status_code == 422


# ─────────────────────────────────────────────────────────────────────────────
# History
# ─────────────────────────────────────────────────────────────────────────────

def test_history_grows():
    before = len(client.get("/api/analysis/history").json())
    client.post("/api/analysis/detect", json=VALID_PAYLOAD)
    after = len(client.get("/api/analysis/history").json())
    assert after == before + 1


def test_history_by_id():
    resp = client.post("/api/analysis/detect", json=VALID_PAYLOAD)
    rid = resp.json()["request_id"]
    detail = client.get(f"/api/analysis/history/{rid}")
    assert detail.status_code == 200
    assert detail.json()["request_id"] == rid


def test_history_not_found():
    resp = client.get("/api/analysis/history/NOTEXIST")
    assert resp.status_code == 404
