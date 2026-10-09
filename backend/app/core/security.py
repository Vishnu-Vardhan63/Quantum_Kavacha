import os
from typing import Dict, Any

def validate_csv_file(filename: str, file_bytes: bytes, max_mb: int = 50) -> Dict[str, Any]:
    """
    Validates CSV upload: extension must be .csv, size <= max_mb, and no binary payload.
    """
    if not filename.lower().endswith(".csv"):
        return {"valid": False, "error": "Only .csv files are permitted."}
    
    size_mb = len(file_bytes) / (1024 * 1024)
    if size_mb > max_mb:
        return {"valid": False, "error": f"File size ({size_mb:.2f}MB) exceeds maximum limit of {max_mb}MB."}
    
    # Check for basic ASCII text / CSV structure
    try:
        sample = file_bytes[:1024].decode("utf-8")
        if "\0" in sample:
            return {"valid": False, "error": "Invalid file content: binary characters detected."}
    except UnicodeDecodeError:
        return {"valid": False, "error": "File decoding failed: must be UTF-8 encoded CSV text."}

    return {"valid": True, "size_mb": size_mb}
