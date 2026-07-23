from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
import requests
from datetime import datetime
from app.models import Job
from app import db

# Create a Blueprint for job routes
jobs_bp = Blueprint('jobs', __name__, url_prefix='/api/jobs')

# RemoteOK API URL - free, no authentication required
REMOTEOK_API_URL = 'https://remoteok.com/api'

def fetch_remoteok_jobs():
    """Fetch job listings from the RemoteOK API.
    
    RemoteOK provides a free API that returns remote job listings.
    No API key or authentication is required.
    
    The API returns a JSON array. The first element is a metadata object,
    and the rest are job listings.
    
    Returns:
        List of job dictionaries from RemoteOK
        
    Raises:
        Exception: If the API request fails
    """
    try:
        # Set a User-Agent header to identify our application
        # Some APIs require this to prevent blocking
        headers = {
            'User-Agent': 'AI-Job-Hunting-Agent/1.0'
        }
        
        # Make the GET request to RemoteOK API
        response = requests.get(REMOTEOK_API_URL, headers=headers, timeout=10)
        
        # Raise an exception if the request failed
        response.raise_for_status()
        
        # Parse the JSON response
        data = response.json()
        
        # RemoteOK returns an array where:
        # - First element (index 0) is API metadata (not a job)
        # - Rest are actual job listings
        if len(data) > 1:
            jobs = data[1:]  # Skip the first element (metadata)
            return jobs
        else:
            return []
            
    except requests.exceptions.RequestException as e:
        raise Exception(f'Failed to fetch jobs from RemoteOK: {str(e)}')
    except ValueError as e:
        raise Exception(f'Failed to parse RemoteOK response: {str(e)}')

def save_job_from_remoteok(job_data):
    """Save a single job from RemoteOK to the database.
    
    Converts RemoteOK's job format to our Job model and saves it.
    Checks for duplicates using external_id.
    
    Args:
        job_data: Dictionary with job data from RemoteOK
        
    Returns:
        True if job was saved, False if it was a duplicate
    """
    # Extract the external ID from RemoteOK's data
    # RemoteOK uses 'id' as their unique identifier
    external_id = str(job_data.get('id', ''))
    
    if not external_id:
        return False
    
    # Check if we already have this job
    existing_job = Job.query.filter_by(external_id=external_id).first()
    if existing_job:
        return False  # Duplicate, skip it
    
    # Create a new Job object from RemoteOK data
    job = Job(
        external_id=external_id,
        title=job_data.get('position', 'Unknown Position'),
        company=job_data.get('company', 'Unknown Company'),
        description=job_data.get('description', ''),
        location=job_data.get('location', 'Remote'),
        source_url=job_data.get('url', ''),
        source='RemoteOK',
        fetched_at=datetime.utcnow()
    )
    
    # Add and commit to database
    db.session.add(job)
    db.session.commit()
    return True

@jobs_bp.route('/fetch', methods=['POST'])
@jwt_required()
def fetch_jobs():
    """Fetch jobs from RemoteOK and save new ones to the database.
    
    This endpoint:
    1. Calls the RemoteOK API to get remote developer jobs
    2. Loops through the results
    3. Saves new jobs (skips duplicates by checking external_id)
    4. Returns a summary of what was done
    
    Returns:
        JSON with count of new jobs added and duplicates skipped
    """
    try:
        # Fetch jobs from RemoteOK API
        remoteok_jobs = fetch_remoteok_jobs()
        
        if not remoteok_jobs:
            return jsonify({
                'message': 'No jobs found from RemoteOK API',
                'new_jobs': 0,
                'duplicates_skipped': 0
            }), 200
        
        # Counters for the summary
        new_jobs_count = 0
        duplicates_count = 0
        
        # Process each job
        for job_data in remoteok_jobs:
            try:
                was_saved = save_job_from_remoteok(job_data)
                if was_saved:
                    new_jobs_count += 1
                else:
                    duplicates_count += 1
            except Exception as e:
                # If saving one job fails, log it but continue with others
                print(f'Error saving job: {str(e)}')
                continue
        
        # Get total jobs in database for context
        total_jobs = Job.query.count()
        
        return jsonify({
            'message': f'Fetched {len(remoteok_jobs)} jobs from RemoteOK',
            'new_jobs_added': new_jobs_count,
            'duplicates_skipped': duplicates_count,
            'total_jobs_in_database': total_jobs
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@jobs_bp.route('', methods=['GET'])
@jwt_required()
def get_jobs():
    """Get all jobs stored in the database.
    
    Supports optional pagination via query parameters:
    - page: Page number (default: 1)
    - per_page: Jobs per page (default: 20, max: 100)
    
    If no pagination params are provided, returns all jobs.
    
    Returns:
        JSON array of jobs
    """
    # Check if pagination parameters are provided
    page = request.args.get('page', type=int)
    per_page = request.args.get('per_page', type=int)
    
    if page and per_page:
        # Limit per_page to maximum 100
        per_page = min(per_page, 100)
        
        # Get paginated results
        # paginate() returns a Pagination object with items, pages, etc.
        pagination = Job.query.order_by(Job.fetched_at.desc())\
            .paginate(page=page, per_page=per_page, error_out=False)
        
        jobs = pagination.items
        
        return jsonify({
            'message': f'Showing page {page} of jobs',
            'page': page,
            'per_page': per_page,
            'total_jobs': pagination.total,
            'total_pages': pagination.pages,
            'has_next': pagination.has_next,
            'has_prev': pagination.has_prev,
            'jobs': [job.to_dict() for job in jobs]
        }), 200
    else:
        # No pagination - return all jobs
        jobs = Job.query.order_by(Job.fetched_at.desc()).all()
        
        return jsonify({
            'message': f'Found {len(jobs)} jobs',
            'total_jobs': len(jobs),
            'jobs': [job.to_dict() for job in jobs]
        }), 200

@jobs_bp.route('/<int:job_id>', methods=['GET'])
@jwt_required()
def get_job(job_id):
    """Get a single job by its ID.
    
    Args:
        job_id: The internal ID of the job
        
    Returns:
        JSON with job details or 404 error
    """
    job = Job.query.get(job_id)
    
    if not job:
        return jsonify({'error': 'Job not found'}), 404
    
    return jsonify({
        'job': job.to_dict()
    }), 200