"""
Flask application factory
"""
from flask import Flask
from flask_session import Session
from config.config import config
from config.database import db
from services.auth_service import AuthService
import os

def create_app(config_name='default'):
    """Create and configure Flask application"""
    
    # Create Flask app
    app = Flask(__name__, template_folder='../templates', static_folder='../static')
    
    # Load configuration
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    
    # Initialize extensions
    db.init_app(app)
    
    # Configure Flask-Session
    Session(app)
    
    # Handle HTTPS in production (behind reverse proxy)
    @app.before_request
    def force_https():
        from flask import request, redirect, url_for
        # Only force HTTPS for production (non-localhost domains)
        if (request.headers.get('X-Forwarded-Proto') == 'http' and 
            not request.host.startswith('localhost') and 
            not request.host.startswith('127.0.0.1')):
            return redirect(request.url.replace('http://', 'https://'))
    
    # Initialize authentication service
    auth_service = AuthService()
    
    # Register blueprints
    from app.routes.main import main_bp
    from app.routes.auth import auth_bp
    from app.routes.quiz import quiz_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(quiz_bp)
    
    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        from flask import render_template
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        from flask import render_template
        return render_template('errors/500.html'), 500
    
    # Context processors
    @app.context_processor
    def utility_processor():
        """Make utility functions available in templates"""
        def format_date(date_obj):
            """Format date for display"""
            if date_obj:
                return date_obj.strftime('%B %d, %Y')
            return ''
        
        def get_quiz_service():
            """Get quiz service instance"""
            from services.quiz_service import QuizService
            return QuizService()
        
        return {
            'format_date': format_date,
            'get_quiz_service': get_quiz_service
        }
    
    @app.context_processor
    def auth_processor():
        """Make authentication info available in templates"""
        from services.auth_service import AuthService
        auth_service = AuthService()
        return {
            'current_user': auth_service.get_current_user_info() if auth_service.is_authenticated() else None
        }
    
    # Before request
    @app.before_request
    def before_request():
        """Handle pre-request tasks"""
        # Update user activity if authenticated
        if auth_service.is_authenticated():
            auth_service.update_user_activity()
    
    return app
