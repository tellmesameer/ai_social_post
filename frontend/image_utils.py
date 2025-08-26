# frontend/image_utils.py
import streamlit as st
import time
from pathlib import Path
from typing import Optional
from PIL import Image, ImageDraw, ImageFont
from config import TMP_DIR

def get_image_path(job_id: str, variant: str) -> Path:
    """Get the local path to an image file."""
    return TMP_DIR / job_id / "images" / f"{variant}.png"

def image_exists(job_id: str, variant: str) -> bool:
    """Check if an image file exists."""
    image_path = get_image_path(job_id, variant)
    return image_path.exists() and image_path.is_file()

def load_image(job_id: str, variant: str) -> Optional[Image.Image]:
    """Load an image from the local filesystem."""
    try:
        image_path = get_image_path(job_id, variant)
        if image_path.exists():
            return Image.open(image_path)
        return None
    except Exception as e:
        st.error(f"Error loading image: {e}")
        return None

def create_animated_placeholder(variant_id: str, status: str = "Generating...") -> Image.Image:
    """Create an animated placeholder image."""
    img = Image.new('RGB', (400, 250), color='#f0f0f0')
    draw = ImageDraw.Draw(img)
    
    try:
        font = ImageFont.load_default()
    except:
        font = None
    
    # Draw rounded rectangle
    draw.rounded_rectangle([10, 10, 390, 240], radius=10, outline='#1f77b4', width=3)
    
    # Draw variant ID
    draw.text((200, 80), f"Variant {variant_id}", fill='#1f77b4', anchor="mm", font=font)
    
    # Draw status with loading dots
    dots = "." * ((int(time.time()) % 3) + 1)
    draw.text((200, 120), f"{status}{dots}", fill='#666666', anchor="mm", font=font)
    
    # Draw progress bar
    bar_width = 200
    bar_height = 10
    bar_x = 100
    bar_y = 160
    progress = (int(time.time()) % 100) / 100
    
    # Background bar
    draw.rectangle([bar_x, bar_y, bar_x + bar_width, bar_y + bar_height], fill='#e9ecef')
    # Progress bar
    draw.rectangle([bar_x, bar_y, bar_x + int(bar_width * progress), bar_y + bar_height], fill='#1f77b4')
    
    return img

def create_placeholder_image(variant_id: str, status: str = "Generating...") -> Image.Image:
    """Create a placeholder image with status text."""
    img = Image.new('RGB', (300, 200), color='#f0f0f0')
    draw = ImageDraw.Draw(img)
    
    try:
        font = ImageFont.load_default()
    except:
        font = None
    
    draw.rectangle([20, 20, 280, 180], outline='#666666', width=3)
    draw.text((150, 80), f"Variant {variant_id}", fill='#666666', anchor="mm", font=font)
    draw.text((150, 120), status, fill='#666666', anchor="mm", font=font)
    
    return img