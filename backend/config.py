from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional
import os

class Settings(BaseSettings):
    MONGODB_URI: Optional[str] = None
    MONGODB_DB_NAME: str = "fitsaathi"
    GOOGLE_PROJECT_ID: Optional[str] = None
    GOOGLE_LOCATION: str = "us-central1"
    GOOGLE_API_KEY: Optional[str] = None
    AGENT_ID: str = ""
    SECRET_KEY: Optional[str] = "dev-secret-key"
    ENVIRONMENT: str = "development"
    MAX_UPLOAD_SIZE_MB: int = 10
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:8080"
    
    # Virtual Try-On specific settings
    CATVTON_MODEL_PATH: Optional[str] = None
    TRYON_OUTPUT_DIR: str = "uploads/tryons"
    UPLOADS_USERS_DIR: str = "uploads/users"
    UPLOADS_GARMENTS_DIR: str = "uploads/garments"
    TRYON_TIMEOUT_SECONDS: int = 300

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
    
    def ensure_directories(self):
        """Ensure all necessary upload directories exist."""
        os.makedirs(self.TRYON_OUTPUT_DIR, exist_ok=True)
        os.makedirs(self.UPLOADS_USERS_DIR, exist_ok=True)
        os.makedirs(self.UPLOADS_GARMENTS_DIR, exist_ok=True)

settings = Settings()
