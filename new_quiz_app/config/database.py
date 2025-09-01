"""
Database configuration and connection setup
"""
from flask_pymongo import PyMongo
from pymongo import MongoClient
import os
from config.config import Config

class Database:
    """Database connection and configuration manager"""
    
    def __init__(self, app=None):
        self.app = app
        self.mongo = None
        self.db = None
        self.quizzes_collection = None
        self.attempts_collection = None
        self.users_collection = None
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize database with Flask app"""
        self.app = app
        
        # Configure MongoDB
        app.config["MONGO_URI"] = Config.MONGO_URI
        
        try:
            # Initialize PyMongo
            self.mongo = PyMongo(app)
            self.db = self.mongo.db
            
            # Initialize collections
            self.quizzes_collection = self.db.quizzes
            self.attempts_collection = self.db.attempts
            self.users_collection = self.db.users
            
            # Test connection
            self.db.list_collection_names()
            print("✅ MongoDB connection successful!")
            
            # Create indexes
            self._create_indexes()
            
        except Exception as e:
            print(f"❌ MongoDB connection failed: {e}")
            self.mongo = None
            self.db = None
            self.quizzes_collection = None
            self.attempts_collection = None
            self.users_collection = None
            print("⚠️  Application will run without database functionality")
    
    def _create_indexes(self):
        """Create necessary database indexes"""
        try:
            # Check if collections are available
            if (self.quizzes_collection is None or 
                self.attempts_collection is None or 
                self.users_collection is None):
                print("⚠️ Warning: Collections not available, skipping index creation")
                return
            
            # Quiz indexes
            self.quizzes_collection.create_index("quiz_date", unique=True)
            self.quizzes_collection.create_index("created_at")
            
            # Attempt indexes
            self.attempts_collection.create_index([("user_id", 1), ("quiz_date", 1)], unique=True)
            self.attempts_collection.create_index("quiz_date")
            self.attempts_collection.create_index("attempted_at")
            self.attempts_collection.create_index("user_id")
            
            # User indexes
            self.users_collection.create_index("user_id", unique=True)
            self.users_collection.create_index("email")
            self.users_collection.create_index("last_active")
            
            print("✅ Database indexes created successfully!")
            
        except Exception as e:
            print(f"⚠️ Warning: Could not create indexes: {e}")
    
    def is_connected(self):
        """Check if database connection is available"""
        return (
            self.mongo is not None and 
            self.db is not None and 
            self.quizzes_collection is not None
        )
    
    def get_collections(self):
        """Get database collections"""
        return {
            'quizzes': self.quizzes_collection,
            'attempts': self.attempts_collection,
            'users': self.users_collection
        }
    
    def health_check(self):
        """Perform database health check"""
        if not self.is_connected():
            return False, "Database not connected"
        
        try:
            # Test basic operations
            self.db.list_collection_names()
            return True, "Database healthy"
        except Exception as e:
            return False, f"Database error: {str(e)}"

# Global database instance
db = Database() 