"""
Request models for API endpoints
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, HttpUrl
from models.job import Job

class ScrapeJobsRequest(BaseModel):
    """Request model for job scraping endpoint"""
    keyword: str = Field(..., description="Job search keyword")
    location: Optional[str] = Field("", description="Job location")
    limit: int = Field(20, ge=1, le=50, description="Maximum number of jobs to scrape")

class ScoreJobsRequest(BaseModel):
    """Request model for job scoring endpoint"""
    resume_url: str = Field(..., description="URL to user's resume")
    jobs: List[Dict[str, Any]] = Field(..., description="List of jobs to score")
    user_skills: Optional[List[str]] = Field([], description="User's skills")
    user_experience: Optional[str] = Field("", description="User's experience summary")
    
    class Config:
        schema_extra = {
            "example": {
                "resume_url": "https://example.com/resume.pdf",
                "jobs": [
                    {
                        "title": "Software Engineer",
                        "company": "Tech Corp",
                        "description": "We are looking for a skilled software engineer...",
                        "location": "San Francisco, CA",
                        "source_url": "https://indeed.com/job/123"
                    }
                ],
                "user_skills": ["Python", "JavaScript", "React"],
                "user_experience": "5 years of software development experience"
            }
        }