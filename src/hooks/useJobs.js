import { useState, useEffect } from 'react';
import { supabase } from '../lib/supabase';

export const useJobs = () => {
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchJobs();
  }, []);

  const fetchJobs = async () => {
    try {
      setLoading(true);
      const { data, error } = await supabase
        .from('jobs')
        .select('*')
        .order('fit_score', { ascending: false })
        .limit(50);

      if (error) throw error;
      
      setJobs(data || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const scrapeAndScoreJobs = async (keyword, location) => {
    try {
      setLoading(true);
      setError(null);
      
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:3001';
      
      // Call our backend API which will coordinate with Python microservice  
      const response = await fetch(`${apiUrl}/api/jobs/scrape-and-score`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('supabase.auth.token')}`,
        },
        body: JSON.stringify({ keyword, location }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to scrape and score jobs');
      }

      const result = await response.json();
      console.log('Job scraping result:', result);
      
      // Refresh jobs list
      await fetchJobs();
      
      return result;
    } catch (err) {
      console.error('Job scraping error:', err);
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  return {
    jobs,
    loading,
    error,
    fetchJobs,
    scrapeAndScoreJobs
  };
};