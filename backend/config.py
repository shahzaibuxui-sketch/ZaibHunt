import os
from datetime import timedelta
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Base configuration class."""
    
    # Flask secret key
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Database configuration
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///site.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # JWT Configuration
    # JWT_SECRET_KEY is used to sign the tokens - keep it secret!
    # If someone gets this key, they can create fake tokens
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'jwt-secret-key-change-in-production')
    
    # Token expiration time (how long until token expires)
    # timedelta(days=1) = 24 hours
    # After this time, user must login again
    # For development, we set it to 30 days for convenience
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=30)
    
    # Where to look for the JWT in requests
    # 'headers' means look in the Authorization header
    JWT_TOKEN_LOCATION = ['headers']
    
    # The prefix before the token in the Authorization header
    # We'll send: Authorization: Bearer <token>
    JWT_HEADER_TYPE = 'Bearer'