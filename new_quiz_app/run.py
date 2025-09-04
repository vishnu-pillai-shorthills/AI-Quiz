"""
Main application entry point
"""
import os
from app import create_app

# Create application instance
app = create_app(os.getenv('FLASK_CONFIG') or 'default')

if __name__ == '__main__':
    # Get port from environment or use default
    port = int(os.environ.get('PORT', 8002))
    
    # Run the application
    app.run(
        host='0.0.0.0',
        port=port,
        debug=app.config.get('DEBUG', False)
    ) 