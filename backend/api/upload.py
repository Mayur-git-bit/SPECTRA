"""
Upload API Endpoint
====================
Handles file ingestion for RAW IQ and WAV recordings.
"""

import logging
import uuid
import shutil
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status
from pydantic import BaseModel

from config import UPLOAD_DIR, MAX_UPLOAD_BYTES
from schemas.analysis import UploadResponse

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Upload"])

@router.post("/upload", response_model=UploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    iq_dtype: str = Form(None),
    sample_rate: float = Form(None)
):
    """
    Ingests an IQ or WAV file.
    
    Parameters:
    - file: The uploaded file
    - iq_dtype: (Optional) The sample format if RAW IQ (e.g., float32, int16).
    - sample_rate: (Optional) The sample rate in Hz if RAW IQ.
    """
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No filename provided")

    # Determine extension
    ext = Path(file.filename).suffix.lower()
    if ext not in [".iq", ".wav"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file extension: {ext}. Only .iq and .wav are supported."
        )

    # Generate a unique job ID
    job_id = str(uuid.uuid4())
    
    # Save the file to the upload directory
    file_path = UPLOAD_DIR / f"{job_id}{ext}"
    
    try:
        # Save uploaded file
        bytes_written = 0
        with open(file_path, "wb") as buffer:
            # Chunked writing to handle large files
            shutil.copyfileobj(file.file, buffer)
            
        file_size = file_path.stat().st_size
        
        if file_size == 0:
            file_path.unlink()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty")
            
        if file_size > MAX_UPLOAD_BYTES:
            file_path.unlink()
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File exceeds maximum allowed size of {MAX_UPLOAD_BYTES / (1024*1024):.1f} MB"
            )

        logger.info(
            "[PHASE 1] File uploaded successfully: %s -> %s (size: %d bytes)",
            file.filename, file_path.name, file_size
        )

        return UploadResponse(
            job_id=job_id,
            filename=file.filename,
            size_bytes=file_size,
            message="File uploaded successfully and assigned to a job."
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during file upload: {e}")
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error during upload")
