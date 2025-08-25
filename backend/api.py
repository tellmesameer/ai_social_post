# backend\api.py
import os
import asyncio
from fastapi import HTTPException, BackgroundTasks, Depends
from sqlmodel import Session, select
from .models import (
    CreatePostRequest,
    CreatePostResponse,
    RegenerateRequest,
    PublishRequest,
    PublishResponse,
    JobStatusResponse,
)
from .config import settings
from .providers import provider

from .models import Job, get_session
from .services import create_job, run_job, regenerate_content, publish_to_linkedin

from .storage import get_job_files
from fastapi.responses import FileResponse
from fastapi import APIRouter, Path
from .logger_config import logger


# Create API router
from fastapi import APIRouter

app = APIRouter()

# Serve image files by job_id and variant (A/B)
@app.get("/images/{job_id}/{variant}.png")
async def get_image(job_id: str = Path(...), variant: str = Path(...)):
    """Serve generated image files by job_id and variant (A/B)."""
    logger.info(f"Fetching image for job_id={job_id}, variant={variant}")
    
    # Construct the correct file system path
    from pathlib import Path
    image_path = Path(f"./tmp/{job_id}/images/{variant}.png")
    
    if not image_path.exists():
        logger.error(f"Image not found at {image_path}")
        raise HTTPException(status_code=404, detail="Image not found")
    
    logger.info(f"Serving image from {image_path}")
    return FileResponse(str(image_path), media_type="image/png")



@app.post("/posts", response_model=CreatePostResponse)
async def create_post(
    request: CreatePostRequest,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session)
):
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
        logger.info(f"Created post job {job_id}")
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
                        logger.error(f"Result file is empty for job {job_id}")
                except Exception as e:
                    logger.error(f"Failed to read result file for job {job_id}: {e}")
                    result_error = f"Failed to read result file: {e}"
            else:
                result_error = "Job files not found"
                logger.error(f"Job files not found for job {job_id}")
        else:
            result_error = "Job not completed"
            logger.error(f"Job {job_id} is not completed yet")
        
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
        
        logger.info(f"Regenerating {request.regenerate} for variant {request.variant} in job {job_id}")
        
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
            logger.info(f"Successfully published variant {request.variant} for job {job_id}")
            return PublishResponse(
                job_id=job_id,
                published=True,
                linkedin_post_id=result["linkedin_post_id"]
            )
        else:
            logger.error(f"Failed to publish variant {request.variant} for job {job_id}: {result.get('error')}")
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