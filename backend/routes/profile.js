import express from 'express';
import { supabase } from '../config/supabase.js';
import { requireAuth } from '../middleware/auth.js';

const router = express.Router();

// Get user profile
router.get('/', requireAuth, async (req, res) => {
  try {
    const { data, error } = await supabase
      .from('profiles')
      .select('*')
      .eq('user_id', req.user.id)
      .single();

    if (error && error.code !== 'PGRST116') {
      throw error;
    }

    res.json({ profile: data });
  } catch (error) {
    console.error('Get profile error:', error);
    res.status(500).json({ error: 'Failed to fetch profile' });
  }
});

// Create user profile
router.post('/', requireAuth, async (req, res) => {
  try {
    const { resume_url, skills, experience } = req.body;

    const profileData = {
      user_id: req.user.id,
      resume_url: resume_url || null,
      skills: skills || [],
      experience: experience || '',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    };

    const { data, error } = await supabase
      .from('profiles')
      .insert([profileData])
      .select()
      .single();

    if (error) {
      throw error;
    }

    res.status(201).json({ 
      message: 'Profile created successfully',
      profile: data 
    });
  } catch (error) {
    console.error('Create profile error:', error);
    
    if (error.code === '23505') { // Unique constraint violation
      res.status(400).json({ error: 'Profile already exists for this user' });
    } else {
      res.status(500).json({ error: 'Failed to create profile' });
    }
  }
});

// Update user profile
router.put('/', requireAuth, async (req, res) => {
  try {
    const { resume_url, skills, experience } = req.body;

    const updateData = {
      updated_at: new Date().toISOString()
    };

    if (resume_url !== undefined) updateData.resume_url = resume_url;
    if (skills !== undefined) updateData.skills = skills;
    if (experience !== undefined) updateData.experience = experience;

    const { data, error } = await supabase
      .from('profiles')
      .update(updateData)
      .eq('user_id', req.user.id)
      .select()
      .single();

    if (error) {
      throw error;
    }

    res.json({ 
      message: 'Profile updated successfully',
      profile: data 
    });
  } catch (error) {
    console.error('Update profile error:', error);
    res.status(500).json({ error: 'Failed to update profile' });
  }
});

export default router;