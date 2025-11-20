"""
Job scraping service for Indeed and JSearch APIs
Uses real APIs to extract job listings with fallback mechanisms
"""

import asyncio
import logging
import random
import time
import os
from typing import List, Dict, Any, Optional
import requests
import aiohttp
from urllib.parse import urlencode

logger = logging.getLogger(__name__)

class JobScraper:
    """Service for scraping job listings from various job boards"""
    
    def __init__(self):
        self.jsearch_api_key = os.getenv("JSEARCH_API_KEY")
        self.jsearch_base_url = "https://jsearch.p.rapidapi.com"
        
        # Headers for JSearch API
        self.jsearch_headers = {
            "X-RapidAPI-Key": self.jsearch_api_key,
            "X-RapidAPI-Host": "jsearch.p.rapidapi.com"
        }
        
        # Session for requests
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        logger.info("JobScraper initialized with API integrations")
    
    async def scrape_jobs(
        self, 
        keyword: str, 
        location: str = "", 
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Scrape jobs from multiple sources with fallback
        
        Args:
            keyword: Job search keyword
            location: Job location
            limit: Maximum number of jobs to scrape
            
        Returns:
            List of job dictionaries
        """
        all_jobs = []
        
        try:
            # Try JSearch API first (more reliable)
            if self.jsearch_api_key:
                logger.info("Fetching jobs from JSearch API")
                jsearch_jobs = await self._scrape_jsearch_jobs(keyword, location, limit)
                all_jobs.extend(jsearch_jobs)
                logger.info(f"JSearch API returned {len(jsearch_jobs)} jobs")
            
            # If we need more jobs, try Indeed scraping
            if len(all_jobs) < limit:
                remaining = limit - len(all_jobs)
                logger.info(f"Fetching {remaining} additional jobs from Indeed")
                indeed_jobs = await self._scrape_indeed_jobs(keyword, location, remaining)
                all_jobs.extend(indeed_jobs)
                logger.info(f"Indeed scraping returned {len(indeed_jobs)} jobs")
            
            # Remove duplicates based on title and company
            unique_jobs = self._remove_duplicates(all_jobs)
            
            # Limit to requested number
            final_jobs = unique_jobs[:limit]
            
            logger.info(f"Total unique jobs found: {len(final_jobs)}")
            return final_jobs
            
        except Exception as e:
            logger.error(f"Error in job scraping: {e}")
            # Fallback to mock data
            return self._get_mock_jobs(keyword, location, limit)
    
    async def _scrape_jsearch_jobs(
        self, 
        keyword: str, 
        location: str = "", 
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Scrape jobs using JSearch API (RapidAPI)
        
        Args:
            keyword: Job search keyword
            location: Job location
            limit: Maximum number of jobs
            
        Returns:
            List of job dictionaries
        """
        try:
            if not self.jsearch_api_key:
                logger.warning("JSearch API key not found")
                return []
            
            # Prepare search parameters
            params = {
                "query": f"{keyword} {location}".strip(),
                "page": "1",
                "num_pages": "1",
                "date_posted": "all"
            }
            
            url = f"{self.jsearch_base_url}/search"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url, 
                    headers=self.jsearch_headers, 
                    params=params,
                    timeout=30
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        jobs_data = data.get("data", [])
                        
                        jobs = []
                        for job_item in jobs_data[:limit]:
                            try:
                                job = self._parse_jsearch_job(job_item)
                                if job:
                                    jobs.append(job)
                            except Exception as e:
                                logger.warning(f"Error parsing JSearch job: {e}")
                                continue
                        
                        return jobs
                    else:
                        logger.error(f"JSearch API error: {response.status}")
                        return []
                        
        except Exception as e:
            logger.error(f"JSearch API request failed: {e}")
            return []
    
    def _parse_jsearch_job(self, job_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Parse job data from JSearch API response
        
        Args:
            job_data: Raw job data from JSearch API
            
        Returns:
            Parsed job dictionary or None
        """
        try:
            title = job_data.get("job_title", "").strip()
            company = job_data.get("employer_name", "").strip()
            description = job_data.get("job_description", "").strip()
            location = job_data.get("job_city", "")
            state = job_data.get("job_state", "")
            country = job_data.get("job_country", "")
            
            # Combine location parts
            location_parts = [loc for loc in [location, state, country] if loc]
            full_location = ", ".join(location_parts)
            
            source_url = job_data.get("job_apply_link") or job_data.get("job_url", "")
            
            # Validate required fields
            if not title or not company:
                return None
            
            # Clean description
            if not description:
                description = f"Job opportunity at {company} for {title} position."
            
            return {
                "title": title,
                "company": company,
                "description": description[:1000],  # Limit description length
                "location": full_location,
                "source_url": source_url,
                "source": "jsearch"
            }
            
        except Exception as e:
            logger.warning(f"Error parsing JSearch job data: {e}")
            return None
    
    async def _scrape_indeed_jobs(
        self, 
        keyword: str, 
        location: str = "", 
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Scrape jobs from Indeed using web scraping
        
        Args:
            keyword: Job search keyword
            location: Job location
            limit: Maximum number of jobs
            
        Returns:
            List of job dictionaries
        """
        try:
            from bs4 import BeautifulSoup
            
            logger.info(f"Scraping Indeed for: {keyword} in {location}")
            
            jobs = []
            
            # Build Indeed search URL
            params = {
                'q': keyword,
                'l': location,
                'start': 0,
                'limit': min(50, limit)
            }
            
            base_url = "https://www.indeed.com/jobs"
            search_url = f"{base_url}?{urlencode(params)}"
            
            logger.info(f"Fetching: {search_url}")
            
            # Add delay to avoid rate limiting
            await asyncio.sleep(random.uniform(1, 3))
            
            response = self.session.get(search_url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for job cards with different selectors
            job_selectors = [
                'div[data-jk]',
                '.job_seen_beacon',
                '.jobsearch-SerpJobCard',
                '.slider_container .slider_item'
            ]
            
            job_cards = []
            for selector in job_selectors:
                job_cards = soup.select(selector)
                if job_cards:
                    break
            
            if not job_cards:
                logger.warning("No job cards found on Indeed page")
                return []
            
            for card in job_cards[:limit]:
                try:
                    job_data = self._extract_indeed_job_from_card(card)
                    if job_data:
                        jobs.append(job_data)
                except Exception as e:
                    logger.warning(f"Error extracting Indeed job from card: {e}")
                    continue
            
            logger.info(f"Indeed scraping returned {len(jobs)} jobs")
            return jobs
            
        except Exception as e:
            logger.error(f"Error scraping Indeed jobs: {e}")
            return []
    
    def _extract_indeed_job_from_card(self, card) -> Optional[Dict[str, Any]]:
        """
        Extract job information from an Indeed job card
        
        Args:
            card: BeautifulSoup element representing a job card
            
        Returns:
            Dictionary with job information or None
        """
        try:
            # Extract job title with multiple selectors
            title_selectors = [
                'h2.jobTitle a span',
                'h2.jobTitle span',
                '.jobTitle a',
                '[data-testid="job-title"]'
            ]
            
            title = ""
            for selector in title_selectors:
                title_elem = card.select_one(selector)
                if title_elem:
                    title = title_elem.get_text(strip=True)
                    break
            
            # Extract company name
            company_selectors = [
                '.companyName',
                '[data-testid="company-name"]',
                '.company'
            ]
            
            company = ""
            for selector in company_selectors:
                company_elem = card.select_one(selector)
                if company_elem:
                    company = company_elem.get_text(strip=True)
                    break
            
            # Extract location
            location_selectors = [
                '.companyLocation',
                '[data-testid="job-location"]',
                '.location'
            ]
            
            location = ""
            for selector in location_selectors:
                location_elem = card.select_one(selector)
                if location_elem:
                    location = location_elem.get_text(strip=True)
                    break
            
            # Extract job description/summary
            summary_selectors = [
                '.summary',
                '.job-snippet',
                '[data-testid="job-snippet"]'
            ]
            
            description = ""
            for selector in summary_selectors:
                summary_elem = card.select_one(selector)
                if summary_elem:
                    description = summary_elem.get_text(strip=True)
                    break
            
            # Extract job URL
            job_key = card.get('data-jk')
            source_url = f"https://www.indeed.com/viewjob?jk={job_key}" if job_key else ""
            
            # Validate required fields
            if not title or not company:
                return None
            
            # Default description if none found
            if not description:
                description = f"Job opportunity at {company} for {title} position."
            
            return {
                "title": title,
                "company": company,
                "description": description[:1000],  # Limit description length
                "location": location,
                "source_url": source_url,
                "source": "indeed"
            }
            
        except Exception as e:
            logger.warning(f"Error extracting Indeed job data from card: {e}")
            return None
    
    def _remove_duplicates(self, jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Remove duplicate jobs based on title and company
        
        Args:
            jobs: List of job dictionaries
            
        Returns:
            List of unique jobs
        """
        seen = set()
        unique_jobs = []
        
        for job in jobs:
            # Create a key based on title and company (normalized)
            key = f"{job['title'].lower().strip()}|{job['company'].lower().strip()}"
            
            if key not in seen:
                seen.add(key)
                unique_jobs.append(job)
        
        return unique_jobs
    
    def _get_mock_jobs(self, keyword: str, location: str, limit: int) -> List[Dict[str, Any]]:
        """
        Generate mock job data for development/testing
        
        Args:
            keyword: Search keyword
            location: Search location
            limit: Number of mock jobs to generate
            
        Returns:
            List of mock job dictionaries
        """
        logger.info("Generating mock job data as fallback")
        
        companies = [
            "TechCorp", "InnovateLab", "DataSoft", "CloudSystems", "AIStartup",
            "DevStudio", "CodeCraft", "ByteDance", "TechFlow", "DigitalHub",
            "Microsoft", "Google", "Amazon", "Meta", "Apple"
        ]
        
        job_types = [
            "Senior", "Junior", "Lead", "Principal", "Staff"
        ]
        
        mock_jobs = []
        
        for i in range(min(limit, 15)):  # Generate up to 15 mock jobs
            company = random.choice(companies)
            job_type = random.choice(job_types)
            
            mock_job = {
                "title": f"{job_type} {keyword.title()}",
                "company": company,
                "description": f"We are looking for a skilled {keyword} to join our team at {company}. "
                             f"The ideal candidate will have experience in {keyword.lower()} and related technologies. "
                             f"This is a great opportunity to work with cutting-edge technology and grow your career. "
                             f"Responsibilities include developing software solutions, collaborating with cross-functional teams, "
                             f"and contributing to our innovative products.",
                "location": location or random.choice(["San Francisco, CA", "New York, NY", "Seattle, WA", "Austin, TX", "Remote"]),
                "source_url": f"https://example.com/job/{i+1}",
                "source": "mock"
            }
            mock_jobs.append(mock_job)
            
        return mock_jobs

    # Keep the old method name for backward compatibility
    async def scrape_indeed_jobs(self, keyword: str, location: str = "", limit: int = 20) -> List[Dict[str, Any]]:
        """Backward compatibility method"""
        return await self.scrape_jobs(keyword, location, limit)