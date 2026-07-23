// src/pages/Jobs.jsx
import { useState, useEffect } from 'react';
import { getJobs, fetchJobs } from '../api/jobs';

function decodeHtmlEntities(text) {
  if (!text) return '';
  const textarea = document.createElement('textarea');
  textarea.innerHTML = text;
  return textarea.value;
}

function fixEncoding(text) {
  if (!text) return '';
  try {
    return decodeURIComponent(escape(text));
  } catch {
    return text;
  }
}

function cleanText(text) {
  return decodeHtmlEntities(fixEncoding(text));
}

function Jobs() {
  const [jobs, setJobs] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isFetching, setIsFetching] = useState(false);
  const [error, setError] = useState('');
  const [fetchResult, setFetchResult] = useState(null);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalJobs, setTotalJobs] = useState(0);

  useEffect(() => {
    loadJobs();
  }, [page]);

  const loadJobs = async () => {
    setIsLoading(true);
    setError('');
    try {
      const data = await getJobs(page, 20);
      setJobs(data.jobs || []);
      setTotalPages(data.total_pages || 1);
      setTotalJobs(data.total_jobs || 0);
    } catch (err) {
      setError('Failed to load jobs. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleFetchJobs = async () => {
    setIsFetching(true);
    setError('');
    setFetchResult(null);
    try {
      const data = await fetchJobs();
      setFetchResult(data);
      setPage(1);
      await loadJobs();
    } catch (err) {
      const message = err.response?.data?.error || 'Failed to fetch jobs. Please try again.';
      setError(message);
    } finally {
      setIsFetching(false);
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  const stripHtml = (text) => {
    if (!text) return '';
    const doc = new DOMParser().parseFromString(text, 'text/html');
    return doc.body.textContent || '';
  };

  const truncateText = (text, maxLength = 200) => {
    if (!text) return '';
    const clean = stripHtml(text);
    const fixed = cleanText(clean);
    if (fixed.length <= maxLength) return fixed;
    return fixed.substring(0, maxLength) + '...';
  };

  return (
    <div className="jobs-container">
      <div className="jobs-header">
        <div className="jobs-header-top">
          <h1 className="jobs-title">Job Listings</h1>
          <button
            onClick={handleFetchJobs}
            className="btn btn-primary"
            disabled={isFetching}
          >
            {isFetching ? 'Fetching...' : 'Fetch New Jobs'}
          </button>
        </div>
        {totalJobs > 0 && (
          <p className="jobs-count">{totalJobs} jobs in database</p>
        )}
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      {fetchResult && (
        <div className="alert alert-success">
          {fetchResult.message} — {fetchResult.new_jobs_added} new, {fetchResult.duplicates_skipped} duplicates skipped
        </div>
      )}

      {isLoading ? (
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <p>Loading jobs...</p>
        </div>
      ) : jobs.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon">💼</div>
          <h2 className="empty-state-title">No jobs yet</h2>
          <p className="empty-state-text">
            Click "Fetch New Jobs" to pull remote developer jobs from RemoteOK.
          </p>
          <button
            onClick={handleFetchJobs}
            className="btn btn-primary"
            disabled={isFetching}
          >
            {isFetching ? 'Fetching...' : 'Fetch New Jobs'}
          </button>
        </div>
      ) : (
        <>
          <div className="jobs-list">
            {jobs.map((job) => (
              <div key={job.id} className="job-card">
                <div className="job-card-header">
                  <h3 className="job-title">{cleanText(job.title)}</h3>
                  <span className="job-source">{job.source}</span>
                </div>
                <p className="job-company">{cleanText(job.company)}</p>
                {job.location && (
                  <p className="job-location">📍 {cleanText(job.location)}</p>
                )}
                {job.description && (
                  <p className="job-description">{truncateText(job.description)}</p>
                )}
                <div className="job-card-footer">
                  <span className="job-date">Fetched: {formatDate(job.fetched_at)}</span>
                  {job.source_url && (
                    <a
                      href={job.source_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="job-link"
                    >
                      View Original →
                    </a>
                  )}
                </div>
              </div>
            ))}
          </div>

          {totalPages > 1 && (
            <div className="pagination">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
                className="btn btn-secondary"
              >
                Previous
              </button>
              <span className="pagination-info">
                Page {page} of {totalPages}
              </span>
              <button
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page === totalPages}
                className="btn btn-secondary"
              >
                Next
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}

export default Jobs;