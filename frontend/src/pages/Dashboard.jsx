// src/pages/Dashboard.jsx
import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { getMyResume } from '../api/resume';
import { getJobs } from '../api/jobs';
import { getMatches } from '../api/matches';

function Dashboard() {
  const [resumeStatus, setResumeStatus] = useState({ loading: true, data: null });
  const [jobsStatus, setJobsStatus] = useState({ loading: true, data: null });
  const [matchesStatus, setMatchesStatus] = useState({ loading: true, data: null });

  useEffect(() => {
    loadResume();
    loadJobs();
    loadMatches();
  }, []);

  const loadResume = async () => {
    try {
      const data = await getMyResume();
      setResumeStatus({ loading: false, data });
    } catch {
      setResumeStatus({ loading: false, data: null });
    }
  };

  const loadJobs = async () => {
    try {
      const data = await getJobs(1, 1);
      setJobsStatus({ loading: false, data });
    } catch {
      setJobsStatus({ loading: false, data: null });
    }
  };

  const loadMatches = async () => {
    try {
      const data = await getMatches();
      setMatchesStatus({ loading: false, data });
    } catch {
      setMatchesStatus({ loading: false, data: null });
    }
  };

  const getHighestScore = (matches) => {
    if (!matches || matches.length === 0) return null;
    const scores = matches.map((m) => m.fit_score);
    return Math.max(...scores);
  };

  const getScoreColorClass = (score) => {
    if (score >= 80) return 'card-stat-score-high';
    if (score >= 60) return 'card-stat-score-medium';
    return 'card-stat-score-low';
  };

  const ResumeIcon = () => (
    <svg className="card-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
      <polyline points="14 2 14 8 20 8" />
      <line x1="16" y1="13" x2="8" y2="13" />
      <line x1="16" y1="17" x2="8" y2="17" />
      <polyline points="10 9 9 9 8 9" />
    </svg>
  );

  const JobsIcon = () => (
    <svg className="card-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="2" y="7" width="20" height="14" rx="2" ry="2" />
      <path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16" />
    </svg>
  );

  const MatchesIcon = () => (
    <svg className="card-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="10" />
      <circle cx="12" cy="12" r="6" />
      <circle cx="12" cy="12" r="2" />
    </svg>
  );

  return (
    <div className="dashboard-container">
      <main className="dashboard-content">
        <div className="welcome-card">
          <h2 className="welcome-title">Welcome to ZaibHunt</h2>
          <p className="welcome-text">
            Upload your resume. Let AI find your best-fit jobs.
          </p>
        </div>

        <div className="dashboard-cards">
          <Link to="/resume" className="dashboard-card dashboard-card-link">
            <div className="card-header">
              <ResumeIcon />
              <h3 className="card-title">Resume</h3>
            </div>
            {resumeStatus.loading ? (
              <p className="card-stat card-loading">Loading...</p>
            ) : resumeStatus.data ? (
              <p className="card-stat card-stat-success">
                ✓ Resume uploaded
                <span className="card-stat-detail">{resumeStatus.data.filename}</span>
              </p>
            ) : (
              <p className="card-stat card-stat-empty">No resume uploaded yet</p>
            )}
          </Link>

          <Link to="/jobs" className="dashboard-card dashboard-card-link">
            <div className="card-header">
              <JobsIcon />
              <h3 className="card-title">Jobs</h3>
            </div>
            {jobsStatus.loading ? (
              <p className="card-stat card-loading">Loading...</p>
            ) : jobsStatus.data ? (
              <p className="card-stat card-stat-success">
                {jobsStatus.data.total_jobs || 0} jobs fetched
              </p>
            ) : (
              <p className="card-stat card-stat-empty">No jobs fetched yet</p>
            )}
          </Link>

          <Link to="/matches" className="dashboard-card dashboard-card-link">
            <div className="card-header">
              <MatchesIcon />
              <h3 className="card-title">Matches</h3>
            </div>
            {matchesStatus.loading ? (
              <p className="card-stat card-loading">Loading...</p>
            ) : matchesStatus.data && matchesStatus.data.matches?.length > 0 ? (
              <div className="card-stat-group">
                <p className="card-stat card-stat-success">
                  {matchesStatus.data.matches.length} matches found
                </p>
                {getHighestScore(matchesStatus.data.matches) && (
                  <p className={`card-stat card-stat-highlight ${getScoreColorClass(getHighestScore(matchesStatus.data.matches))}`}>
                    Best match: {getHighestScore(matchesStatus.data.matches)}%
                  </p>
                )}
              </div>
            ) : (
              <p className="card-stat card-stat-empty">No matches found yet</p>
            )}
          </Link>
        </div>
      </main>
    </div>
  );
}

export default Dashboard;