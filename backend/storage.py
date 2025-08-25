# backend\storage.py
import shutil
from pathlib import Path
from .logger_config import logger
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from .config import settings
from .utils import safe_write_json, safe_read_json
from .logger_config import logger


def ensure_job_dir(job_id: str) -> Path:
    """Ensure job directory exists and return path."""
    logger.info(f"Ensuring job directory for job_id: {job_id}")
    job_dir = settings.tmp_dir / job_id
    job_dir.mkdir(parents=True, exist_ok=True)
    
    # Create subdirectories
    (job_dir / "images").mkdir(exist_ok=True)
    
    return job_dir


async def save_json(data: Dict[str, Any], file_path: Path) -> bool:
    """Save JSON data to file."""
    return safe_write_json(data, str(file_path))


def read_json(file_path: Path) -> Optional[Dict[str, Any]]:
    """Read JSON data from file."""
    return safe_read_json(str(file_path))


async def save_image(image_data: bytes, file_path: Path) -> bool:
    """Save image data to file."""
    logger.info(f"Saving image to {file_path}")
    try:
        with open(file_path, 'wb') as f:
            f.write(image_data)
        return True
    except Exception as e:
        logger.error(f"Error saving image to {file_path}: {e}")
        return False


def cleanup_tmp(max_age_hours: int = 24) -> None:
    """Clean up temporary job directories older than specified hours."""
    logger.info(f"Cleaning up temporary files older than {max_age_hours} hours")
    if not settings.tmp_dir.exists():
        return
    
    cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
    cleaned_count = 0
    
    for job_dir in settings.tmp_dir.iterdir():
        if not job_dir.is_dir():
            continue
            
        try:
            # Check if directory is old enough to clean
            dir_time = datetime.fromtimestamp(job_dir.stat().st_mtime)
            if dir_time < cutoff_time:
                shutil.rmtree(job_dir)
                cleaned_count += 1
                logger.info(f"Cleaned up old job directory: {job_dir}")
        except Exception as e:
            logger.error(f"Error cleaning up directory {job_dir}: {e}")
    
    if cleaned_count > 0:
        logger.info(f"Cleaned up {cleaned_count} old job directories")


def get_job_files(job_id: str) -> Dict[str, Any]:
    """Get all file paths for a job."""
    logger.info(f"Retrieving file paths for job_id: {job_id}")
    job_dir = settings.tmp_dir / job_id
    if not job_dir.exists():
        return {}
    
    return {
        "scrape": job_dir / "scrape.json",
        "summary": job_dir / "summary.txt",
        "result": job_dir / "result.json",
        "images": {
            "A": job_dir / "images" / "A.png",
            "B": job_dir / "images" / "B.png"
        }
    }


def job_exists(job_id: str) -> bool:
    """Check if job directory exists."""
    return (settings.tmp_dir / job_id).exists()


def delete_job(job_id: str) -> bool:
    """Delete a job directory and all its contents."""
    logger.info(f"Deleting job directory for job_id: {job_id}")
    job_dir = settings.tmp_dir / job_id
    if job_dir.exists():
        try:
            shutil.rmtree(job_dir)
            logger.info(f"Deleted job directory: {job_dir}")
            return True
        except Exception as e:
            logger.error(f"Error deleting job directory {job_dir}: {e}")
            return False
    return False
