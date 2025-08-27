# backend\api.py

# Standard library imports
import os
import asyncio
from pathlib import Path

# Third-party imports
from fastapi import (APIRouter, BackgroundTasks, Depends, HTTPException, Path as FastAPIPath, status)
from fastapi.responses import FileResponse
from sqlmodel import Session, select

# Local application imports
from .config import settings
from .logger_config import logger
from .models import (CreatePostRequest, CreatePostResponse, Job, JobStatusResponse, PublishRequest, PublishResponse, RegenerateRequest, get_session)
from .providers import provider
from .services import (create_job, publish_to_linkedin, regenerate_content, run_job)
from .storage import get_job_files

# Create API router
app = APIRouter()

# Add a helper for consistent log prefix
LOG_PREFIX = "[api.py]"

# Add cancel endpoint to router (APIRouter)
@app.post("/posts/{job_id}/cancel", status_code=status.HTTP_200_OK)
async def cancel_post(job_id: str, session: Session = Depends(get_session)):
    logger.info(f"{LOG_PREFIX} cancel_post: Received cancel request for job_id={job_id}")
    """Cancel a running or queued job."""
    logger.info(f"Received cancel request for job_id={job_id}")
    try:
        job = session.exec(select(Job).where(Job.job_id == job_id)).first()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        if job.status not in ["queued", "in_progress"]:
            raise HTTPException(status_code=400, detail="Job cannot be cancelled in its current state")
        job.status = "cancelled"
        session.commit()
        logger.info(f"{LOG_PREFIX} cancel_post: Job {job_id} cancelled successfully")
        return {"job_id": job_id, "status": "cancelled"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel job {job_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Serve image files by job_id and variant (A/B)
@app.get("/api/v1/images/{job_id}/{variant}.png") # Ensure the full path is defined in the decorator
async def serve_image(
    job_id: str = FastAPIPath(..., description="Job ID"),
    variant: str = FastAPIPath(..., description="Variant (A or B)")
):
    logger.info(f"{LOG_PREFIX} serve_image: called for job_id={job_id}, variant={variant}")
    """Serve generated image files by job_id and variant (A/B)."""
    logger.info(f"serve_image called for job_id={job_id}, variant={variant}")
    logger.info(f"{LOG_PREFIX} serve_image: Configured settings.base_dir: {settings.base_dir}")
    
    try:
        # Construct the full path to the image file
        image_path = settings.base_dir / "tmp" / job_id / "images" / f"{variant}.png"
        logger.info(f"{LOG_PREFIX} serve_image: Constructed full image_path: {image_path}")
        
        # Check if the file actually exists
        if not image_path.exists():
            logger.error(f"Image file not found on disk at: {image_path}")
            raise HTTPException(status_code=404, detail=f"Image not found at {image_path}")
        
        # Check if it's actually a file (not a directory)
        if not image_path.is_file():
            logger.error(f"Path exists but is not a file: {image_path}")
            raise HTTPException(status_code=500, detail=f"Path is not a file: {image_path}")

        logger.info(f"{LOG_PREFIX} serve_image: Serving image from: {image_path}")
        # Return the file response
        return FileResponse(path=str(image_path), media_type="image/png", filename=f"{variant}.png")
        
    except HTTPException:
        # Re-raise HTTPExceptions (like 404)
        raise
    except Exception as e:
        # Catch any other unexpected errors during path handling or FileResponse creation
        logger.exception(f"Unexpected error serving image for job_id={job_id}, variant={variant}: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error while serving image: {str(e)}")


@app.post("/posts", response_model=CreatePostResponse)
async def create_post(
    request: CreatePostRequest,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session)
):
    logger.info(f"{LOG_PREFIX} create_post: Received create_post request: {request}")
    """Create a new post generation job."""
    logger.info(f"Received create_post request: {request}")
    try:
        # Create the job
        job_id =await create_job(
            url=request.url,
            opinion=request.opinion,
            tone=request.tone,
            image_options=request.image_options
        )
        
        # Schedule the job to run in background (async)
        asyncio.create_task(run_job(job_id))
        logger.info(f"{LOG_PREFIX} create_post: Created post job {job_id}")
        return CreatePostResponse(
            job_id=job_id,
            status="queued"
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create post job: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

        
@app.get("/posts/{job_id}", response_model=JobStatusResponse)
async def get_post_status(job_id: str, session: Session = Depends(get_session)):
    logger.info(f"{LOG_PREFIX} get_post_status: Fetching status for job_id={job_id}")
    """Get the status and result of a post generation job."""
    logger.info(f"Fetching status for job_id={job_id}")
    try:
        # Get job from database
        job = session.exec(select(Job).where(Job.job_id == job_id)).first()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        result = {}
        result_error = None
        
        # If job is completed, include the result
        if job.status == "completed":
            job_files = get_job_files(job_id)
            if job_files and "result" in job_files:
                try:
                    # Use the storage helper to read the JSON result
                    from .storage import read_json
                    result = read_json(job_files["result"])
                    
                    # Patch image_path in post_variants to be API URLs
                    if result and "post_variants" in result:
                        for variant in result["post_variants"]:
                            variant_id = variant.get("id")
                            if variant_id:
                                # Ensure the image path is an API URL, not a file path
                                variant["image_path"] = f"/api/v1/images/{job_id}/{variant_id}.png"
                    
                    if not result:
                        result_error = "Result file is empty"
                        logger.error(f"{LOG_PREFIX} get_post_status: Result file is empty for job {job_id}")
                except Exception as e:
                    logger.error(f"{LOG_PREFIX} get_post_status: Failed to read result file for job {job_id}: {e}")
                    result_error = f"Failed to read result file: {e}"
            else:
                result_error = "Job files not found"
                logger.error(f"{LOG_PREFIX} get_post_status: Job files not found for job {job_id}")
        else:
            result_error = "Job not completed"
            logger.error(f"{LOG_PREFIX} get_post_status: Job {job_id} is not completed yet")
        
        response = JobStatusResponse(
            job_id=job_id,
            status=job.status if job else "",
            error=job.error if job and job.error is not None else "",  # Convert None to empty string
            result=result
        )
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get job status for {job_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
        

@app.post("/posts/{job_id}/regenerate", response_model=CreatePostResponse)
async def regenerate_post(
    job_id: str,
    request: RegenerateRequest,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session)
):
    logger.info(f"{LOG_PREFIX} regenerate_post: Received regenerate request for job_id={job_id}, type={request.regenerate}, variant={request.variant}")
    """Regenerate specific content for a post variant."""
    logger.info(f"Received regenerate request for job_id={job_id}, type={request.regenerate}, variant={request.variant}")
    try:
        # Validate regenerate type
        if request.regenerate not in ["text", "image", "both"]:
            raise HTTPException(status_code=400, detail="Invalid regenerate type")
        
        # Validate variant
        if request.variant not in ["A", "B"]:
            raise HTTPException(status_code=400, detail="Invalid variant")
        
        # Check if job exists and is completed
        job = session.exec(select(Job).where(Job.job_id == job_id)).first()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        if job.status != "completed":
            raise HTTPException(status_code=400, detail="Job must be completed to regenerate content")
        
        # Update job status to in_progress
        job.status = "in_progress"
        session.commit()
    
        # Schedule regeneration in background (async)
        asyncio.create_task(regenerate_content(job_id, request.regenerate, request.variant))
        # Update job status back to completed after regeneration
        background_tasks.add_task(lambda: update_job_status(session, job_id, "completed"))
        
        logger.info(f"{LOG_PREFIX} regenerate_post: Regenerating {request.regenerate} for variant {request.variant} in job {job_id}")
        
        return CreatePostResponse(
            job_id=job_id,
            status="in_progress"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to regenerate content for job {job_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/posts/{job_id}/publish", response_model=PublishResponse)
async def publish_post(
    job_id: str,
    request: PublishRequest,
    session: Session = Depends(get_session)
):
    logger.info(f"{LOG_PREFIX} publish_post: Received publish request for job_id={job_id}, variant={request.variant}, user_id={request.user_id}")
    """Publish a post variant to LinkedIn."""
    logger.info(f"Received publish request for job_id={job_id}, variant={request.variant}, user_id={request.user_id}")
    try:
        # Validate variant
        if request.variant not in ["A", "B"]:
            raise HTTPException(status_code=400, detail="Invalid variant")
        
        # Check if job exists and is completed
        job = session.exec(select(Job).where(Job.job_id == job_id)).first()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        if job.status != "completed":
            raise HTTPException(status_code=400, detail="Job must be completed to publish")
        
        # Publish to LinkedIn
        result = publish_to_linkedin(job_id, request.variant, request.user_id)
        
        if result["published"]:
            logger.info(f"{LOG_PREFIX} publish_post: Successfully published variant {request.variant} for job {job_id}")
            return PublishResponse(
                job_id=job_id,
                published=True,
                linkedin_post_id=result["linkedin_post_id"]
            )
        else:
            logger.error(f"{LOG_PREFIX} publish_post: Failed to publish variant {request.variant} for job {job_id}: {result.get('error')}")
            return PublishResponse(
                job_id=job_id,
                published=False,
                error=result.get("error", "Unknown error")
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to publish post for job {job_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/health")
async def health_check():
    logger.info(f"{LOG_PREFIX} health_check: Health check requested")
    """Health check endpoint."""
    logger.info("Health check requested")
    return {"status": "healthy", "service": "AI Social Post Generator"}


def update_job_status(session: Session, job_id: str, status: str):
    """Helper function to update job status."""
    logger.info(f"Updating job {job_id} status to {status}")
    try:
        job = session.exec(select(Job).where(Job.job_id == job_id)).first()
        if job:
            job.status = status
            session.commit()
    except Exception as e:
        logger.error(f"Failed to update job status for {job_id}: {e}")

# Root endpoint
@app.get("/")
async def root():
    logger.info(f"{LOG_PREFIX} root: Root endpoint accessed")
    """Root endpoint with API information."""
    logger.info("Root endpoint accessed")
    return {
        "message": "AI Social Post Generator API",
        "version": "1.0.0",
        "endpoints": {
            "create_post": "POST /posts",
            "get_status": "GET /posts/{job_id}",
            "regenerate": "POST /posts/{job_id}/regenerate",
            "publish": "POST /posts/{job_id}/publish",
            "health": "GET /health"
        }
    }

@app.get("/test-config")
async def test_config():
    logger.info(f"{LOG_PREFIX} test_config: Configuration test endpoint accessed")
    """Test endpoint to verify configuration is loaded correctly."""
    logger.info("Configuration test endpoint accessed")
    return {
        "google_api_key_loaded": bool(settings.google_api_key),
        "google_api_key_preview": settings.google_api_key[:10] + "..." if settings.google_api_key else None,
        "env_file_path": settings.Config.env_file,
        "working_directory": os.getcwd()
    }


@app.get("/test-vertex-ai")
async def test_vertex_ai():
    """Test endpoint to verify Vertex AI is working."""
    try:
        # Simple test prompt
        test_prompt = "Hello, please respond with just the word 'SUCCESS' else tell me capital of France."
        # Use the provider instance (ProviderAdapter) which abstracts Google/OpenAI/dev stub
        response = provider.generate_text(
            prompt=test_prompt,
            max_tokens=10,
            temperature=0.1
        )

        return {"status": "ok", "response": response}

    except Exception as e:
        return {"status": "error", "message": str(e)}