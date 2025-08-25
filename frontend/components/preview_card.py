# frontend/components/preview_card.py
import streamlit as st
from typing import Dict, Any, Optional
from PIL import Image
from frontend.logger import logger

BASE_API_URL = "http://127.0.0.1:8000"  # Update if backend runs elsewhere
LOG_PREFIX = "[preview_card.py]"

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
    
    # In the render_preview_card function
    with col2:
        # Image display
        st.write("**Generated Image:**")
        # Ensure the image path is a full URL
        image_path = variant.get("image_path", "")
        if not image_path.startswith("http"):
            # Prepend the base API URL if it's not already a full URL
            image_path = f"{BASE_API_URL}{image_path}"
        st.write(f"Loading image from: {image_path}")  # This will show the URL in the app
        # Now use the full URL
        st.image(image_path, caption="Generated Image")
        # Construct the API URL for the image
        if image_path and (image_path.startswith("http://") or image_path.startswith("https://")):
            api_url = image_path
        elif image_path and image_path.startswith("/api/"):
            # Convert relative API path to full URL
            api_url = f"{BASE_API_URL}{image_path}"
        else:
            # Fallback to constructing the URL manually
            api_url = f"{BASE_API_URL}/api/v1/images/{job_id}/{variant_id}.png"
        
        # Display the image using the API URL
        try:
            st.image(api_url, caption="Generated Image", use_column_width=True)
            logger.info(f"{LOG_PREFIX} render_preview_card: Variant {variant_id} image_path: {image_path} (type: {type(image_path)})")
        except Exception as e:
            st.error(f"Unable to load image: {e}")
            st.info("Image will be displayed when available")
            logger.error(f"Failed to load image for variant {variant_id}: {e}")
            
            # Use a placeholder image
            placeholder_img = create_placeholder_image(variant_id)
            st.image(placeholder_img, caption="Image will be generated", use_column_width=True)


            st.info("Image will be displayed when available")
            logger.info(f"ℹ️ Using placeholder image for variant {variant_id}")
            return variant
        else:
            try:
                st.image(api_url, caption="Generated Image", use_column_width=True)
            except Exception as e:
                st.error(f"Unable to load image: {e}")
                st.info("Image will be displayed when available")
                logger.error(f"Failed to load image for variant {variant_id}: {e}")
    
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
    
    logger.info(f"{LOG_PREFIX} render_preview_card: Rendering action buttons for variant {variant_id}, image_ready={image_ready}")
    logger.info(f"{LOG_PREFIX} render_preview_card: User edited text for variant {variant_id}: {edited_text[:50]}...")
    
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
