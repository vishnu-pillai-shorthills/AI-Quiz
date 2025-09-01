# 🧠 New Modular Quiz Application

A clean, modular quiz application built with Flask, featuring Microsoft authentication, MongoDB storage, and comprehensive quiz management.

## ✨ Features

- **🔐 Microsoft Authentication**: Secure OAuth 2.0 integration with Azure AD
- **📅 Daily Quiz System**: One quiz attempt per day per user
- **💾 Auto-save**: Answers are automatically saved as users progress
- **📊 Progress Tracking**: Real-time progress monitoring and statistics
- **🔄 Resume Support**: Users can resume incomplete quiz attempts
- **👑 Admin Panel**: Quiz management and statistics dashboard
- **📱 Responsive Design**: Modern, mobile-friendly interface

## 🏗️ Architecture

The application follows a clean, modular architecture:

```
new_quiz_app/
├── app/                    # Flask application package
│   ├── routes/            # Route blueprints
│   │   ├── auth.py        # Authentication routes
│   │   ├── main.py        # Main application routes
│   │   └── quiz.py        # Quiz-related routes
│   └── __init__.py        # Application factory
├── config/                 # Configuration files
│   ├── config.py          # Main configuration
│   ├── auth_config.py     # Authentication configuration
│   └── database.py        # Database configuration
├── models/                 # Data models
│   ├── quiz.py            # Quiz model
│   ├── quiz_attempt.py    # Quiz attempt model
│   └── user.py            # User model
├── services/               # Business logic services
│   ├── auth_service.py    # Authentication service
│   └── quiz_service.py    # Quiz management service
├── templates/              # HTML templates
├── static/                 # Static files (CSS, JS, images)
├── utils/                  # Utility functions
├── run.py                  # Application entry point
└── requirements.txt        # Python dependencies
```

## 🚀 Quick Start

### Prerequisites

- **Python 3.8+**
- **MongoDB** (local or cloud)
- **Microsoft Azure App Registration**

### 1. Installation

```bash
# Clone or navigate to project directory
cd new_quiz_app

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Environment Setup

Copy the example environment file and configure it:

```bash
cp env.example .env
```

Edit `.env` with your configuration:

```env
# Flask Configuration
FLASK_CONFIG=development
FLASK_DEBUG=True
SECRET_KEY=your-secret-key-change-this-in-production

# MongoDB Configuration
MONGO_URI=mongodb://localhost:27017/quiz_db

# Microsoft Azure OAuth Configuration
AZURE_CLIENT_ID=your-azure-client-id
AZURE_CLIENT_SECRET=your-azure-client-secret
AZURE_TENANT_ID=your-azure-tenant-id
```

### 3. Microsoft Azure Setup

1. **Create Azure App Registration**:
   - Go to Azure Portal → Azure Active Directory → App registrations
   - Click "New registration"
   - Set name: "Quiz Application"
   - Set redirect URI: `http://localhost:8002/auth/callback`
   - Note the Application (client) ID

2. **Configure Authentication**:
   - Go to Authentication → Add platform → Web
   - Set redirect URI: `http://localhost:8002/auth/callback`
   - Enable "Access tokens" and "ID tokens"

3. **Create Client Secret**:
   - Go to Certificates & secrets → New client secret
   - Set description and expiration
   - Copy the secret value

4. **Update .env file** with your Azure credentials

### 4. Start MongoDB

**Local MongoDB:**
```bash
# Ubuntu/Debian
sudo systemctl start mongodb

# macOS (with Homebrew)
brew services start mongodb-community
```

**Or use MongoDB Atlas (Cloud)**

### 5. Run the Application

```bash
# Run the application
python run.py
```

The application will be available at `http://localhost:8002`

## 📖 Usage Guide

### For Users

1. **Access Quiz**: Visit the application URL
2. **Sign In**: Use Microsoft account to authenticate
3. **Take Quiz**: Answer questions (answers auto-save)
4. **Submit**: Complete and submit the quiz
5. **View Results**: See your score and performance

### For Administrators

1. **Access Admin Panel**: Navigate to `/admin`
2. **Upload Quizzes**: Use the quiz upload form
3. **Monitor Statistics**: View quiz performance metrics
4. **Manage Content**: Upload daily quizzes

### Quiz Format

Quizzes should be in JSON format:

```json
{
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
    }
  ]
}
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `FLASK_CONFIG` | Flask configuration environment | `development` |
| `FLASK_DEBUG` | Enable Flask debug mode | `False` |
| `SECRET_KEY` | Flask secret key | Required |
| `MONGO_URI` | MongoDB connection string | Required |
| `AZURE_CLIENT_ID` | Azure app client ID | Required |
| `AZURE_CLIENT_SECRET` | Azure app client secret | Required |
| `AZURE_TENANT_ID` | Azure tenant ID | `common` |

### MongoDB Collections

The application creates and manages these collections:

- **`quizzes`**: Daily quiz content
- **`attempts`**: User quiz attempts and answers
- **`users`**: Authenticated user information

## 🛡️ Security Features

- **OAuth 2.0 Authentication**: Secure Microsoft authentication
- **CSRF Protection**: State parameter validation
- **Session Management**: Secure session handling
- **Input Validation**: Comprehensive data validation
- **Database Indexes**: Optimized query performance

## 📱 API Endpoints

### Authentication
- `GET /auth/login` - Microsoft login page
- `GET /auth/callback` - OAuth callback handler
- `GET /auth/logout` - User logout
- `GET /auth/profile` - User profile

### Quiz Management
- `GET /quiz/` - Take today's quiz
- `GET /quiz/<date>` - Take quiz for specific date
- `POST /quiz/<date>/save-answer` - Save answer
- `POST /quiz/<date>/submit` - Submit completed quiz
- `GET /quiz/<date>/result` - View quiz result
- `GET /quiz/history` - User quiz history

### Admin Functions
- `GET /admin` - Admin dashboard
- `GET /admin/quizzes` - Quiz management
- `POST /admin/upload-quiz` - Upload new quiz

### System
- `GET /health` - Health check
- `GET /api/quiz-stats/<date>` - Quiz statistics

## 🧪 Testing

```bash
# Run tests (when implemented)
python -m pytest

# Run with coverage
python -m pytest --cov=app
```

## 🚀 Deployment

### Production Configuration

1. **Update Environment**:
   ```env
   FLASK_CONFIG=production
   FLASK_DEBUG=False
   SECRET_KEY=your-production-secret-key
   ```

2. **Use Production WSGI Server**:
   ```bash
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:8002 run:app
   ```

3. **Set up Reverse Proxy** (Nginx recommended)

### Docker Deployment

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8002

CMD ["python", "run.py"]
```

## 🔍 Troubleshooting

### Common Issues

1. **MongoDB Connection Failed**:
   - Check MongoDB service status
   - Verify connection string in `.env`
   - Check network connectivity

2. **Azure Authentication Failed**:
   - Verify Azure app registration
   - Check redirect URI configuration
   - Ensure client secret is correct

3. **Quiz Upload Failed**:
   - Verify JSON format
   - Check file permissions
   - Review application logs

### Debug Mode

```bash
export FLASK_DEBUG=1
python run.py
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Make changes
4. Add tests
5. Submit pull request

## 📝 License

This project is licensed under the MIT License.

## 🆘 Support

For support:
1. Check this README
2. Review application logs
3. Check MongoDB connection
4. Verify Azure configuration

---

**Happy Quizzing! 🧠✨** 