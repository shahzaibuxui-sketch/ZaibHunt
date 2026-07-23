from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import pdfplumber
from io import BytesIO
from app.models import Resume, User
from app import db

# Create a Blueprint for resume routes
# All routes in this file will start with /api/resume
resume_bp = Blueprint('resume', __name__, url_prefix='/api/resume')

# Allowed file extensions
ALLOWED_EXTENSIONS = {'pdf'}

def allowed_file(filename):
    """Check if the uploaded file has an allowed extension.
    
    Args:
        filename: The name of the uploaded file
        
    Returns:
        True if file extension is allowed, False otherwise
    """
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_from_pdf(file):
    """Extract text from a PDF file using pdfplumber.
    
    pdfplumber is a library that can read PDF files and extract
    text, tables, and metadata. We use it to get the text content
    of resumes so we can analyze them later with AI.
    
    Args:
        file: A file object (from request.files)
        
    Returns:
        Extracted text as a string
        
    Raises:
        ValueError: If the PDF is invalid or can't be read
    """
    try:
        # pdfplumber.open() can work with file paths or BytesIO objects
        # BytesIO lets us treat the uploaded file data as a file-like object
        with pdfplumber.open(BytesIO(file.read())) as pdf:
            text_parts = []
            
            # Iterate through each page of the PDF
            for page in pdf.pages:
                # Extract text from the current page
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
            
            # Join all pages with newlines between them
            full_text = '\n'.join(text_parts)
            
            if not full_text.strip():
                raise ValueError('No text could be extracted from the PDF. The file might be scanned or image-based.')
            
            return full_text
            
    except Exception as e:
        # Re-raise with a more user-friendly message
        raise ValueError(f'Failed to extract text from PDF: {str(e)}')

@resume_bp.route('/upload', methods=['POST'])
@jwt_required()
def upload_resume():
    """Upload a resume PDF and extract its text.
    
    This endpoint:
    1. Requires a valid JWT token (user must be logged in)
    2. Accepts a PDF file via multipart/form-data
    3. Extracts text from the PDF
    4. Saves the extracted text to the database
    5. Returns the extracted text and metadata
    
    Request format: multipart/form-data
    - Field name for the file: 'resume'
    - Header: Authorization: Bearer <token>
    
    Returns:
        JSON with extracted text and resume metadata
    """
    # Check if a file was included in the request
    if 'resume' not in request.files:
        return jsonify({'error': 'No file provided. Please upload a PDF file with the field name "resume".'}), 400
    
    file = request.files['resume']
    
    # Check if a filename was provided
    if file.filename == '':
        return jsonify({'error': 'No file selected. Please choose a PDF file.'}), 400
    
    # Check file extension
    if not allowed_file(file.filename):
        return jsonify({
            'error': 'Invalid file type. Only PDF files are allowed.',
            'allowed_extensions': list(ALLOWED_EXTENSIONS)
        }), 400
    
    try:
        # Extract text from the PDF
        extracted_text = extract_text_from_pdf(file)
        
        # Get the current user's ID from the JWT token
        current_user_id = get_jwt_identity()
        
        # Verify the user exists
        user = User.query.get(current_user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Create a new Resume record in the database
        resume = Resume(
            user_id=current_user_id,
            filename=file.filename,
            raw_text=extracted_text
        )
        
        # Save to database
        db.session.add(resume)
        db.session.commit()
        
        # Return success response
        return jsonify({
            'message': 'Resume uploaded and processed successfully',
            'resume': resume.to_dict()
        }), 201
        
    except ValueError as e:
        # Handle PDF parsing errors
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        # Handle unexpected errors
        db.session.rollback()  # Undo any partial database changes
        return jsonify({'error': f'An unexpected error occurred: {str(e)}'}), 500

@resume_bp.route('/me', methods=['GET'])
@jwt_required()
def get_my_resume():
    """Get the most recent resume for the logged-in user.
    
    This endpoint returns the latest resume uploaded by the
    currently authenticated user. If the user has uploaded
    multiple resumes, only the most recent one is returned.
    
    Returns:
        JSON with the most recent resume data
    """
    # Get the current user's ID from the JWT token
    current_user_id = get_jwt_identity()
    
    # Query for the most recent resume for this user
    # order_by(Resume.uploaded_at.desc()) sorts by upload date, newest first
    # .first() returns the first result (newest) or None
    resume = Resume.query.filter_by(user_id=current_user_id)\
        .order_by(Resume.uploaded_at.desc())\
        .first()
    
    if not resume:
        return jsonify({
            'message': 'No resume found. Please upload a resume first.',
            'resume': None
        }), 404
    
    return jsonify({
        'message': 'Resume retrieved successfully',
        'resume': resume.to_dict()
    }), 200

@resume_bp.route('/history', methods=['GET'])
@jwt_required()
def get_resume_history():
    """Get all resumes for the logged-in user.
    
    This endpoint returns ALL resumes uploaded by the currently
    authenticated user, ordered by upload date (newest first).
    This is useful if you want to let users see their upload history.
    
    Returns:
        JSON array of all resumes
    """
    current_user_id = get_jwt_identity()
    
    resumes = Resume.query.filter_by(user_id=current_user_id)\
        .order_by(Resume.uploaded_at.desc())\
        .all()
    
    if not resumes:
        return jsonify({
            'message': 'No resumes found. Please upload a resume first.',
            'resumes': []
        }), 200
    
    return jsonify({
        'message': f'Found {len(resumes)} resume(s)',
        'resumes': [resume.to_dict() for resume in resumes]
    }), 200