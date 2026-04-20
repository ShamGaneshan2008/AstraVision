<<<<<<< HEAD
# 🛰️ Sentinel Watch — AI Satellite Change Detection System

<div align="center">

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111+-009688?style=flat-square&logo=fastapi&logoColor=white)
![NASA](https://img.shields.io/badge/NASA-MODIS%20%7C%20Landsat--9-FC3D21?style=flat-square)
![ESA](https://img.shields.io/badge/ESA-Sentinel--1%2F2%20%7C%20Copernicus-003247?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)
![Status](https://img.shields.io/badge/Status-Active-brightgreen?style=flat-square)

**Multi-source AI-powered satellite imagery change detection using NASA and ESA data streams.**  
Deforestation · Flood mapping · Urban sprawl · Glacier retreat · Wildfire tracking

[Features](#-features) · [Architecture](#-architecture) · [Quickstart](#-quickstart) · [API Docs](#-api-reference) · [Dashboard](#-dashboard) · [Data Sources](#-data-sources)

</div>

---

## 📡 What It Does

Sentinel Watch fuses imagery from **7 satellite sources** (NASA MODIS, Landsat-9, ESA Sentinel-1/2, VIIRS, Copernicus) into a single AI-powered change detection pipeline. It automatically classifies surface changes, scores anomaly severity, and streams real-time alerts through a FastAPI backend with an optional full-screen dashboard.

```
Satellite Feed → Preprocessing → NDVI / SAR / Thermal Index → AI Classification → Alert + Dashboard
```

### Example detections

| Event | Source | Detection Method | Confidence |
|---|---|---|---|
| Amazon deforestation | Landsat-9 | NDVI delta −0.42 | 94% |
| Ganges Delta flood | Sentinel-1 SAR | Backscatter shift | 97% |
| Lagos urban sprawl | Sentinel-2 | NDBI +0.28 | 91% |
| Himalayan glacier retreat | MODIS | Terminus shift −1.8 km | 89% |
| Siberia wildfire | VIIRS | Hotspot + FRP | 98% |

---

## ✨ Features

- **Multi-source fusion** — ingests NASA MODIS, Landsat-9, ESA Sentinel-1/2, VIIRS, and Copernicus in one pipeline
- **AI change classification** — Claude Sonnet-powered natural language analysis of detected anomalies
- **NDVI / SAR / Thermal indices** — computes spectral indices per scene for vegetation, flood, and heat detection
- **Before/after comparator** — aligned image pairs with pixel-level diff rendering
- **Temporal sequences** — tracks a region of interest across all available revisit passes
- **Real-time WebSocket feed** — push alerts to the dashboard or any subscriber as detections occur
- **REST API** — full CRUD for zones, analysis jobs, and archived comparisons
- **Pluggable data adapters** — swap in any STAC-compliant catalog (NASA Earthdata, ESA Copernicus Data Space)
- **Optional dashboard** — full-screen mission-control UI built with NASA's Horizon Design System aesthetic

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Data Ingestion Layer                     │
│  NASA Earthdata API  │  ESA Copernicus  │  USGS STAC Catalog │
└──────────────┬──────────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────┐
│                   Preprocessing Pipeline                     │
│  Band extraction  │  Atmospheric correction  │  Co-registration│
└──────────────┬──────────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────┐
│                  Change Detection Engine                     │
│  NDVI Delta  │  SAR Backscatter  │  Thermal Anomaly  │  NDBI │
└──────────────┬──────────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────┐
│                   AI Classification Layer                    │
│         Claude Sonnet — anomaly type + severity score        │
└──────────────┬──────────────────────────────────────────────┘
               │
    ┌──────────┴──────────┐
    ▼                     ▼
FastAPI REST API     WebSocket Feed
/api/v1/*            /ws/realtime
    │
    ▼
Optional Dashboard  (Sentinel Watch UI)
```

### Project structure

```
sentinel-watch/
├── app/
│   ├── main.py                  # FastAPI entry point
│   ├── api/
│   │   ├── routes/
│   │   │   ├── changes.py       # GET /api/v1/changes
│   │   │   ├── analyze.py       # POST /api/v1/analyze
│   │   │   ├── alerts.py        # GET /api/v1/alerts
│   │   │   └── compare.py       # POST /api/v1/compare
│   │   └── websocket.py         # WS /ws/realtime
│   ├── core/
│   │   ├── config.py            # Settings & env vars
│   │   ├── scheduler.py         # Background ingestion jobs
│   │   └── database.py          # SQLite / PostgreSQL session
│   ├── services/
│   │   ├── ingestion/
│   │   │   ├── nasa_earthdata.py
│   │   │   ├── esa_copernicus.py
│   │   │   └── stac_client.py
│   │   ├── indices/
│   │   │   ├── ndvi.py
│   │   │   ├── sar.py
│   │   │   └── thermal.py
│   │   ├── detection.py         # Change detection logic
│   │   └── ai_analysis.py       # Claude API integration
│   └── models/
│       ├── zone.py
│       ├── alert.py
│       └── comparison.py
├── dashboard/
│   └── index.html               # Optional standalone UI
├── tests/
│   ├── test_api.py
│   ├── test_detection.py
│   └── fixtures/
├── .env.example
├── requirements.txt
├── docker-compose.yml
=======
# 🛰 Orbital Insight AI

AI-powered satellite change detection using NASA and ESA imagery.  
Detects deforestation, urban expansion, flooding, wildfires, glacial retreat, and more.

---

## Project structure

```
orbital-insight-ai/
├── app/
│   ├── api/routes.py           # All API endpoints
│   ├── core/config.py          # Pydantic settings (reads .env)
│   ├── core/schemas.py         # Request / response models
│   ├── services/
│   │   └── detection_service.py  # Full pipeline orchestration
│   └── main.py                 # FastAPI app + startup
│
├── model/
│   ├── train.py                # Train RandomForest classifier
│   ├── inference.py            # Standalone inference wrapper
│   └── weights/                # Saved .pkl files (git-ignored)
│
├── utils/
│   ├── image_processing.py     # NDVI, NDWI, change masks, rasterio I/O
│   └── visualization.py        # PNG chart generators
│
├── data/
│   ├── raw/                    # Downloaded scenes (git-ignored)
│   ├── processed/              # Clipped / normalised rasters
│   └── samples/                # Small test fixtures
│
├── notebooks/
│   └── exploration.ipynb       # End-to-end walkthrough
│
├── frontend/
│   └── index.html              # Dark dashboard (standalone, no build step)
│
├── tests/
│   └── test_api.py             # Pytest suite (18 tests)
│
├── scripts/
│   └── download_data.py        # Search NASA CMR + ESA Dataspace
│
├── .env                        # Credentials (never commit)
├── requirements.txt
├── run.py                      # Uvicorn launcher
>>>>>>> e46083c (The files are being added)
└── README.md
```

---

<<<<<<< HEAD
## 🚀 Quickstart

### Prerequisites

- Python 3.11+
- NASA Earthdata account → [register here](https://urs.earthdata.nasa.gov/)
- ESA Copernicus account → [register here](https://dataspace.copernicus.eu/)
- Anthropic API key (for AI classification) → [get one here](https://console.anthropic.com/)

### 1. Clone and install

```bash
git clone https://github.com/ShamGaneshan2008/sentinel-watch.git
cd sentinel-watch
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
```

Edit `.env`:

```env
# === API Keys ===
ANTHROPIC_API_KEY=sk-ant-...
NASA_EARTHDATA_USERNAME=your_username
NASA_EARTHDATA_PASSWORD=your_password
ESA_COPERNICUS_CLIENT_ID=your_client_id
ESA_COPERNICUS_CLIENT_SECRET=your_secret

# === Database ===
DATABASE_URL=sqlite:///./sentinel.db
# For production: DATABASE_URL=postgresql://user:pass@localhost/sentinel

# === App Config ===
APP_ENV=development
ALERT_THRESHOLD_NDVI=0.25          # Minimum NDVI delta to trigger alert
ALERT_THRESHOLD_CONFIDENCE=0.80    # Minimum AI confidence to emit event
INGESTION_INTERVAL_HOURS=6         # How often to pull new scenes
MAX_CONCURRENT_JOBS=4

# === Dashboard ===
DASHBOARD_ENABLED=true
CORS_ORIGINS=["http://localhost:3000","http://localhost:8000"]
```

### 3. Run

```bash
uvicorn app.main:app --reload --port 8000
```

Open:
- **API** → `http://localhost:8000`
- **Interactive docs** → `http://localhost:8000/docs`
- **Dashboard** → open `dashboard/index.html` in your browser

### 4. Run with Docker

```bash
docker-compose up --build
```

```yaml
# docker-compose.yml (included)
services:
  api:
    build: .
    ports: ["8000:8000"]
    env_file: .env
    volumes: ["./data:/app/data"]
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: sentinel
      POSTGRES_USER: sentinel
      POSTGRES_PASSWORD: sentinel
=======
## Quick start

```bash
# 1. Clone and install
git clone https://github.com/YOUR_USERNAME/orbital-insight-ai
cd orbital-insight-ai
pip install -r requirements.txt

# 2. Configure credentials
cp .env .env.local   # edit with your keys (see Credentials below)

# 3. Run the server
python run.py --reload

# 4. Open docs
open http://localhost:8000/docs

# 5. Open the dashboard
open frontend/index.html
```

---

## API endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET`  | `/api/health` | Liveness + version + model status |
| `GET`  | `/api/datasets` | All supported satellite sources |
| `GET`  | `/api/datasets/{source}` | Single source details |
| `POST` | `/api/analysis/detect` | Run change detection |
| `GET`  | `/api/analysis/history` | Last N results |
| `GET`  | `/api/analysis/history/{id}` | Single result by ID |

### Example request

```bash
curl -X POST http://localhost:8000/api/analysis/detect \
  -H "Content-Type: application/json" \
  -d '{
    "bbox": {"min_lon":-62,"min_lat":-10,"max_lon":-58,"max_lat":-7},
    "date_before": "2021-01-01",
    "date_after":  "2023-01-01",
    "source": "esa_sentinel2",
    "cloud_cover_max": 15,
    "sensitivity": 0.8
  }'
```

---

## Data sources

| Source | Agency | Resolution | Revisit | Best for |
|--------|--------|-----------|---------|---------|
| Sentinel-2 MSI L2A | ESA | 10 m | 5 days | Vegetation, water, urban |
| Landsat 8/9 OLI-TIRS | NASA | 30 m | 16 days | Long time-series, thermal |
| MODIS MOD09A1 | NASA | 500 m | 8 days | Rapid fire / flood response |
| Sentinel-1 SAR GRD | ESA | 10 m | 6 days | All-weather, flood mapping |

---

## Credentials

| Key | Where to get |
|-----|-------------|
| `ANTHROPIC_API_KEY` | [console.anthropic.com](https://console.anthropic.com) |
| `NASA_EARTHDATA_USER/PASS` | [urs.earthdata.nasa.gov](https://urs.earthdata.nasa.gov) (free) |
| `ESA_DATASPACE_USER/PASS` | [dataspace.copernicus.eu](https://dataspace.copernicus.eu) (free) |

The API runs without any credentials — it uses simulated imagery and a fallback AI summary.  
Set keys progressively to unlock real data and Claude narratives.

---

## Train the ML model

```bash
# Train on synthetic data (no labels needed to start)
python -m model.train --samples 5000

# Enable in .env
USE_ML_MODEL=True

# CLI inference
python -m model.inference --ndvi-delta -0.28 --ndwi-delta 0.05
```

---

## Download real imagery

```bash
# Search ESA Sentinel-2 over Amazon
python scripts/download_data.py --preset amazon --source esa_sentinel2

# Custom bbox
python scripts/download_data.py \
  --source nasa_landsat \
  --bbox "-62,-10,-58,-7" \
  --date-before 2021-01-01 \
  --date-after  2023-01-01
>>>>>>> e46083c (The files are being added)
```

---

<<<<<<< HEAD
## 📖 API Reference

Base URL: `http://localhost:8000/api/v1`

Interactive Swagger UI available at `/docs` · ReDoc at `/redoc`

---

### `GET /changes`

Returns recent detected change events across all monitored zones.

**Query parameters**

| Param | Type | Default | Description |
|---|---|---|---|
| `severity` | `critical\|warning\|info` | all | Filter by severity level |
| `source` | `landsat\|sentinel\|modis\|viirs` | all | Filter by satellite source |
| `region` | string | — | Filter by region name or bbox `lat,lon,lat,lon` |
| `limit` | int | 50 | Max results |
| `since` | ISO 8601 | 7 days ago | Start of time window |

**Example**

```bash
curl "http://localhost:8000/api/v1/changes?severity=critical&limit=10"
```

**Response**

```json
{
  "count": 3,
  "changes": [
    {
      "id": "chg_01HXYZ",
      "region": "Amazon Basin · ROI-7G",
      "coordinates": { "lat": -5.4, "lon": -53.2 },
      "source": "landsat-9",
      "detected_at": "2025-04-02T14:32:07Z",
      "severity": "critical",
      "index": "ndvi",
      "delta": -0.42,
      "area_km2": 847,
      "confidence": 0.94,
      "classification": "deforestation",
      "ai_summary": "Primary forest clearing consistent with illegal agricultural expansion..."
    }
  ]
}
```

---

### `POST /analyze`

Submits a region of interest for on-demand AI analysis.

**Request body**

```json
{
  "bbox": [-54.1, -6.2, -52.8, -4.9],
  "date_range": {
    "start": "2024-01-01",
    "end": "2025-04-01"
  },
  "sources": ["landsat-9", "sentinel-2"],
  "indices": ["ndvi", "sar"],
  "ai_classify": true
}
```

**Response**

```json
{
  "job_id": "job_02HABC",
  "status": "processing",
  "estimated_seconds": 45,
  "webhook": "/api/v1/jobs/job_02HABC"
}
```

Poll `GET /jobs/{job_id}` for results, or listen on `/ws/realtime` for push delivery.

---

### `POST /compare`

Returns a pixel-level before/after comparison for a zone and date pair.

**Request body**

```json
{
  "zone_id": "amazon-roi-7g",
  "date_before": "2024-01-12",
  "date_after": "2025-04-02",
  "source": "landsat-9",
  "band_combo": "natural_color"
}
```

**Response**

```json
{
  "before_url": "https://...",
  "after_url": "https://...",
  "diff_url": "https://...",
  "ndvi_delta": -0.42,
  "changed_pixels_pct": 68.1,
  "change_area_km2": 847
}
```

---

### `GET /alerts`

Returns the live alert feed, sorted by recency.

```bash
curl "http://localhost:8000/api/v1/alerts?severity=critical"
```

---

### `WebSocket /ws/realtime`

Connect to receive push alerts as detections occur.

```python
import asyncio, websockets, json

async def listen():
    async with websockets.connect("ws://localhost:8000/ws/realtime") as ws:
        async for message in ws:
            alert = json.loads(message)
            print(f"[{alert['severity'].upper()}] {alert['region']} — {alert['classification']}")

asyncio.run(listen())
```

**Message schema**

```json
{
  "event": "change_detected",
  "severity": "critical",
  "region": "Amazon Basin · ROI-7G",
  "classification": "deforestation",
  "confidence": 0.94,
  "delta": -0.42,
  "area_km2": 847,
  "source": "landsat-9",
  "timestamp": "2025-04-02T14:32:07Z"
}
=======
## Connecting real rasters

Once you have downloaded GeoTIFF scenes, replace the two mock methods in  
`app/services/detection_service.py`:

```python
# Replace _fetch_imagery_meta() with real NASA CMR / ESA OData calls
# Replace _compute_indices() with rasterio band math:

from utils.image_processing import compute_ndvi, compute_ndwi, read_band

nir_arr, profile = read_band("scene_nir.tif")
red_arr, _       = read_band("scene_red.tif")
ndvi = compute_ndvi(nir_arr, red_arr)
>>>>>>> e46083c (The files are being added)
```

---

<<<<<<< HEAD
## 🌍 Data Sources

| Satellite | Agency | Revisit | Resolution | Best for |
|---|---|---|---|---|
| **Landsat-9** | NASA / USGS | 16 days | 30 m | Vegetation, land use |
| **MODIS** | NASA | Daily | 250 m–1 km | Fire, snow, daily change |
| **VIIRS** | NASA / NOAA | Daily | 375 m | Active fire, night lights |
| **Sentinel-1** | ESA | 6–12 days | 10 m | SAR — flood, deforestation |
| **Sentinel-2** | ESA | 5 days | 10 m | High-res multispectral |
| **Sentinel-3** | ESA | ~2 days | 300 m | Ocean color, sea surface temp |
| **Copernicus DEM** | ESA | — | 30 m | Elevation reference |

Data is accessed via:
- [NASA Earthdata STAC API](https://cmr.earthdata.nasa.gov/stac/)
- [ESA Copernicus Data Space](https://dataspace.copernicus.eu/)
- [USGS EarthExplorer](https://earthexplorer.usgs.gov/)

---

## 🔬 Detection Methods

### NDVI Change Detection
Normalized Difference Vegetation Index delta between two dates. Values below `−0.25` trigger a warning; below `−0.40` trigger a critical alert.

```python
ndvi = (NIR - RED) / (NIR + RED)
delta = ndvi_after - ndvi_before
```

### SAR Backscatter (Sentinel-1)
Synthetic Aperture Radar is cloud-independent. A significant drop in C-band backscatter (VV/VH) indicates surface moisture change or clearing.

### Normalized Burn Ratio (NBR)
Detects fire scars using SWIR and NIR bands. `dNBR > 0.66` = high severity burn.

### Urban Index (NDBI)
Normalized Difference Built-up Index using SWIR1 and NIR. Rising NDBI over vegetated areas indicates urban expansion.

---

## 🤖 AI Classification

When a spectral change exceeds threshold, the detection payload is sent to Claude Sonnet for natural language classification:

```python
# app/services/ai_analysis.py

async def classify_change(detection: ChangeEvent) -> AIAnalysis:
    prompt = f"""
    Satellite change detection event:
    - Region: {detection.region}
    - Index: {detection.index} delta = {detection.delta}
    - Area affected: {detection.area_km2} km²
    - Source: {detection.source}
    - Date range: {detection.date_before} → {detection.date_after}

    Classify the event type, assess environmental severity,
    and provide a 2-sentence plain-English summary.
    Respond as JSON: {{ "type", "severity", "summary", "confidence" }}
    """
    response = anthropic_client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}]
    )
    return AIAnalysis.model_validate_json(response.content[0].text)
```

---

## 🧪 Testing

```bash
# Run all tests
pytest

# With coverage
pytest --cov=app --cov-report=html

# Just API tests
pytest tests/test_api.py -v

# Just detection logic
pytest tests/test_detection.py -v
=======
## Run tests

```bash
pytest tests/ -v
pytest tests/ -v --cov=app --cov-report=term-missing
>>>>>>> e46083c (The files are being added)
```

---

<<<<<<< HEAD
## 🗺️ Dashboard

The optional dashboard (`dashboard/index.html`) is a standalone HTML file — no build step needed. Just open it in a browser while the API is running.

Features:
- Live global map with animated change zones
- Before/after image comparator
- Temporal sequence timeline per ROI
- AI analysis sidebar with confidence scoring
- Real-time alert feed via WebSocket
- Layer toggles: NDVI · SAR · Thermal · Flood · Urban

> NASA Horizon Design System aesthetic — Inter + DM Mono typography, NASA red `#FC3D21`, deep navy `#0B3D91`

---

## 🚧 Roadmap

- [ ] Cloud masking via Fmask integration
- [ ] Email / Slack / webhook alert delivery
- [ ] Multi-temporal compositing (reduce cloud noise)
- [ ] GeoJSON zone import / export
- [ ] PDF report generation per detection event
- [ ] Timelapse video export per ROI
- [ ] PostgreSQL + PostGIS spatial queries
- [ ] Docker GPU support for faster index computation
- [ ] Public demo deployment on Railway / Render

---

## 🤝 Contributing

Pull requests welcome. Please open an issue first for anything beyond small fixes.

```bash
# Fork → clone → branch
git checkout -b feature/your-feature

# Make changes, then
pytest                          # tests must pass
black app/ tests/               # format
ruff check app/ tests/          # lint

git commit -m "feat: your feature"
git push origin feature/your-feature
# Open PR on GitHub
```

---

## 📄 License

MIT — see [LICENSE](LICENSE)

---

<div align="center">

Built by **Sham Ganeshan** · [GitHub @ShamGaneshan2008](https://github.com/ShamGaneshan2008)

*Data from NASA Earthdata and ESA Copernicus — open access for scientific and educational use.*

</div>
=======
## Change types detected

| Type | Primary indicator |
|------|------------------|
| Deforestation | ΔNDVI < −0.1 |
| Wildfire | ΔNDVI < −0.25 (severe) |
| Flooding | ΔNDWI > +0.05, concurrent ΔNDVI drop |
| Urban expansion | ΔNDVI drop + ΔNDWI drop |
| Glacial retreat | ΔNDWI rise + ΔNDVI rise |
| Agricultural | Moderate ΔNDVI oscillation |
| SAR flood (Sentinel-1) | Backscatter anomaly |
>>>>>>> e46083c (The files are being added)
