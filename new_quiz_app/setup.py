#!/usr/bin/env python3
"""
Setup script for the Quiz Application
"""
import os
import sys
import json
from pathlib import Path

def create_env_file():
    """Create .env file from template"""
    env_example = Path("env.example")
    env_file = Path(".env")
    
    if env_file.exists():
        print("⚠️  .env file already exists. Skipping creation.")
        return
    
    if not env_example.exists():
        print("❌ env.example file not found. Cannot create .env file.")
        return
    
    # Read template
    with open(env_example, 'r') as f:
        template = f.read()
    
    # Create .env file
    with open(env_file, 'w') as f:
        f.write(template)
    
    print("✅ Created .env file from template.")
    print("📝 Please edit .env file with your configuration values.")

def create_sample_quiz():
    """Create a sample quiz file"""
    sample_quiz = {
        "quiz_date": "2025-01-15",
        "questions": [
            {
                "question": "What is the capital of France?",
                "options": {
                    "A": "London",
                    "B": "Berlin",
                    "C": "Paris",
                    "D": "Madrid"
                },
                "answer": "C"
            },
            {
                "question": "Which planet is known as the Red Planet?",
                "options": {
                    "A": "Venus",
                    "B": "Mars",
                    "C": "Jupiter",
                    "D": "Saturn"
                },
                "answer": "B"
            },
            {
                "question": "What is the largest mammal in the world?",
                "options": {
                    "A": "African Elephant",
                    "B": "Blue Whale",
                    "C": "Giraffe",
                    "D": "Hippopotamus"
                },
                "answer": "B"
            }
        ]
    }
    
    quiz_file = Path("sample_quiz.json")
    if not quiz_file.exists():
        with open(quiz_file, 'w') as f:
            json.dump(sample_quiz, f, indent=2)
        print("✅ Created sample_quiz.json file.")
    else:
        print("⚠️  sample_quiz.json already exists. Skipping creation.")

def check_dependencies():
    """Check if required dependencies are available"""
    print("🔍 Checking dependencies...")
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ is required.")
        return False
    
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    
    # Check if virtual environment is activated
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("✅ Virtual environment is activated.")
    else:
        print("⚠️  Virtual environment is not activated. Consider using one.")
    
    return True

def print_next_steps():
    """Print next steps for setup"""
    print("\n" + "="*50)
    print("🚀 NEXT STEPS TO COMPLETE SETUP")
    print("="*50)
    
    print("\n1. 📝 Configure Environment:")
    print("   - Edit .env file with your configuration")
    print("   - Set AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, AZURE_TENANT_ID")
    print("   - Set MONGO_URI for your MongoDB connection")
    print("   - Set SECRET_KEY for Flask")
    
    print("\n2. 🔐 Microsoft Azure Setup:")
    print("   - Create Azure App Registration")
    print("   - Configure redirect URI: http://localhost:8002/auth/callback")
    print("   - Create client secret")
    print("   - Update .env file with credentials")
    
    print("\n3. 🗄️  MongoDB Setup:")
    print("   - Start MongoDB service")
    print("   - Ensure connection string is correct")
    
    print("\n4. 📦 Install Dependencies:")
    print("   pip install -r requirements.txt")
    
    print("\n5. 🚀 Run Application:")
    print("   python run.py")
    
    print("\n6. 📚 Upload Sample Quiz:")
    print("   - Access admin panel at /admin")
    print("   - Use sample_quiz.json to test the system")
    
    print("\n" + "="*50)

def main():
    """Main setup function"""
    print("🧠 Quiz Application Setup")
    print("="*30)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Create .env file
    create_env_file()
    
    # Create sample quiz
    create_sample_quiz()
    
    # Print next steps
    print_next_steps()
    
    print("\n✅ Setup completed successfully!")
    print("📖 See README.md for detailed instructions.")

if __name__ == "__main__":
    main() 