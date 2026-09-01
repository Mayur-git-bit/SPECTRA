"""
Phase 1 — Metadata Extractor
=============================
Wrapper to extract basic file information before parsing samples.
"""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

def get_file_metadata(path: Path) -> dict:
    """
    Extract basic metadata from a file without parsing its contents.
    """
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    ext = path.suffix.lower()
    
    # We strip the leading dot
    fmt = ext[1:].upper() if ext else "UNKNOWN"

    # Base file information
    return {
        "name": path.name,
        "format": fmt,
        "size_bytes": path.stat().st_size
    }
