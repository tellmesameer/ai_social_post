# backend\models.py
import json
from datetime import datetime
from .config import settings
from pydantic import BaseModel
from typing import Optional, Dict, Any
from .logger_config import logger

from sqlmodel import SQLModel, Field, create_engine, Session

# Pydantic models for API requests/responses
class CreatePostRequest(BaseModel):
    url: str
    opinion: str
    tone: str
    image_options: Dict[str, Any]

class CreatePostResponse(BaseModel):
    job_id: str
    status: str

class RegenerateRequest(BaseModel):
    regenerate: str  # "text", "image", or "both"
    variant: str     # "A" or "B"

class PublishRequest(BaseModel):
    variant: str
    user_id: str

class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class PublishResponse(BaseModel):
    job_id: str
    published: bool
    linkedin_post_id: Optional[str] = None
    error: Optional[str] = None






class Job(SQLModel, table=True):
    """Job model for storing post generation requests."""
    id: Optional[int] = Field(default=None, primary_key=True)
    job_id: str = Field(unique=True, index=True)
    url: str
    opinion: str
    tone: str
    image_options: str  # JSON string
    status: str = Field(default="queued")  # queued, in_progress, completed, failed
    result_path: Optional[str] = None
    error: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    def get_image_options(self) -> Dict[str, Any]:
        """Parse image_options JSON string to dict."""
        logger.info(f"Parsing image options for job {self.job_id}")
        try:
            return json.loads(self.image_options)
        except (json.JSONDecodeError, TypeError):
            return {}
    
    def set_image_options(self, options: Dict[str, Any]) -> None:
        logger.info(f"Setting image options for job {self.job_id}")
        """Set image_options as JSON string."""
        self.image_options = json.dumps(options)

# Database engine
engine = create_engine(settings.database_url, echo=settings.debug)

def create_db_and_tables():
    """Create database and tables."""
    logger.info("Creating database and tables...")
    SQLModel.metadata.create_all(engine)

def get_session():
    """Get database session."""
    logger.info("Creating new database session")
    with Session(engine) as session:
        yield session
