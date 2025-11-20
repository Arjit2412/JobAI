"""
AI Job Applier - Python Microservice
FastAPI service for job scraping and AI-powered job matching
"""

import os
import logging
from typing import List, Dict, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from dotenv import load_dotenv

from services.job_scraper import JobScraper
from services.ai_matcher import AIMatcher
from models.job import Job, ScoredJob
from models.requests import ScrapeJobsRequest, ScoreJobsRequest

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="AI Job Applier - Python Service",
    description="Microservice for job scraping and AI-powered job matching",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
job_scraper = JobScraper()
ai_matcher = AIMatcher()

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "service": "AI Job Applier Python Service",
        "status": "running",
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "services": {
            "job_scraper": "ready",
            "ai_matcher": "ready"
        },
        "environment": os.getenv("ENVIRONMENT", "development")
    }

@app.get("/scrape_jobs")
async def scrape_jobs(
    keyword: str,
    location: str = "",
    limit: int = 20
):
    """
    Scrape jobs from multiple sources (JSearch API, Indeed) based on keyword and location
    
    Args:
        keyword: Job search keyword (e.g., "software engineer")
        location: Job location (e.g., "San Francisco" or "Remote")
        limit: Maximum number of jobs to scrape (default: 20)
    
    Returns:
        Dictionary containing scraped jobs and metadata
    """
    try:
        logger.info(f"🔍 Starting job scrape: keyword='{keyword}', location='{location}', limit={limit}")
        
        if not keyword.strip():
            raise HTTPException(status_code=400, detail="Keyword is required")
        
        # Scrape jobs using the job scraper service
        jobs = await job_scraper.scrape_jobs(
            keyword=keyword.strip(),
            location=location.strip(),
            limit=min(limit, 50)  # Cap at 50 jobs
        )
        
        logger.info(f"✅ Successfully scraped {len(jobs)} jobs")
        
        return {
            "jobs": jobs,
            "count": len(jobs),
            "keyword": keyword,
            "location": location,
            "sources": ["jsearch", "indeed", "mock"]
        }
        
    except Exception as e:
        logger.error(f"❌ Job scraping failed: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Job scraping failed: {str(e)}"
        )

@app.post("/score_jobs")
async def score_jobs(request: ScoreJobsRequest):
    """
    Score jobs based on user profile using AI
    
    Args:
        request: ScoreJobsRequest containing resume_url, jobs, user_skills, user_experience
    
    Returns:
        Dictionary containing scored jobs with fit scores (0-100)
    """
    try:
        logger.info(f"🤖 Starting AI job scoring for {len(request.jobs)} jobs")
        
        if not request.jobs:
            raise HTTPException(status_code=400, detail="Jobs list is required")
        
        if not request.resume_url:
            raise HTTPException(status_code=400, detail="Resume URL is required")
        
        # Score jobs using AI matcher service
        scored_jobs = await ai_matcher.score_jobs(
            resume_url=request.resume_url,
            jobs=request.jobs,
            user_skills=request.user_skills or [],
            user_experience=request.user_experience or ""
        )
        
        # Sort by fit score (highest first)
        scored_jobs.sort(key=lambda job: job.fit_score, reverse=True)
        
        logger.info(f"✅ Successfully scored {len(scored_jobs)} jobs")
        
        # Convert to dict for JSON serialization
        scored_jobs_dict = [job.dict() for job in scored_jobs]
        
        return {
            "scored_jobs": scored_jobs_dict,
            "count": len(scored_jobs_dict),
            "average_score": sum(job.fit_score for job in scored_jobs) / len(scored_jobs) if scored_jobs else 0
        }
        
    except Exception as e:
        logger.error(f"❌ Job scoring failed: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Job scoring failed: {str(e)}"
        )

@app.post("/test_ai")
async def test_ai():
    """Test endpoint to verify AI service connectivity"""
    try:
        test_result = await ai_matcher.test_connection()
        return {"status": "success", "ai_service": test_result}
    except Exception as e:
        logger.error(f"❌ AI service test failed: {str(e)}")
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=port, 
        reload=True,
        log_level="info"
    )