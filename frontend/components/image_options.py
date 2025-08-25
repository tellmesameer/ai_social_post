# frontend/components/image_options.py
import streamlit as st
from typing import Dict, Any

def render_image_options() -> Dict[str, Any]:
    """Render image options form and return selected options."""
    
    st.subheader("🎨 Image Generation Options")
    
    # Image style selection
    style = st.selectbox(
        "Image Style",
        options=["photographic", "illustrated", "flat", "abstract"],
        help="Choose the visual style for generated images"
    )
    
    # Aspect ratio selection
    aspect_ratio = st.selectbox(
        "Aspect Ratio",
        options=["16:9", "1:1", "4:3", "3:2"],
        help="Choose the aspect ratio for generated images"
    )
    
    # Negative prompt input
    negative_prompt = st.text_area(
        "Negative Prompts",
        value="no text, no logos, no watermarks, no signatures",
        help="Specify what should NOT appear in the generated images",
        max_chars=200
    )
    
    # Additional image settings
    with st.expander("Advanced Image Settings"):
        # Image quality
        quality = st.slider(
            "Image Quality",
            min_value=1,
            max_value=10,
            value=8,
            help="Higher values produce higher quality images (may take longer)"
        )
        
        # Number of images to generate per variant
        num_images = st.selectbox(
            "Images per Variant",
            options=[1, 2, 3],
            index=0,  # Changed from value=0 to index=0
            help="Number of images to generate for each post variant"
        )
    
    # Return the selected options
    return {
        "style": style,
        "aspect_ratio": aspect_ratio,
        "negative_prompt": negative_prompt,
        "quality": quality,
        "num_images": num_images
    }

def render_image_preview_style():
    """Render a preview of the selected image style."""
    
    st.caption("💡 **Style Preview:**")
    
    style_descriptions = {
        "photographic": "Realistic, photo-like images with natural lighting and textures",
        "illustrated": "Artistic, hand-drawn style with creative interpretations",
        "flat": "Minimalist, modern design with solid colors and simple shapes",
        "abstract": "Non-representational art with geometric patterns and colors"
    }
    
    selected_style = st.session_state.get("selected_style", "photographic")
    
    if selected_style in style_descriptions:
        st.info(f"**{selected_style.title()} Style:** {style_descriptions[selected_style]}")
    
    # Show example aspect ratios
    st.caption("📐 **Aspect Ratio Examples:**")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("16:9", "Landscape")
    with col2:
        st.metric("1:1", "Square")
    with col3:
        st.metric("4:3", "Traditional")
    with col4:
        st.metric("3:2", "Classic")

def get_default_image_options() -> Dict[str, Any]:
    """Get default image options."""
    return {
        "style": "photographic",
        "aspect_ratio": "16:9",
        "negative_prompt": "no text, no logos, no watermarks, no signatures",
        "quality": 8,
        "num_images": 1
    }