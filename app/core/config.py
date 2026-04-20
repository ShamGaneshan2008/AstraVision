from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    # --- Project ---
    PROJECT_NAME: str = "Orbital Insight AI"
    VERSION: str = "1.0.0"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = False

    # --- CORS ---
    ALLOWED_ORIGINS: List[str] = ["*"]

    # --- Anthropic (Claude AI summaries) ---
    ANTHROPIC_API_KEY: str = ""

    # --- NASA EarthData ---
    # Register free at https://urs.earthdata.nasa.gov/
    NASA_EARTHDATA_USER: str = ""
    NASA_EARTHDATA_PASS: str = ""
    NASA_CMR_ENDPOINT: str = "https://cmr.earthdata.nasa.gov/search/granules.json"

    # --- ESA Copernicus Dataspace ---
    # Register free at https://dataspace.copernicus.eu/
    ESA_DATASPACE_USER: str = ""
    ESA_DATASPACE_PASS: str = ""
    ESA_DATASPACE_ENDPOINT: str = "https://catalogue.dataspace.copernicus.eu/odata/v1/Products"
    ESA_TOKEN_ENDPOINT: str = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"

    # --- ML model ---
    MODEL_WEIGHTS_PATH: str = "model/weights/change_detector.pkl"
    MODEL_CONFIDENCE_THRESHOLD: float = 0.45
    USE_ML_MODEL: bool = False          # False → heuristic fallback (no weights needed)

    # --- Data paths ---
    DATA_RAW_DIR: str = "data/raw"
    DATA_PROCESSED_DIR: str = "data/processed"
    DATA_SAMPLES_DIR: str = "data/samples"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


settings = Settings()
