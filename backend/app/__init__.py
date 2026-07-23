from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_jwt_extended import JWTManager

# Create extensions without app (factory pattern)
db = SQLAlchemy()
jwt = JWTManager()

def create_app():
    """Application factory function."""
    
    app = Flask(__name__)
    
    # Configure maximum file upload size (16MB)
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB
    
    # Load configuration
    app.config.from_object('config.Config')
    
    # Initialize extensions
    db.init_app(app)
    CORS(app)
    jwt.init_app(app)
    
    # Register blueprints
    from app.routes.health import health_bp
    app.register_blueprint(health_bp)
    
    from app.routes.auth import auth_bp
    app.register_blueprint(auth_bp)
    
    from app.routes.resume import resume_bp
    app.register_blueprint(resume_bp)
    
    from app.routes.jobs import jobs_bp
    app.register_blueprint(jobs_bp)
    
    from app.routes.matches import matches_bp
    app.register_blueprint(matches_bp)
    
    # Create database tables
    from app import models
    with app.app_context():
        db.create_all()
        print("Database tables created successfully!")
    
    return app