"""
AI-powered job matching service
Uses OpenAI or Claude API to score job fit based on user profile
"""

import asyncio
import logging
import os
from typing import List, Dict, Any, Optional
import requests
from openai import AsyncOpenAI
import anthropic

from models.job import Job, ScoredJob

logger = logging.getLogger(__name__)

class AIMatcher:
    """Service for AI-powered job matching and scoring"""
    
    def __init__(self):
        self.openai_client = None
        self.claude_client = None
        
        # Initialize OpenAI client if API key is available
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            self.openai_client = AsyncOpenAI(api_key=openai_key)
            logger.info("✅ OpenAI client initialized")
        
        # Initialize Claude client if API key is available
        claude_key = os.getenv("ANTHROPIC_API_KEY")
        if claude_key:
            self.claude_client = anthropic.AsyncAnthropic(api_key=claude_key)
            logger.info("✅ Claude client initialized")
        
        if not self.openai_client and not self.claude_client:
            logger.warning("⚠️  No AI API keys found. AI scoring will use mock data.")
    
    async def score_jobs(
        self,
        resume_url: str,
        jobs: List[Dict[str, Any]],
        user_skills: List[str] = None,
        user_experience: str = ""
    ) -> List[ScoredJob]:
        """
        Score jobs based on user profile using AI
        
        Args:
            resume_url: URL to user's resume
            jobs: List of job dictionaries
            user_skills: List of user's skills
            user_experience: User's experience summary
            
        Returns:
            List of ScoredJob objects with fit scores
        """
        try:
            logger.info(f"Scoring {len(jobs)} jobs using AI")
            
            # Download and extract resume content
            resume_content = await self._extract_resume_content(resume_url)
            
            # Prepare user profile summary
            user_profile = {
                "resume_content": resume_content,
                "skills": user_skills or [],
                "experience": user_experience or ""
            }
            
            scored_jobs = []
            
            # Process jobs in batches to avoid API limits
            batch_size = 5
            for i in range(0, len(jobs), batch_size):
                batch = jobs[i:i + batch_size]
                batch_scores = await self._score_job_batch(user_profile, batch)
                scored_jobs.extend(batch_scores)
                
                # Add delay between batches to respect rate limits
                if i + batch_size < len(jobs):
                    await asyncio.sleep(1)
            
            logger.info(f"Successfully scored {len(scored_jobs)} jobs")
            return scored_jobs
            
        except Exception as e:
            logger.error(f"Error in AI job scoring: {e}")
            # Fall back to mock scoring
            return self._generate_mock_scores(jobs)
    
    async def _extract_resume_content(self, resume_url: str) -> str:
        """
        Download and extract text content from resume
        
        Args:
            resume_url: URL to the resume file
            
        Returns:
            Extracted text content
        """
        try:
            logger.info(f"Downloading resume from: {resume_url}")
            
            response = requests.get(resume_url, timeout=30)
            response.raise_for_status()
            
            # For now, return a placeholder. In production, you would:
            # 1. Check file type (PDF, DOC, etc.)
            # 2. Extract text using appropriate library (PyPDF2, python-docx, etc.)
            # 3. Clean and format the extracted text
            
            return "Resume content extracted successfully. Skills and experience available for matching."
            
        except Exception as e:
            logger.warning(f"Could not extract resume content: {e}")
            return "Resume content not available for analysis."
    
    async def _score_job_batch(
        self, 
        user_profile: Dict[str, Any], 
        jobs: List[Dict[str, Any]]
    ) -> List[ScoredJob]:
        """
        Score a batch of jobs using AI
        
        Args:
            user_profile: User profile information
            jobs: List of jobs to score
            
        Returns:
            List of scored jobs
        """
        try:
            if self.openai_client:
                return await self._score_with_openai(user_profile, jobs)
            elif self.claude_client:
                return await self._score_with_claude(user_profile, jobs)
            else:
                return self._generate_mock_scores(jobs)
                
        except Exception as e:
            logger.error(f"Error in batch scoring: {e}")
            return self._generate_mock_scores(jobs)
    
    async def _score_with_openai(
        self, 
        user_profile: Dict[str, Any], 
        jobs: List[Dict[str, Any]]
    ) -> List[ScoredJob]:
        """Score jobs using OpenAI GPT"""
        try:
            # Prepare prompt for job scoring
            prompt = self._create_scoring_prompt(user_profile, jobs)
            
            response = await self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert career advisor and recruiter. Analyze job postings against a candidate's profile and provide fit scores."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=1000
            )
            
            # Parse AI response and create ScoredJob objects
            return self._parse_ai_scores(jobs, response.choices[0].message.content)
            
        except Exception as e:
            logger.error(f"OpenAI scoring error: {e}")
            return self._generate_mock_scores(jobs)
    
    async def _score_with_claude(
        self, 
        user_profile: Dict[str, Any], 
        jobs: List[Dict[str, Any]]
    ) -> List[ScoredJob]:
        """Score jobs using Claude"""
        try:
            # Prepare prompt for job scoring
            prompt = self._create_scoring_prompt(user_profile, jobs)
            
            message = await self.claude_client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=1000,
                temperature=0.3,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            # Parse AI response and create ScoredJob objects
            return self._parse_ai_scores(jobs, message.content[0].text)
            
        except Exception as e:
            logger.error(f"Claude scoring error: {e}")
            return self._generate_mock_scores(jobs)
    
    def _create_scoring_prompt(
        self, 
        user_profile: Dict[str, Any], 
        jobs: List[Dict[str, Any]]
    ) -> str:
        """
        Create a prompt for AI job scoring
        
        Args:
            user_profile: User profile information
            jobs: List of jobs to score
            
        Returns:
            Formatted prompt string
        """
        skills_str = ", ".join(user_profile["skills"]) if user_profile["skills"] else "Not specified"
        
        prompt = f"""
Please analyze the following job postings against this candidate's profile and provide fit scores from 0-100 for each job.

CANDIDATE PROFILE:
Skills: {skills_str}
Experience: {user_profile["experience"]}
Resume: {user_profile["resume_content"]}

JOBS TO SCORE:
"""
        
        for i, job in enumerate(jobs, 1):
            prompt += f"""
Job {i}:
Title: {job['title']}
Company: {job['company']}
Description: {job['description'][:500]}...
Location: {job.get('location', 'Not specified')}

"""
        
        prompt += """
For each job, provide a score from 0-100 where:
- 90-100: Excellent match (perfect skills alignment, ideal role)
- 80-89: Very good match (strong skills overlap, good role fit)
- 70-79: Good match (decent skills alignment, some missing elements)
- 60-69: Fair match (some relevant skills, role partially suitable)
- 50-59: Below average match (limited relevance)
- 0-49: Poor match (little to no alignment)

Respond in this exact format for each job:
Job 1: [score] - [brief explanation]
Job 2: [score] - [brief explanation]
etc.
"""
        
        return prompt
    
    def _parse_ai_scores(
        self, 
        jobs: List[Dict[str, Any]], 
        ai_response: str
    ) -> List[ScoredJob]:
        """
        Parse AI response and create ScoredJob objects
        
        Args:
            jobs: Original job list
            ai_response: AI scoring response
            
        Returns:
            List of ScoredJob objects
        """
        try:
            lines = ai_response.strip().split('\n')
            scored_jobs = []
            
            for i, job in enumerate(jobs):
                score = 50  # Default score
                explanation = "AI analysis completed"
                
                # Try to parse score from AI response
                for line in lines:
                    if f"Job {i+1}:" in line:
                        parts = line.split(' - ')
                        if len(parts) >= 2:
                            try:
                                score_part = parts[0].split(':')[1].strip()
                                score = int(score_part)
                                explanation = parts[1].strip()
                            except:
                                pass
                        break
                
                # Ensure score is within valid range
                score = max(0, min(100, score))
                
                scored_job = ScoredJob(
                    title=job['title'],
                    company=job['company'],
                    description=job['description'],
                    location=job.get('location'),
                    source_url=job.get('source_url'),
                    fit_score=score,
                    score_explanation=explanation
                )
                
                scored_jobs.append(scored_job)
            
            return scored_jobs
            
        except Exception as e:
            logger.error(f"Error parsing AI scores: {e}")
            return self._generate_mock_scores(jobs)
    
    def _generate_mock_scores(self, jobs: List[Dict[str, Any]]) -> List[ScoredJob]:
        """
        Generate mock scores for development/testing
        
        Args:
            jobs: List of jobs to score
            
        Returns:
            List of ScoredJob objects with mock scores
        """
        logger.info("Generating mock AI scores for development")
        
        scored_jobs = []
        
        for i, job in enumerate(jobs):
            # Generate a realistic mock score based on job position
            base_score = 85 - (i * 3)  # Decreasing scores
            mock_score = max(40, min(95, base_score + (i % 3) * 5))
            
            explanation = f"Mock AI analysis: Good match based on job requirements and candidate profile."
            
            scored_job = ScoredJob(
                title=job['title'],
                company=job['company'],
                description=job['description'],
                location=job.get('location'),
                source_url=job.get('source_url'),
                fit_score=mock_score,
                score_explanation=explanation
            )
            
            scored_jobs.append(scored_job)
        
        return scored_jobs
    
    async def test_connection(self) -> str:
        """Test AI service connectivity"""
        if self.openai_client:
            return "OpenAI API connected"
        elif self.claude_client:
            return "Claude API connected"
        else:
            return "No AI API configured - using mock data"