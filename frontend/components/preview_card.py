# frontend/components/preview_card.py
import streamlit as st
from typing import Dict, Any, Optional
from PIL import Image


def render_preview_card(
    variant: Dict[str, Any], 
    job_id: str, 
    api_client,
    on_regenerate_text=None,
    on_regenerate_image=None,
    on_publish=None
):
    """Render a preview card for a post variant."""
    
    variant_id = variant.get("id", "Unknown")
    
    st.subheader(f"📝 Variant {variant_id}")
    
    # Create columns for layout
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Post text (editable)
        st.write("**Post Text:**")
        edited_text = st.text_area(
            f"text_{variant_id}",
            value=variant.get("text", ""),
            height=150,
            key=f"text_edit_{variant_id}",
            help="Edit the post text as needed"
        )
        
        # Hashtags
        st.write("**Hashtags:**")
        hashtags = variant.get("hashtags", [])
        hashtag_display = " ".join(hashtags) if hashtags else "No hashtags"
        st.info(hashtag_display)
        
        # Suggested comment
        st.write("**Suggested Comment:**")
        suggested_comment = variant.get("suggested_comment", "")
        st.success(suggested_comment if suggested_comment else "No comment suggested")
        
        # Alt text
        st.write("**Image Alt Text:**")
        alt_text = variant.get("alt_text", "")
        st.caption(alt_text if alt_text else "No alt text provided")
    
    with col2:
        # Image display
        st.write("**Generated Image:**")
        
        # Get image path from variant
        image_path = variant.get("image_path")
        
        # If image_path is a URL (starts with /api/ or http), use it directly
        if isinstance(image_path, str) and (image_path.startswith("/api/") or image_path.startswith("http")):
            st.image(image_path, caption="Generated Image", use_column_width=True)
        # If image_path is a file path, convert to API URL
        elif isinstance(image_path, str) and not image_path.startswith("/api/"):
            # Convert file path to API URL
            api_url = f"/api/v1/images/{job_id}/{variant_id}.png"
            st.image(api_url, caption="Generated Image", use_column_width=True)
        # If image_data is bytes, display directly
        elif isinstance(image_path, bytes):
            st.image(image_path, caption="Generated Image", use_column_width=True)
        # If image_path is a file path as a Path object
        elif hasattr(image_path, 'exists') and callable(image_path.exists):
            if image_path.exists():
                try:
                    with open(image_path, "rb") as f:
                        img_bytes = f.read()
                    st.image(img_bytes, caption="Generated Image", use_column_width=True)
                except Exception as e:
                    st.error(f"Unable to load image from path: {e}")
            else:
                # Try API URL as fallback
                api_url = f"/api/v1/images/{job_id}/{variant_id}.png"
                st.image(api_url, caption="Generated Image", use_column_width=True)
        else:
            # Try API URL as fallback
            api_url = f"/api/v1/images/{job_id}/{variant_id}.png"
            st.image(api_url, caption="Generated Image", use_column_width=True)
    
    # Action buttons
    st.write("**Actions:**")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button(f"🔄 Regenerate Text", key=f"regen_text_{variant_id}"):
            if on_regenerate_text:
                on_regenerate_text(job_id, "text", variant_id)
            else:
                st.info("Text regeneration requested")
    
    with col2:
        if st.button(f"🎨 Regenerate Image", key=f"regen_image_{variant_id}"):
            if on_regenerate_image:
                on_regenerate_image(job_id, "image", variant_id)
            else:
                st.info("Image regeneration requested")
    
    with col3:
        if st.button(f"📤 Publish to LinkedIn", key=f"publish_{variant_id}", type="primary"):
            if on_publish:
                on_publish(job_id, variant_id)
            else:
                st.info("Publish requested")
    
    # Update variant data with edited text
    variant["text"] = edited_text
    
    return variant



