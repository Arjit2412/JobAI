import express from 'express';
import { supabase } from '../config/supabase.js';
import { requireAuth } from '../middleware/auth.js';

const router = express.Router();

// Get user applications
router.get('/', requireAuth, async (req, res) => {
  try {
    const { data, error } = await supabase
      .from('applications')
      .select(`
        *,
        jobs (
          id,
          title,
          company,
          description,
          location,
          fit_score,
          source_url
        )
      `)
      .eq('user_id', req.user.id)
      .order('created_at', { ascending: false });

    if (error) {
      throw error;
    }

    res.json({ applications: data });
  } catch (error) {
    console.error('Get applications error:', error);
    res.status(500).json({ error: 'Failed to fetch applications' });
  }
});

// Apply to a job
router.post('/', requireAuth, async (req, res) => {
  try {
    const { job_id } = req.body;

    if (!job_id) {
      return res.status(400).json({ error: 'Job ID is required' });
    }

    // Check if job exists
    const { data: job, error: jobError } = await supabase
      .from('jobs')
      .select('id')
      .eq('id', job_id)
      .single();

    if (jobError || !job) {
      return res.status(404).json({ error: 'Job not found' });
    }

    // Create or update application
    const applicationData = {
      user_id: req.user.id,
      job_id: job_id,
      status: 'applied',
      applied_at: new Date().toISOString(),
      created_at: new Date().toISOString()
    };

    const { data, error } = await supabase
      .from('applications')
      .upsert([applicationData], {
        onConflict: 'user_id,job_id'
      })
      .select()
      .single();

    if (error) {
      throw error;
    }

    res.status(201).json({ 
      message: 'Applied to job successfully',
      application: data 
    });
  } catch (error) {
    console.error('Apply to job error:', error);
    res.status(500).json({ error: 'Failed to apply to job' });
  }
});

// Update application status
router.put('/:id', requireAuth, async (req, res) => {
  try {
    const { id } = req.params;
    const { status } = req.body;

    if (!['applied', 'not_applied'].includes(status)) {
      return res.status(400).json({ error: 'Invalid status' });
    }

    const updateData = {
      status,
      applied_at: status === 'applied' ? new Date().toISOString() : null
    };

    const { data, error } = await supabase
      .from('applications')
      .update(updateData)
      .eq('id', id)
      .eq('user_id', req.user.id) // Ensure user can only update their own applications
      .select()
      .single();

    if (error) {
      if (error.code === 'PGRST116') {
        return res.status(404).json({ error: 'Application not found' });
      }
      throw error;
    }

    res.json({ 
      message: 'Application updated successfully',
      application: data 
    });
  } catch (error) {
    console.error('Update application error:', error);
    res.status(500).json({ error: 'Failed to update application' });
  }
});

// Get application by job ID
router.get('/job/:jobId', requireAuth, async (req, res) => {
  try {
    const { jobId } = req.params;

    const { data, error } = await supabase
      .from('applications')
      .select('*')
      .eq('user_id', req.user.id)
      .eq('job_id', jobId)
      .single();

    if (error && error.code !== 'PGRST116') {
      throw error;
    }

    res.json({ application: data });
  } catch (error) {
    console.error('Get application error:', error);
    res.status(500).json({ error: 'Failed to fetch application' });
  }
});

export default router;