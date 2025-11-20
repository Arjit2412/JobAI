import express from 'express';
import axios from 'axios';
import { supabase } from '../config/supabase.js';
import { requireAuth } from '../middleware/auth.js';

const router = express.Router();

const PYTHON_SERVICE_URL = process.env.PYTHON_SERVICE_URL || 'http://localhost:8000';

// Get all jobs with pagination
router.get('/', requireAuth, async (req, res) => {
  try {
    const { page = 1, limit = 20 } = req.query;
    const offset = (page - 1) * limit;

    const { data, error, count } = await supabase
      .from('jobs')
      .select('*', { count: 'exact' })
      .order('fit_score', { ascending: false })
      .range(offset, offset + limit - 1);

    if (error) {
      throw error;
    }

    res.json({ 
      jobs: data,
      pagination: {
        page: parseInt(page),
        limit: parseInt(limit),
        total: count,
        totalPages: Math.ceil(count / limit)
      }
    });
  } catch (error) {
    console.error('Get jobs error:', error);
    res.status(500).json({ error: 'Failed to fetch jobs' });
  }
});

// Scrape and score jobs endpoint
router.post('/scrape-and-score', requireAuth, async (req, res) => {
  try {
    const { keyword, location } = req.body;

    if (!keyword) {
      return res.status(400).json({ error: 'Keyword is required' });
    }

    console.log(`🔍 Job search request: keyword="${keyword}", location="${location}"`);

    // Get user profile for scoring
    const { data: profile, error: profileError } = await supabase
      .from('profiles')
      .select('*')
      .eq('user_id', req.user.id)
      .single();

    if (profileError || !profile?.resume_url) {
      return res.status(400).json({ 
        error: 'User profile with resume is required for job scoring' 
      });
    }

    // Step 1: Scrape jobs from Python service
    console.log('🔍 Scraping jobs...');
    const scrapeResponse = await axios.get(`${PYTHON_SERVICE_URL}/scrape_jobs`, {
      params: { keyword, location },
      timeout: 60000 // 60 second timeout
    });

    if (!scrapeResponse.data.jobs || scrapeResponse.data.jobs.length === 0) {
      return res.json({ 
        message: 'No jobs found for the given criteria',
        jobs: [],
        count: 0
      });
    }

    console.log(`📊 Found ${scrapeResponse.data.jobs.length} jobs`);

    // Step 2: Score jobs using Python service
    console.log('🤖 Scoring jobs with AI...');
    const scoreResponse = await axios.post(`${PYTHON_SERVICE_URL}/score_jobs`, {
      resume_url: profile.resume_url,
      jobs: scrapeResponse.data.jobs,
      user_skills: profile.skills || [],
      user_experience: profile.experience || ''
    }, {
      timeout: 120000 // 2 minute timeout for AI processing
    });

    const scoredJobs = scoreResponse.data.scored_jobs;
    console.log(`✅ Scored ${scoredJobs.length} jobs`);

    // Step 3: Save jobs to database
    const jobInserts = scoredJobs.map(job => ({
      title: job.title,
      company: job.company,
      description: job.description,
      location: job.location || location || '',
      source_url: job.source_url,
      fit_score: job.fit_score,
      scraped_at: new Date().toISOString(),
      created_at: new Date().toISOString()
    }));

    const { data: insertedJobs, error: insertError } = await supabase
      .from('jobs')
      .upsert(jobInserts, { 
        onConflict: 'source_url',
        ignoreDuplicates: false 
      })
      .select();

    if (insertError) {
      console.error('Database insert error:', insertError);
      throw insertError;
    }

    console.log(`💾 Saved ${insertedJobs.length} jobs to database`);

    res.json({ 
      message: 'Jobs scraped and scored successfully',
      jobs: insertedJobs,
      count: insertedJobs.length,
      sources: scrapeResponse.data.sources || ['multiple']
    });

  } catch (error) {
    console.error('Scrape and score error:', error);
    
    if (error.code === 'ECONNREFUSED') {
      res.status(503).json({ 
        error: 'Python service is unavailable. Please ensure the AI service is running.' 
      });
    } else if (error.code === 'ETIMEDOUT') {
      res.status(408).json({ 
        error: 'Request timeout. Job processing took too long.' 
      });
    } else {
      res.status(500).json({ 
        error: 'Failed to scrape and score jobs',
        details: error.message
      });
    }
  }
});

// Get job by ID
router.get('/:id', requireAuth, async (req, res) => {
  try {
    const { id } = req.params;

    const { data, error } = await supabase
      .from('jobs')
      .select('*')
      .eq('id', id)
      .single();

    if (error) {
      if (error.code === 'PGRST116') {
        return res.status(404).json({ error: 'Job not found' });
      }
      throw error;
    }

    res.json({ job: data });
  } catch (error) {
    console.error('Get job error:', error);
    res.status(500).json({ error: 'Failed to fetch job' });
  }
});

export default router;