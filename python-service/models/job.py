"""
Job-related Pydantic models for data validation and serialization
"""

from typing import Optional, List
from pydantic import BaseModel, Field

class Job(BaseModel):
    """Base job model for scraped job data"""
    title: str = Field(..., description="Job title")
    company: str = Field(..., description="Company name")
    description: str = Field(..., description="Job description")
    location: Optional[str] = Field(None, description="Job location")
    source_url: Optional[str] = Field(None, description="Original job posting URL")
    
    class Config:
        json_encoders = {
            # Add custom encoders if needed
        }

class ScoredJob(Job):
    """Extended job model with AI fit score"""
    fit_score: int = Field(..., description="AI-generated fit score (0-100)")
    score_explanation: Optional[str] = Field(None, description="Explanation for the fit score")
    
    class Config:
        json_encoders = {
            # Add custom encoders if needed
        }

class JobSearchCriteria(BaseModel):
    """Model for job search parameters"""
    keyword: str = Field(..., description="Search keyword")
    location: Optional[str] = Field("", description="Job location")
    limit: int = Field(20, ge=1, le=50, description="Maximum number of jobs to return")