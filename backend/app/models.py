from datetime import datetime
from app import db
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    """User model for storing user account information."""
    
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    resumes = db.relationship('Resume', backref='owner', lazy=True)
    matches = db.relationship('Match', backref='user', lazy=True)
    
    def set_password(self, password):
        """Hash and store the password."""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Verify a password against the stored hash."""
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.email}>'


class Resume(db.Model):
    """Resume model for storing uploaded resume files and extracted text."""
    
    __tablename__ = 'resumes'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    raw_text = db.Column(db.Text, nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Resume {self.filename}>'
    
    def to_dict(self):
        """Convert resume to dictionary for JSON responses."""
        return {
            'id': self.id,
            'filename': self.filename,
            'raw_text': self.raw_text,
            'uploaded_at': self.uploaded_at.isoformat() if self.uploaded_at else None,
            'text_preview': self.raw_text[:500] + '...' if len(self.raw_text) > 500 else self.raw_text
        }


class Job(db.Model):
    """Job model for storing fetched job listings."""
    
    __tablename__ = 'jobs'
    
    id = db.Column(db.Integer, primary_key=True)
    external_id = db.Column(db.String(100), unique=True, nullable=False)
    title = db.Column(db.String(255), nullable=False)
    company = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    location = db.Column(db.String(255), nullable=True)
    source_url = db.Column(db.String(500), nullable=True)
    source = db.Column(db.String(50), nullable=False, default='RemoteOK')
    fetched_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship with Match model
    matches = db.relationship('Match', backref='job', lazy=True)
    
    def __repr__(self):
        return f'<Job {self.title} at {self.company}>'
    
    def to_dict(self):
        """Convert job to dictionary for JSON responses."""
        return {
            'id': self.id,
            'external_id': self.external_id,
            'title': self.title,
            'company': self.company,
            'description': self.description,
            'location': self.location,
            'source_url': self.source_url,
            'source': self.source,
            'fetched_at': self.fetched_at.isoformat() if self.fetched_at else None
        }


class Match(db.Model):
    """Match model for storing AI-generated job matches and cover letters."""
    
    __tablename__ = 'matches'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    job_id = db.Column(db.Integer, db.ForeignKey('jobs.id'), nullable=False)
    fit_score = db.Column(db.Integer, nullable=False)
    explanation = db.Column(db.Text, nullable=True)
    cover_letter = db.Column(db.Text, nullable=True)  # NEW: Generated cover letter
    matched_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        db.UniqueConstraint('user_id', 'job_id', name='unique_user_job_match'),
    )
    
    def __repr__(self):
        return f'<Match user={self.user_id} job={self.job_id} score={self.fit_score}>'
    
    def to_dict(self):
        """Convert match to dictionary for JSON responses."""
        return {
            'id': self.id,
            'fit_score': self.fit_score,
            'explanation': self.explanation,
            'cover_letter': self.cover_letter,
            'has_cover_letter': self.cover_letter is not None,
            'matched_at': self.matched_at.isoformat() if self.matched_at else None,
            'job': {
                'id': self.job.id,
                'title': self.job.title,
                'company': self.job.company,
                'location': self.job.location
            }
        }