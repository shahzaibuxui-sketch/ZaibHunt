from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
import requests
import os
from datetime import datetime
from app.models import Job
from app import db

# Create a Blueprint for job routes
jobs_bp = Blueprint('jobs', __name__, url_prefix='/api/jobs')

# Adzuna API configuration
ADZUNA_APP_ID = os.getenv('ADZUNA_APP_ID')
ADZUNA_APP_KEY = os.getenv('ADZUNA_APP_KEY')
ADZUNA_COUNTRY = 'us'  # Can be changed to 'gb', 'au', etc.
ADZUNA_API_URL = f'https://api.adzuna.com/v1/api/jobs/{ADZUNA_COUNTRY}/search/1'


def fetch_adzuna_jobs(search_term='developer', results_per_page=20):
    """Fetch job listings from the Adzuna API.

    Adzuna requires an app_id and app_key (both free, from
    developer.adzuna.com). Returns a JSON object with a 'results' array
    of job listings.

    Args:
        search_term: Keyword to search for (default: 'developer')
        results_per_page: Number of jobs to fetch (max ~50 on free tier)

    Returns:
        List of job dictionaries from Adzuna

    Raises:
        Exception: If the API request fails or credentials are missing
    """
    if not ADZUNA_APP_ID or not ADZUNA_APP_KEY:
        raise Exception('Adzuna API credentials are not configured (ADZUNA_APP_ID / ADZUNA_APP_KEY)')

    try:
        params = {
            'app_id': ADZUNA_APP_ID,
            'app_key': ADZUNA_APP_KEY,
            'results_per_page': results_per_page,
            'what': search_term,
            'content-type': 'application/json'
        }

        response = requests.get(ADZUNA_API_URL, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()
        return data.get('results', [])

    except requests.exceptions.RequestException as e:
        raise Exception(f'Failed to fetch jobs from Adzuna: {str(e)}')
    except ValueError as e:
        raise Exception(f'Failed to parse Adzuna response: {str(e)}')


def save_job_from_adzuna(job_data):
    """Save a single job from Adzuna to the database.

    Converts Adzuna's job format to our Job model and saves it.
    Checks for duplicates using external_id.

    Args:
        job_data: Dictionary with job data from Adzuna

    Returns:
        True if job was saved, False if it was a duplicate
    """
    # Adzuna uses 'id' as their unique identifier
    external_id = str(job_data.get('id', ''))

    if not external_id:
        return False

    # Check if we already have this job
    existing_job = Job.query.filter_by(external_id=external_id).first()
    if existing_job:
        return False  # Duplicate, skip it

    # Adzuna nests company and location as objects with a display_name
    company_obj = job_data.get('company', {}) or {}
    location_obj = job_data.get('location', {}) or {}

    company_name = company_obj.get('display_name', 'Unknown Company')
    location_name = location_obj.get('display_name', 'Remote')

    job = Job(
        external_id=external_id,
        title=job_data.get('title', 'Unknown Position'),
        company=company_name,
        description=job_data.get('description', ''),
        location=location_name,
        source_url=job_data.get('redirect_url', ''),
        source='Adzuna',
        fetched_at=datetime.utcnow()
    )

    db.session.add(job)
    db.session.commit()
    return True


@jobs_bp.route('/fetch', methods=['POST'])
@jwt_required()
def fetch_jobs():
    """Fetch jobs from Adzuna and save new ones to the database.

    This endpoint:
    1. Calls the Adzuna API to get job listings
    2. Loops through the results
    3. Saves new jobs (skips duplicates by checking external_id)
    4. Returns a summary of what was done

    Returns:
        JSON with count of new jobs added and duplicates skipped
    """
    try:
        adzuna_jobs = fetch_adzuna_jobs()

        if not adzuna_jobs:
            return jsonify({
                'message': 'No jobs found from Adzuna API',
                'new_jobs': 0,
                'duplicates_skipped': 0
            }), 200

        new_jobs_count = 0
        duplicates_count = 0

        for job_data in adzuna_jobs:
            try:
                was_saved = save_job_from_adzuna(job_data)
                if was_saved:
                    new_jobs_count += 1
                else:
                    duplicates_count += 1
            except Exception as e:
                print(f'Error saving job: {str(e)}')
                continue

        total_jobs = Job.query.count()

        return jsonify({
            'message': f'Fetched {len(adzuna_jobs)} jobs from Adzuna',
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
    page = request.args.get('page', type=int)
    per_page = request.args.get('per_page', type=int)

    if page and per_page:
        per_page = min(per_page, 100)

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
