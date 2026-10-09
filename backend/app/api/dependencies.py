from typing import Generator
import pandas as pd
import os
from backend.app.core.config import settings

def get_demo_dataset_path() -> str:
    return os.path.join(settings.DATA_DIR, "sample", "demo_transactions.csv")
