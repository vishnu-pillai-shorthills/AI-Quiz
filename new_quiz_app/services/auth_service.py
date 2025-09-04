"""
Microsoft Authentication Service using MSAL
"""
import msal
from flask import session, request, url_for, current_app
from config.auth_config import AuthConfig
from models.user import User
from config.database import db
import uuid
from datetime import datetime

class AuthService:
    """Service for handling Microsoft authentication"""
    
    def __init__(self):
        self.config = AuthConfig()
    
    def get_msal_app(self):
        """Create MSAL confidential client application"""
        return msal.ConfidentialClientApplication(
            self.config.CLIENT_ID,
            authority=self.config.AUTHORITY,
            client_credential=self.config.CLIENT_SECRET
        )
    
    def get_auth_url(self):
        """Generate Microsoft login URL"""
        msal_app = self.get_msal_app()
        
        # Generate state to prevent CSRF attacks
        session["state"] = str(uuid.uuid4())
        
        # Build authorization URL
        auth_url = msal_app.get_authorization_request_url(
            self.config.SCOPE,
            state=session["state"],
            redirect_uri=self.config.get_redirect_uri(request)
        )
        
        return auth_url
    
    def handle_auth_callback(self, auth_code, state):
        """Handle the OAuth callback and get user information"""
        # Verify state to prevent CSRF attacks
        if state != session.get("state"):
            raise ValueError("Invalid state parameter")
        
        msal_app = self.get_msal_app()
        
        # Exchange authorization code for tokens
        result = msal_app.acquire_token_by_authorization_code(
            auth_code,
            scopes=self.config.SCOPE,
            redirect_uri=self.config.get_redirect_uri(request)
        )
        
        if "error" in result:
            raise Exception(f"Authentication error: {result.get('error_description', result['error'])}")
        
        # Store tokens and user info in session
        session["user"] = result.get("id_token_claims")
        session["access_token"] = result.get("access_token")
        
        # Create or update user in database
        user_info = self._extract_user_info(result.get("id_token_claims"))
        self._create_or_update_user(user_info)
        
        return user_info
    
    def _extract_user_info(self, id_token_claims):
        """Extract user information from ID token claims"""
        return {
            "id": id_token_claims.get("oid", id_token_claims.get("sub")),
            "email": id_token_claims.get("preferred_username", id_token_claims.get("email")),
            "name": id_token_claims.get("name", "Unknown User"),
            "given_name": id_token_claims.get("given_name", ""),
            "family_name": id_token_claims.get("family_name", "")
        }
    
    def _create_or_update_user(self, user_info):
        """Create or update user in database"""
        if not hasattr(db, 'is_connected') or not db.is_connected():
            print("⚠️  Database not connected, skipping user creation")
            return None
        
        try:
            # Check if user exists
            existing_user = db.users_collection.find_one({"user_id": user_info["id"]})
            
            if existing_user:
                # Update existing user
                db.users_collection.update_one(
                    {"user_id": user_info["id"]},
                    {"$set": {
                        "last_active": datetime.utcnow(),
                        "name": user_info["name"],
                        "email": user_info["email"],
                        "given_name": user_info["given_name"],
                        "family_name": user_info["family_name"]
                    }}
                )
                return User.from_dict(existing_user)
            else:
                # Create new user
                new_user = User(
                    user_id=user_info["id"],
                    email=user_info["email"],
                    name=user_info["name"],
                    given_name=user_info["given_name"],
                    family_name=user_info["family_name"]
                )
                
                if new_user.is_valid():
                    result = db.users_collection.insert_one(new_user.to_dict())
                    new_user.id = str(result.inserted_id)
                    return new_user
                
        except Exception as e:
            print(f"Error creating/updating user: {e}")
            return None
    
    def get_current_user(self):
        """Get current authenticated user from session"""
        return session.get("user")
    
    def get_current_user_info(self):
        """Get current user info from database"""
        user_data = self.get_current_user()
        if not user_data or not hasattr(db, 'is_connected') or not db.is_connected():
            return None
        
        try:
            user_id = user_data.get("oid", user_data.get("sub"))
            user_doc = db.users_collection.find_one({"user_id": user_id})
            if user_doc:
                user_obj = User.from_dict(user_doc)
                # Return dictionary representation for template compatibility
                return user_obj.to_dict()
        except Exception as e:
            print(f"Error getting user info: {e}")
        
        return None
    
    def is_authenticated(self):
        """Check if user is currently authenticated"""
        return "user" in session and session["user"] is not None
    
    def logout(self):
        """Clear user session"""
        session.clear()
    
    def get_logout_url(self):
        """Get Microsoft logout URL"""
        return f"{self.config.AUTHORITY}/oauth2/v2.0/logout?post_logout_redirect_uri={request.url_root}"
    
    def require_auth(self, f):
        """Decorator to require authentication for routes"""
        from functools import wraps
        from flask import redirect, url_for, flash
        
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not self.is_authenticated():
                flash("Please sign in to access this page.", "info")
                return redirect(url_for('auth.login'))
            return f(*args, **kwargs)
        return decorated_function
    
    def get_user_id(self):
        """Get current user ID"""
        user = self.get_current_user()
        if user:
            return user.get("oid", user.get("sub"))
        return None
    
    def update_user_activity(self):
        """Update user's last active timestamp"""
        user_info = self.get_current_user_info()
        if user_info and hasattr(db, 'is_connected') and db.is_connected():
            try:
                db.users_collection.update_one(
                    {"user_id": user_info.user_id},
                    {"$set": {"last_active": datetime.utcnow()}}
                )
            except Exception as e:
                print(f"Error updating user activity: {e}") 