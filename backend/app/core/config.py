import os
from pydantic import BaseModel, Field

try:
    from dotenv import load_dotenv
    env_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.env"))
    if os.path.exists(env_file):
        load_dotenv(env_file)
except ImportError:
    pass

class Settings(BaseModel):
    PROJECT_NAME: str = "QUANTUM KAVACHA"
    VERSION: str = "2.0.0"
    API_PREFIX: str = "/api"
    CORS_ORIGINS: list[str] = [
        "https://quantum-kavacha.netlify.app",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://localhost:8000",
        "*"
    ]
    
    # MongoDB Atlas Database Configuration
    MONGODB_URI: str = Field(default_factory=lambda: os.getenv("MONGODB_URI", ""))
    MONGODB_DATABASE: str = Field(default_factory=lambda: os.getenv("MONGODB_DATABASE", "quantum_kavacha"))

    # Quantum Hardware & Token
    IBM_QUANTUM_TOKEN: str = Field(default_factory=lambda: os.getenv("IBM_QUANTUM_TOKEN", ""))
    QUANTUM_MODE_DEFAULT: str = "SIMULATION" # SIMULATION, NOISY SIMULATION, or HARDWARE
    
    # Groq Conversational AI Copilot
    GROQ_API_KEY: str = Field(default_factory=lambda: os.getenv("GROQ_API_KEY", ""))
    GROQ_MODEL: str = Field(default_factory=lambda: os.getenv("GROQ_MODEL", "qwen/qwen3.8-27b"))

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

