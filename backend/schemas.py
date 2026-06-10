"""
Pydantic schemas for Virtual Try-On module.
Defines request/response models for API endpoints.
"""
from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum

# =============================================================================
# ENUMERATIONS
# =============================================================================
class TryOnJobStatus(str, Enum):
    """Status of a virtual try-on job."""
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


# =============================================================================
# REQUEST SCHEMAS
# =============================================================================
class TryOnGenerateRequest(BaseModel):
    """Request schema for generating a virtual try-on."""
    user_id: str = Field(..., description="Unique ID of the user requesting the try-on")
    item_id: str = Field(..., description="Unique ID of the clothing item to try on")


# =============================================================================
# RESPONSE SCHEMAS
# =============================================================================
class TryOnGenerateResponse(BaseModel):
    """Response schema for initiating a virtual try-on job."""
    job_id: str = Field(..., description="Unique ID of the try-on job for tracking")
    status: TryOnJobStatus = Field(TryOnJobStatus.PROCESSING, description="Current status of the job")


class TryOnResultResponse(BaseModel):
    """Response schema for getting the result of a virtual try-on job."""
    job_id: str = Field(..., description="Unique ID of the try-on job")
    status: TryOnJobStatus = Field(..., description="Current status of the job")
    generated_image: Optional[str] = Field(None, description="URL/path to the generated try-on image (only if completed)")
    error_message: Optional[str] = Field(None, description="Error details if job failed")
    processing_time_seconds: Optional[float] = Field(None, description="Time taken to generate the try-on")