def create_placeholder_image(variant_id: str) -> Image.Image:
    """Create a placeholder image for development."""
    from PIL import Image, ImageDraw, ImageFont
    
    # Create a 300x200 placeholder image
    img = Image.new('RGB', (300, 200), color='#f0f0f0')
    draw = ImageDraw.Draw(img)
    
    # Draw a simple placeholder
    draw.rectangle([20, 20, 280, 180], outline='#666666', width=3)
    
    # Add text
    try:
        # Try to use a default font
        font = ImageFont.load_default()
    except:
        font = None
    
    # Draw variant ID
    draw.text((150, 80), f"Variant {variant_id}", fill='#666666', anchor="mm", font=font)
    draw.text((150, 120), "AI Generated", fill='#666666', anchor="mm", font=font)
    
    return img

def render_provenance_info(provenance: Dict[str, Any]):
    """Render provenance information about the source article."""
    if not provenance:
        return
    
    st.subheader("📚 Source Information")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.write("**Article Title:**")
        title = provenance.get("title", "No title available")
        st.info(title)
        
        st.write("**Source URL:**")
        source_url = provenance.get("source_url", "")
        if source_url:
            st.markdown(f"[{source_url}]({source_url})")
        else:
            st.info("No source URL available")
    
    with col2:
        st.write("**Excerpt:**")
        excerpt = provenance.get("excerpt", "No excerpt available")
        st.caption(excerpt[:100] + "..." if len(excerpt) > 100 else excerpt)

def render_moderation_status(moderation: Dict[str, Any]):
    """Render content moderation status and warnings."""
    if not moderation:
        return
    
    status = moderation.get("status", "unknown")
    
    if status == "pass":
        st.success("✅ Content Moderation: PASSED")
    elif status == "review":
        st.warning("⚠️ Content Moderation: NEEDS REVIEW")
        if "notes" in moderation and moderation["notes"]:
            st.write("**Moderation Notes:**")
            for note in moderation["notes"]:
                st.info(f"• {note}")
    elif status == "reject":
        st.error("❌ Content Moderation: REJECTED")
        if "notes" in moderation and moderation["notes"]:
            st.write("**Rejection Reasons:**")
            for note in moderation["notes"]:
                st.error(f"• {note}")
    
    # Show variant-specific moderation
    if "variants" in moderation:
        st.write("**Variant Moderation:**")
        for variant_mod in moderation["variants"]:
            variant_id = variant_mod.get("variant_id", "Unknown")
            variant_status = variant_mod.get("status", "unknown")
            
            if variant_status == "pass":
                st.success(f"Variant {variant_id}: ✅ PASSED")
            elif variant_status == "review":
                st.warning(f"Variant {variant_id}: ⚠️ REVIEW")
            elif variant_status == "reject":
                st.error(f"Variant {variant_id}: ❌ REJECTED")

def render_job_status(job_status: str, error: Optional[str] = None):
    """Render job status information."""
    st.subheader("📊 Job Status")
    
    if job_status == "queued":
        st.info("🔄 Job is queued and waiting to start")
    elif job_status == "in_progress":
        st.info("⚙️ Job is currently processing")
        with st.spinner("Generating your social post..."):
            st.progress(0.5)
    elif job_status == "completed":
        st.success("✅ Job completed successfully!")
    elif job_status == "failed":
        st.error("❌ Job failed")
        if error:
            st.error(f"Error: {error}")
    else:
        st.info(f"Status: {job_status}")

def render_provider_info(providers: Dict[str, Any]):
    """Render information about which AI providers were used."""
    if not providers:
        return
    
    st.subheader("🤖 AI Provider Information")
    
    col1, col2 = st.columns(2)
    
    with col1:
        text_provider = providers.get("text", "Unknown")
        st.write(f"**Text Generation:** {text_provider}")
    
    with col2:
        image_provider = providers.get("image", "Unknown")
        st.write(f"**Image Generation:** {image_provider}")
    
    # Show provider status
    if "dev_stub" in str(providers).lower():
        st.info("ℹ️ Using development stubs - no real AI calls made")
    else:
        st.success("✅ Using production AI providers")
