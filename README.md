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
└── README.md
```

---

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
```

---

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
```

---

## Run tests

```bash
pytest tests/ -v
pytest tests/ -v --cov=app --cov-report=term-missing
```

---

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
