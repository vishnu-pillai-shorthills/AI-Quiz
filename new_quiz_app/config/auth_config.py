"""
Microsoft Authentication Configuration
"""
import os
from dotenv import load_dotenv

load_dotenv()

class AuthConfig:
    """Microsoft OAuth Configuration"""
    
    # Microsoft OAuth Configuration
    CLIENT_ID = os.getenv('AZURE_CLIENT_ID')
    CLIENT_SECRET = os.getenv('AZURE_CLIENT_SECRET') 
    TENANT_ID = os.getenv('AZURE_TENANT_ID', 'common')  # 'common' for multi-tenant
    
    # OAuth URLs
    AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
    
    # Scopes - what permissions we want
    SCOPE = ["User.Read"]  # Basic user profile information
    
    # Redirect URI - must match Azure AD app registration
    REDIRECT_PATH = "/auth/callback"
    
    # Session configuration
    SESSION_TYPE = "filesystem"
    SESSION_PERMANENT = False
    SESSION_USE_SIGNER = True
    SESSION_KEY_PREFIX = "quiz_app:"
    
    @classmethod
    def get_redirect_uri(cls, request):
        """Get the full redirect URI for the current request"""
        return request.url_root.rstrip('/') + cls.REDIRECT_PATH
    
    @classmethod
    def is_configured(cls):
        """Check if all required Azure configurations are present"""
        return all([
            cls.CLIENT_ID,
            cls.CLIENT_SECRET,
            cls.TENANT_ID
        ])
    
    @classmethod
    def validate_config(cls):
        """Validate configuration and return any missing values"""
        missing = []
        if not cls.CLIENT_ID:
            missing.append("AZURE_CLIENT_ID")
        if not cls.CLIENT_SECRET:
            missing.append("AZURE_CLIENT_SECRET")
        if not cls.TENANT_ID:
            missing.append("AZURE_TENANT_ID")
        return missing 