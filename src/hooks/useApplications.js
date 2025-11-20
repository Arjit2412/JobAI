import { useState, useEffect } from 'react';
import { supabase } from '../lib/supabase';
import { useAuth } from '../contexts/AuthContext';

export const useApplications = () => {
  const { user } = useAuth();
  const [applications, setApplications] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (user) {
      fetchApplications();
    }
  }, [user]);

  const fetchApplications = async () => {
    try {
      setLoading(true);
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
            fit_score
          )
        `)
        .eq('user_id', user.id);

      if (error) throw error;
      
      setApplications(data || []);
    } catch (err) {
      console.error('Error fetching applications:', err);
    } finally {
      setLoading(false);
    }
  };

  const applyToJob = async (jobId) => {
    try {
      const { data, error } = await supabase
        .from('applications')
        .upsert([
          {
            user_id: user.id,
            job_id: jobId,
            status: 'applied',
            applied_at: new Date().toISOString()
          }
        ])
        .select();

      if (error) throw error;
      
      await fetchApplications();
      return { success: true };
    } catch (err) {
      console.error('Error applying to job:', err);
      return { success: false, error: err.message };
    }
  };

  const getApplicationStatus = (jobId) => {
    const application = applications.find(app => app.job_id === jobId);
    return application?.status || 'not_applied';
  };

  return {
    applications,
    loading,
    fetchApplications,
    applyToJob,
    getApplicationStatus
  };
};