// src/pages/Matches.jsx
import { useState, useEffect } from 'react';
import { getMatches, runMatching, generateCoverLetter } from '../api/matches';

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

function Matches() {
  const [matches, setMatches] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isRunning, setIsRunning] = useState(false);
  const [error, setError] = useState('');
  const [runResult, setRunResult] = useState(null);
  const [generatingForId, setGeneratingForId] = useState(null);
  const [expandedCoverLetters, setExpandedCoverLetters] = useState({});
  const [copySuccess, setCopySuccess] = useState({});
  const [cardErrors, setCardErrors] = useState({});

  useEffect(() => {
    loadMatches();
  }, []);

  const loadMatches = async () => {
    setIsLoading(true);
    setError('');
    try {
      const data = await getMatches();
      setMatches(data.matches || []);
    } catch (err) {
      setError('Failed to load matches. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleRunMatching = async () => {
    setIsRunning(true);
    setError('');
    setRunResult(null);
    try {
      const data = await runMatching();
      setRunResult(data);
      await loadMatches();
    } catch (err) {
      const message = err.response?.data?.error || 'Failed to run matching. Please try again.';
      setError(message);
    } finally {
      setIsRunning(false);
    }
  };

  const handleGenerateCoverLetter = async (matchId) => {
    setGeneratingForId(matchId);
    setCardErrors((prev) => ({ ...prev, [matchId]: '' }));
    try {
      const data = await generateCoverLetter(matchId);
      setMatches((prevMatches) =>
        prevMatches.map((match) =>
          match.id === matchId
            ? { ...match, cover_letter: data.cover_letter, has_cover_letter: true }
            : match
        )
      );
      setExpandedCoverLetters((prev) => ({ ...prev, [matchId]: true }));
    } catch (err) {
      const message = err.response?.data?.error || 'Failed to generate cover letter.';
      setCardErrors((prev) => ({ ...prev, [matchId]: message }));
    } finally {
      setGeneratingForId(null);
    }
  };

  const toggleCoverLetter = (matchId) => {
    setExpandedCoverLetters((prev) => ({
      ...prev,
      [matchId]: !prev[matchId],
    }));
  };

  const handleCopyToClipboard = async (matchId, text) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopySuccess((prev) => ({ ...prev, [matchId]: true }));
      setTimeout(() => {
        setCopySuccess((prev) => ({ ...prev, [matchId]: false }));
      }, 2000);
    } catch {
      const textarea = document.createElement('textarea');
      textarea.value = text;
      document.body.appendChild(textarea);
      textarea.select();
      document.execCommand('copy');
      document.body.removeChild(textarea);
      setCopySuccess((prev) => ({ ...prev, [matchId]: true }));
      setTimeout(() => {
        setCopySuccess((prev) => ({ ...prev, [matchId]: false }));
      }, 2000);
    }
  };

  const getScoreColor = (score) => {
    if (score >= 80) return 'score-high';
    if (score >= 60) return 'score-medium';
    return 'score-low';
  };

  const getScoreLabel = (score) => {
    if (score >= 80) return 'Strong Match';
    if (score >= 60) return 'Good Match';
    if (score >= 40) return 'Average Match';
    return 'Low Match';
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

  return (
    <div className="matches-container">
      <div className="matches-header">
        <div className="matches-header-top">
          <h1 className="matches-title">Job Matches</h1>
          <button
            onClick={handleRunMatching}
            className="btn btn-primary"
            disabled={isRunning}
          >
            {isRunning ? 'Analyzing...' : 'Run AI Matching'}
          </button>
        </div>
        {matches.length > 0 && (
          <p className="matches-count">{matches.length} matches found</p>
        )}
      </div>

      {error && (
        <div className="alert alert-error">
          {error}
          <button onClick={() => setError('')} className="alert-close">×</button>
        </div>
      )}

      {runResult && (
        <div className="alert alert-success">
          {runResult.message} — Average fit score: {runResult.average_fit_score}
        </div>
      )}

      {isRunning && (
        <div className="matching-progress">
          <div className="loading-spinner"></div>
          <p className="matching-progress-text">
            Analyzing your resume against job listings...
          </p>
          <p className="matching-progress-hint">
            This may take a few seconds as AI evaluates each job match.
          </p>
        </div>
      )}

      {isLoading ? (
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <p>Loading matches...</p>
        </div>
      ) : matches.length === 0 && !isRunning ? (
        <div className="empty-state">
          <div className="empty-state-icon">🎯</div>
          <h2 className="empty-state-title">No matches yet</h2>
          <p className="empty-state-text">
            Run AI matching to analyze your resume against job listings and find the best fits.
          </p>
          <button
            onClick={handleRunMatching}
            className="btn btn-primary"
            disabled={isRunning}
          >
            {isRunning ? 'Analyzing...' : 'Run AI Matching'}
          </button>
        </div>
      ) : (
        <div className="matches-list">
          {matches.map((match) => (
            <div key={match.id} className="match-card">
              <div className="match-card-header">
                <div className="match-job-info">
                  <h3 className="match-job-title">
                    {cleanText(match.job?.title || 'Unknown Position')}
                  </h3>
                  <p className="match-job-company">
                    {cleanText(match.job?.company || 'Unknown Company')}
                  </p>
                  {match.job?.location && (
                    <p className="match-job-location">📍 {cleanText(match.job.location)}</p>
                  )}
                </div>
                <div className={`match-score ${getScoreColor(match.fit_score)}`}>
                  <span className="score-number">{match.fit_score}</span>
                  <span className="score-label">{getScoreLabel(match.fit_score)}</span>
                </div>
              </div>

              {match.explanation && (
                <div className="match-explanation">
                  <p className="explanation-label">AI Analysis:</p>
                  <p className="explanation-text">{match.explanation}</p>
                </div>
              )}

              {cardErrors[match.id] && (
                <div className="alert alert-error card-alert">
                  {cardErrors[match.id]}
                  <button
                    onClick={() => setCardErrors((prev) => ({ ...prev, [match.id]: '' }))}
                    className="alert-close"
                  >
                    ×
                  </button>
                </div>
              )}

              {match.has_cover_letter && match.cover_letter ? (
                <div className="cover-letter-section">
                  <div className="cover-letter-header">
                    <button
                      onClick={() => toggleCoverLetter(match.id)}
                      className="cover-letter-toggle"
                    >
                      <span className="cover-letter-icon">
                        {expandedCoverLetters[match.id] ? '▼' : '▶'}
                      </span>
                      Cover Letter
                    </button>
                    <button
                      onClick={() => handleCopyToClipboard(match.id, match.cover_letter)}
                      className="btn btn-secondary btn-sm"
                    >
                      {copySuccess[match.id] ? '✓ Copied!' : 'Copy'}
                    </button>
                  </div>
                  {expandedCoverLetters[match.id] && (
                    <div className="cover-letter-content">
                      <pre className="cover-letter-text">{match.cover_letter}</pre>
                    </div>
                  )}
                </div>
              ) : (
                <div className="cover-letter-section">
                  <button
                    onClick={() => handleGenerateCoverLetter(match.id)}
                    className="btn btn-secondary btn-sm"
                    disabled={generatingForId === match.id}
                  >
                    {generatingForId === match.id ? (
                      <span className="btn-loading">
                        <span className="btn-spinner"></span>
                        Generating...
                      </span>
                    ) : (
                      'Generate Cover Letter'
                    )}
                  </button>
                </div>
              )}

              <div className="match-card-footer">
                <span className="match-date">Matched: {formatDate(match.matched_at)}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default Matches;