# backend\utils.py
import re
import time
import json
from functools import wraps
from urllib.parse import urlparse
from .logger_config import logger
from typing import Any, Dict, Optional

def is_valid_url(url: str) -> bool:
    """Validate if the given string is a valid URL."""
    logger.info(f"Validating URL: {url}")
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False

def safe_write_json(data: Any, file_path: str) -> bool:
    """Safely write JSON data to a file."""
    logger.info(f"Writing JSON data to {file_path}")
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error writing JSON to {file_path}: {e}")
        return False

def safe_read_json(file_path: str) -> Optional[Dict[str, Any]]:
    """Safely read JSON data from a file."""
    logger.info(f"Reading JSON data from {file_path}")
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error reading JSON from {file_path}: {e}")
        return None

def retry_with_backoff(max_retries: int = 3, base_delay: float = 1.0):
    """Retry decorator with exponential backoff."""
    logger.info(f"Setting up retry decorator with max_retries={max_retries}, base_delay={base_delay}")
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        delay = base_delay * (2 ** attempt)
                        time.sleep(delay)
                        continue
                    else:
                        raise last_exception
            return None
        return wrapper
    return decorator

def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe file system operations."""
    logger.info(f"Sanitizing filename: {filename}")
    # Remove or replace unsafe characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Limit length
    if len(filename) > 100:
        filename = filename[:100]
    return filename

def truncate_text(text: str, max_length: int) -> str:
    """Truncate text to specified length, preserving word boundaries."""
    logger.info(f"Truncating text to max_length: {max_length}")
    if len(text) <= max_length:
        return text
    
    truncated = text[:max_length].rsplit(' ', 1)[0]
    return truncated + "..." if truncated != text[:max_length] else truncated
