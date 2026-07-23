// src/pages/Resume.jsx
import { useState, useEffect, useRef } from 'react';
import { uploadResume, getMyResume } from '../api/resume';

function Resume() {
  const [resume, setResume] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');
  const fileInputRef = useRef(null);

  useEffect(() => {
    loadResume();
  }, []);

  const loadResume = async () => {
    setIsLoading(true);
    setError('');
    try {
      const data = await getMyResume();
      setResume(data);
    } catch (err) {
      setError('Failed to load resume. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleFileChange = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    if (file.type !== 'application/pdf' && !file.name.endsWith('.pdf')) {
      setError('Only PDF files are allowed.');
      return;
    }

    if (file.size > 16 * 1024 * 1024) {
      setError('File size must be less than 16MB.');
      return;
    }

    setError('');
    setSuccessMessage('');
    setIsUploading(true);

    try {
      const uploadedResume = await uploadResume(file);
      setResume(uploadedResume);
      setSuccessMessage('Resume uploaded successfully!');
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    } catch (err) {
      const message = err.response?.data?.error || 'Failed to upload resume. Please try again.';
      setError(message);
    } finally {
      setIsUploading(false);
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  if (isLoading) {
    return (
      <div className="loading-container">
        <div className="loading-spinner"></div>
        <p>Loading resume...</p>
      </div>
    );
  }

  return (
    <div className="resume-container">
      <div className="resume-header">
        <h1 className="resume-title">My Resume</h1>
      </div>

      {error && <div className="alert alert-error">{error}</div>}
      {successMessage && <div className="alert alert-success">{successMessage}</div>}

      <div className="resume-upload-section">
        <h2 className="section-title">
          {resume ? 'Update Your Resume' : 'Upload Your Resume'}
        </h2>
        <p className="section-description">
          Upload a PDF of your resume to get AI-powered job matches.
        </p>

        <div className="file-upload-area">
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf"
            onChange={handleFileChange}
            className="file-input"
            id="resume-file"
            disabled={isUploading}
          />
          <label htmlFor="resume-file" className="file-upload-label">
            {isUploading ? (
              <span className="upload-text">Uploading...</span>
            ) : (
              <span className="upload-text">
                <span className="upload-icon">📄</span>
                Choose PDF File
              </span>
            )}
          </label>
          <p className="file-hint">Accepted: PDF files only (max 16MB)</p>
        </div>
      </div>

      {resume && (
        <div className="resume-details">
          <h2 className="section-title">Uploaded Resume</h2>
          <div className="resume-info-card">
            <div className="resume-info-row">
              <span className="info-label">Filename:</span>
              <span className="info-value">{resume.filename}</span>
            </div>
            <div className="resume-info-row">
              <span className="info-label">Uploaded:</span>
              <span className="info-value">{formatDate(resume.uploaded_at)}</span>
            </div>
          </div>

          {resume.text_preview && (
            <div className="resume-preview">
              <h3 className="preview-title">Text Preview</h3>
              <div className="preview-content">
                <pre className="preview-text">{resume.text_preview}</pre>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default Resume;