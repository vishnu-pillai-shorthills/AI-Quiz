"""
Authentication routes for Microsoft OAuth
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from services.auth_service import AuthService
from config.auth_config import AuthConfig

# Create blueprint
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

# Initialize services
auth_service = AuthService()

@auth_bp.route('/login')
def login():
    """Microsoft login page"""
    if auth_service.is_authenticated():
        return redirect(url_for('main.index'))
    
    # Check if authentication is configured
    missing_config = AuthConfig.validate_config()
    if missing_config:
        flash(f"Microsoft authentication is not configured. Missing: {', '.join(missing_config)}", "error")
        return render_template("auth/error.html", 
                             error="Authentication not configured",
                             missing_config=missing_config)
    
    # Generate login URL
    try:
        auth_url = auth_service.get_auth_url()
        return redirect(auth_url)

    except Exception as e:
        flash(f"Error generating login URL: {str(e)}", "error")
        return render_template("auth/error.html", error="Authentication error")


@auth_bp.route('/callback')
def callback():
    """Handle OAuth callback from Microsoft"""
    try:
        # Get authorization code and state from query parameters
        auth_code = request.args.get('code')
        state = request.args.get('state')
        error = request.args.get('error')
        error_description = request.args.get('error_description')
        
        if error:
            flash(f"Authentication failed: {error_description or error}", "error")
            return redirect(url_for('auth.login'))
        
        if not auth_code or not state:
            flash("Invalid authentication response", "error")
            return redirect(url_for('auth.login'))
        
        # Handle the callback
        user_info = auth_service.handle_auth_callback(auth_code, state)
        
        if user_info:
            return redirect(url_for('main.index'))
        else:
            flash("Authentication completed but user creation failed", "warning")
            return redirect(url_for('main.index'))
            
    except ValueError as e:
        flash(f"Authentication security error: {str(e)}", "error")
        return redirect(url_for('auth.login'))
    except Exception as e:
        flash(f"Authentication error: {str(e)}", "error")
        return redirect(url_for('auth.login'))

@auth_bp.route('/logout')
def logout():
    """Logout user"""
    if auth_service.is_authenticated():
        # Get logout URL for Microsoft
        logout_url = auth_service.get_logout_url()
        
        # Clear local session
        auth_service.logout()
        
        # Don't show flash message for logout as user will be redirected away
        # The Microsoft logout page will handle the logout confirmation
        
        # Redirect to Microsoft logout
        return redirect(logout_url)
    
    # If not authenticated, just redirect to home
    return redirect(url_for('main.index'))

@auth_bp.route('/profile')
def profile():
    """User profile page"""
    if not auth_service.is_authenticated():
        flash("Please sign in to view your profile", "info")
        return redirect(url_for('auth.login'))
    
    user_info = auth_service.get_current_user_info()
    if not user_info:
        flash("Error loading user information", "error")
        return redirect(url_for('main.index'))
    
    return render_template("auth/profile.html", user=user_info) 