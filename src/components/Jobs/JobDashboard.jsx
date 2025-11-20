import React, { useState } from 'react';
import { Search, MapPin, Star, ExternalLink, CheckCircle, Clock, Briefcase } from 'lucide-react';
import { useJobs } from '../../hooks/useJobs';
import { useApplications } from '../../hooks/useApplications';
import { useProfile } from '../../hooks/useProfile';

const JobDashboard = () => {
  const [keyword, setKeyword] = useState('');
  const [location, setLocation] = useState('');
  const [searching, setSearching] = useState(false);
  
  const { jobs, loading: jobsLoading, scrapeAndScoreJobs } = useJobs();
  const { applyToJob, getApplicationStatus } = useApplications();
  const { profile } = useProfile();

  const handleSearch = async (e) => {
    e.preventDefault();
    
    if (!profile?.resume_url) {
      alert('Please upload your resume in the Profile tab first to get personalized job recommendations.');
      return;
    }
    
    if (!keyword.trim()) {
      alert('Please enter a job keyword to search.');
      return;
    }

    setSearching(true);
    try {
      console.log('Starting job search...', { keyword, location });
      await scrapeAndScoreJobs(keyword, location);
      alert(`Jobs found and scored successfully! Check the results below.`);
    } catch (error) {
      console.error('Error scraping jobs:', error);
      alert('Error finding jobs. Please try again or try different keywords.');
    } finally {
      setSearching(false);
    }
  };

  const handleApply = async (jobId) => {
    const result = await applyToJob(jobId);
    if (result.success) {
      alert('Successfully applied to this job!');
    } else {
      alert('Error applying to job: ' + result.error);
    }
  };

  const getFitScoreColor = (score) => {
    if (score >= 80) return 'text-green-600 bg-green-100';
    if (score >= 60) return 'text-yellow-600 bg-yellow-100';
    if (score >= 40) return 'text-orange-600 bg-orange-100';
    return 'text-red-600 bg-red-100';
  };

  const getFitScoreLabel = (score) => {
    if (score >= 80) return 'Excellent Match';
    if (score >= 60) return 'Good Match';
    if (score >= 40) return 'Fair Match';
    return 'Poor Match';
  };

  return (
    <div className="space-y-6">
      {/* Search Section */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">Find Jobs</h2>
        
        {!profile?.resume_url && (
          <div className="mb-4 p-4 bg-yellow-50 border border-yellow-200 rounded-md">
            <p className="text-sm text-yellow-800">
              Please upload your resume in the Profile tab to get personalized job recommendations.
            </p>
          </div>
        )}

        <form onSubmit={handleSearch} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label htmlFor="keyword" className="block text-sm font-medium text-gray-700 mb-1">
                Job Title / Keywords
              </label>
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
                <input
                  id="keyword"
                  type="text"
                  value={keyword}
                  onChange={(e) => setKeyword(e.target.value)}
                  placeholder="e.g., Software Engineer, Data Scientist"
                  className="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  required
                />
              </div>
            </div>

            <div>
              <label htmlFor="location" className="block text-sm font-medium text-gray-700 mb-1">
                Location
              </label>
              <div className="relative">
                <MapPin className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
                <input
                  id="location"
                  type="text"
                  value={location}
                  onChange={(e) => setLocation(e.target.value)}
                  placeholder="e.g., San Francisco, Remote"
                  className="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
            </div>
          </div>

          <button
            type="submit"
            disabled={searching || !profile?.resume_url}
            className="w-full md:w-auto px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {searching ? 'Searching & Scoring Jobs...' : 'Search Jobs'}
          </button>
        </form>
      </div>

      {/* Jobs List */}
      <div className="space-y-4">
        {jobsLoading ? (
          <div className="flex justify-center items-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          </div>
        ) : jobs.length === 0 ? (
          <div className="text-center py-8">
            <Briefcase className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No jobs found</h3>
            <p className="text-gray-600">
              Start by searching for jobs using the form above.
            </p>
          </div>
        ) : (
          jobs.map((job) => {
            const applicationStatus = getApplicationStatus(job.id);
            const isApplied = applicationStatus === 'applied';

            return (
              <div key={job.id} className="bg-white rounded-lg shadow-sm border p-6 hover:shadow-md transition-shadow">
                <div className="flex justify-between items-start mb-4">
                  <div className="flex-1">
                    <div className="flex items-center space-x-3 mb-2">
                      <h3 className="text-lg font-semibold text-gray-900">{job.title}</h3>
                      {job.source_url && (
                        <a
                          href={job.source_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-blue-600 hover:text-blue-800"
                        >
                          <ExternalLink className="w-4 h-4" />
                        </a>
                      )}
                    </div>
                    <p className="text-gray-700 font-medium">{job.company}</p>
                    {job.location && (
                      <p className="text-gray-500 text-sm flex items-center mt-1">
                        <MapPin className="w-3 h-3 mr-1" />
                        {job.location}
                      </p>
                    )}
                  </div>

                  <div className="flex items-center space-x-3">
                    {/* Fit Score */}
                    <div className={`px-3 py-1 rounded-full text-sm font-medium ${getFitScoreColor(job.fit_score)}`}>
                      <div className="flex items-center space-x-1">
                        <Star className="w-3 h-3" />
                        <span>{job.fit_score}% - {getFitScoreLabel(job.fit_score)}</span>
                      </div>
                    </div>

                    {/* Apply Button */}
                    <button
                      onClick={() => handleApply(job.id)}
                      disabled={isApplied}
                      className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                        isApplied
                          ? 'bg-green-100 text-green-800 cursor-not-allowed'
                          : 'bg-blue-600 text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500'
                      }`}
                    >
                      {isApplied ? (
                        <div className="flex items-center space-x-1">
                          <CheckCircle className="w-4 h-4" />
                          <span>Applied</span>
                        </div>
                      ) : (
                        'Apply'
                      )}
                    </button>
                  </div>
                </div>

                {/* Job Description */}
                <div className="text-gray-600 text-sm">
                  <p className="line-clamp-3">{job.description}</p>
                </div>

                {/* Metadata */}
                <div className="flex items-center justify-between text-xs text-gray-500 mt-4 pt-4 border-t">
                  <span>Scraped {new Date(job.scraped_at).toLocaleDateString()}</span>
                  <div className="flex items-center space-x-1">
                    <Clock className="w-3 h-3" />
                    <span>Posted {new Date(job.created_at).toLocaleDateString()}</span>
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};

export default JobDashboard;