from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import time
from app.models import User, Resume, Job, Match
from app import db
from app.services.gemini import match_resume_to_job, generate_cover_letter

# Create a Blueprint for match routes
matches_bp = Blueprint('matches', __name__, url_prefix='/api/matches')

# Configuration for rate limiting
BATCH_SIZE = 5
DELAY_BETWEEN_CALLS = 2

def get_unmatched_jobs(user_id, limit=BATCH_SIZE):
    """Get jobs that haven't been matched yet for this user."""
    matched_job_ids = db.session.query(Match.job_id)\
        .filter(Match.user_id == user_id)\
        .subquery()
    
    unmatched_jobs = Job.query\
        .filter(~Job.id.in_(db.session.query(matched_job_ids.c.job_id)))\
        .limit(limit)\
        .all()
    
    return unmatched_jobs

def process_single_match(user_id, resume_text, job):
    """Match a single job against a resume using Gemini."""
    try:
        result = match_resume_to_job(
            resume_text=resume_text,
            job_title=job.title,
            job_description=job.description or ''
        )
        
        match = Match(
            user_id=user_id,
            job_id=job.id,
            fit_score=result['fit_score'],
            explanation=result['explanation']
        )
        db.session.add(match)
        db.session.commit()
        
        return {
            'success': True,
            'job_id': job.id,
            'job_title': job.title,
            'company': job.company,
            'fit_score': result['fit_score'],
            'explanation': result['explanation']
        }
        
    except Exception as e:
        db.session.rollback()
        return {
            'success': False,
            'job_id': job.id,
            'job_title': job.title,
            'company': job.company,
            'error': str(e)
        }

@matches_bp.route('/run', methods=['POST'])
@jwt_required()
def run_matching():
    """Run AI matching for the current user's resume against jobs."""
    current_user_id = get_jwt_identity()
    
    resume = Resume.query.filter_by(user_id=current_user_id)\
        .order_by(Resume.uploaded_at.desc())\
        .first()
    
    if not resume:
        return jsonify({
            'error': 'No resume found. Please upload a resume first.'
        }), 400
    
    if not resume.raw_text or len(resume.raw_text.strip()) < 50:
        return jsonify({
            'error': 'Resume text is too short or empty. Please upload a valid resume.'
        }), 400
    
    batch_size = request.args.get('batch_size', BATCH_SIZE, type=int)
    batch_size = min(batch_size, 10)
    
    unmatched_jobs = get_unmatched_jobs(current_user_id, limit=batch_size)
    
    if not unmatched_jobs:
        return jsonify({
            'message': 'All jobs have already been matched!',
            'total_matched': Match.query.filter_by(user_id=current_user_id).count()
        }), 200
    
    results = []
    successful = 0
    failed = 0
    
    print(f"Starting matching for {len(unmatched_jobs)} jobs...")
    
    for i, job in enumerate(unmatched_jobs):
        print(f"Processing job {i+1}/{len(unmatched_jobs)}: {job.title} at {job.company}")
        
        result = process_single_match(
            user_id=current_user_id,
            resume_text=resume.raw_text,
            job=job
        )
        results.append(result)
        
        if result['success']:
            successful += 1
        else:
            failed += 1
        
        if i < len(unmatched_jobs) - 1:
            time.sleep(DELAY_BETWEEN_CALLS)
    
    scores = [r['fit_score'] for r in results if r['success']]
    avg_score = sum(scores) / len(scores) if scores else 0
    
    return jsonify({
        'message': f'Processed {len(unmatched_jobs)} jobs',
        'batch_size': len(unmatched_jobs),
        'successful_matches': successful,
        'failed_matches': failed,
        'average_fit_score': round(avg_score, 1),
        'total_matches_in_database': Match.query.filter_by(user_id=current_user_id).count(),
        'results': results
    }), 200

@matches_bp.route('', methods=['GET'])
@jwt_required()
def get_matches():
    """Get all matches for the current user, sorted by fit_score descending."""
    current_user_id = get_jwt_identity()
    
    matches = Match.query.filter_by(user_id=current_user_id)\
        .order_by(Match.fit_score.desc())\
        .all()
    
    if not matches:
        return jsonify({
            'message': 'No matches found. Run matching first.',
            'matches': []
        }), 200
    
    return jsonify({
        'message': f'Found {len(matches)} matches',
        'average_fit_score': round(
            sum(m.fit_score for m in matches) / len(matches), 1
        ),
        'matches': [match.to_dict() for match in matches]
    }), 200

@matches_bp.route('/<int:match_id>', methods=['GET'])
@jwt_required()
def get_match(match_id):
    """Get a single match by ID with full details including cover letter."""
    current_user_id = get_jwt_identity()
    
    match = Match.query.filter_by(id=match_id, user_id=current_user_id).first()
    
    if not match:
        return jsonify({'error': 'Match not found'}), 404
    
    return jsonify({
        'match': match.to_dict()
    }), 200

@matches_bp.route('/<int:match_id>/cover-letter', methods=['POST'])
@jwt_required()
def generate_match_cover_letter(match_id):
    """Generate a cover letter for a specific match.
    
    This endpoint:
    1. Verifies the match belongs to the logged-in user
    2. Gets the resume text and job details
    3. Calls Gemini to generate a tailored cover letter
    4. Saves it to the Match record
    5. Returns the generated cover letter
    
    Args:
        match_id: The ID of the match to generate a cover letter for
        
    Returns:
        JSON with the generated cover letter
    """
    current_user_id = get_jwt_identity()
    
    # Find the match and verify it belongs to this user
    match = Match.query.filter_by(id=match_id, user_id=current_user_id).first()
    
    if not match:
        return jsonify({'error': 'Match not found'}), 404
    
    # Get the resume text for this user
    resume = Resume.query.filter_by(user_id=current_user_id)\
        .order_by(Resume.uploaded_at.desc())\
        .first()
    
    if not resume:
        return jsonify({'error': 'No resume found. Please upload a resume first.'}), 400
    
    # Get the job details
    job = Job.query.get(match.job_id)
    if not job:
        return jsonify({'error': 'Job not found'}), 404
    
    try:
        # Generate the cover letter
        cover_letter = generate_cover_letter(
            resume_text=resume.raw_text,
            job_title=job.title,
            company_name=job.company,
            job_description=job.description or ''
        )
        
        # Save to the match record
        match.cover_letter = cover_letter
        db.session.commit()
        
        return jsonify({
            'message': 'Cover letter generated successfully',
            'match_id': match.id,
            'job_title': job.title,
            'company': job.company,
            'cover_letter': cover_letter
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to generate cover letter: {str(e)}'}), 500

@matches_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_match_stats():
    """Get match statistics for the current user."""
    current_user_id = get_jwt_identity()
    
    matches = Match.query.filter_by(user_id=current_user_id).all()
    
    if not matches:
        return jsonify({
            'message': 'No matches found',
            'total_matches': 0
        }), 200
    
    scores = [m.fit_score for m in matches]
    
    return jsonify({
        'total_matches': len(matches),
        'average_score': round(sum(scores) / len(scores), 1),
        'highest_score': max(scores),
        'lowest_score': min(scores),
        'top_matches': [
            m.to_dict() for m in matches 
            if m.fit_score >= 70
        ][:10]
    }), 200