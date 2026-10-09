import os
from pydantic import BaseModel, Field

class Settings(BaseModel):
    PROJECT_NAME: str = "QUANTUM KAVACHA"
    VERSION: str = "2.0.0"
    API_PREFIX: str = "/api"
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000", "http://localhost:8000", "*"]
    
    # Quantum Hardware & Token
    IBM_QUANTUM_TOKEN: str = Field(default_factory=lambda: os.getenv("IBM_QUANTUM_TOKEN", ""))
    QUANTUM_MODE_DEFAULT: str = "SIMULATION" # SIMULATION, NOISY SIMULATION, or HARDWARE
    
    # Gemini Multimodal Evidence Verification
    GEMINI_API_KEY: str = Field(default_factory=lambda: os.getenv("GEMINI_API_KEY", ""))
    GEMINI_MODEL: str = Field(default_factory=lambda: os.getenv("GEMINI_MODEL", "gemini-1.5-flash"))

    # Threat Intelligence & VirusTotal (Adapted from threat feeds)
    VIRUSTOTAL_API_KEY: str = Field(default_factory=lambda: os.getenv("VIRUSTOTAL_API_KEY", os.getenv("VT_API_KEY", "")))
    VIRUSTOTAL_ENABLED: bool = Field(default_factory=lambda: bool(os.getenv("VIRUSTOTAL_API_KEY") or os.getenv("VT_API_KEY")))
    ENABLE_EXTERNAL_FILE_SUBMISSION: bool = False # Explicit consent required for external payload upload

    # Storage
    DATA_DIR: str = Field(default_factory=lambda: os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../data")))
    ARTIFACTS_DIR: str = Field(default_factory=lambda: os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../model_artifacts")))

settings = Settings()

