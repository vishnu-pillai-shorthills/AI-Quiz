# 🧠 AI Quiz Application

A modern, interactive quiz platform built with Flask and MongoDB, featuring Microsoft Azure authentication, real-time analytics, and a beautiful responsive UI.

## ✨ Features

- **🔐 Microsoft OAuth Authentication** - Secure login with Azure AD
- **📊 Advanced Analytics Dashboard** - Track participation, scores, and performance
- **🎯 Interactive Quiz Interface** - Modern, Kahoot-like design with auto-save
- **👑 Leaderboards** - Top performers tracking and rankings
- **📱 Responsive Design** - Works seamlessly on desktop and mobile
- **⚡ Real-time Progress Tracking** - Auto-save answers and resume capability
- **🎨 Professional UI** - Clean, modern interface with dark theme
- **📈 Admin Dashboard** - Comprehensive quiz management and analytics

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- MongoDB (Local installation or MongoDB Atlas)
- Microsoft Azure App Registration (for authentication)
- Git

### 1. Clone the Repository

```bash
git clone <your-repository-url>
cd ai-quiz-application
```

### 2. Navigate to Application Directory

```bash
cd new_quiz_app
```

### 3. Create Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 4. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 5. Setup Environment Variables

```bash
cp env.example .env
```

Edit `.env` file with your configuration:

```env
FLASK_CONFIG=development
FLASK_DEBUG=True
SECRET_KEY="your-super-secret-flask-session-key-change-this"
MONGO_URI="mongodb://localhost:27017/ai_quiz"
# OR for MongoDB Atlas:
# MONGO_URI="mongodb+srv://username:password@cluster.mongodb.net/ai_quiz?retryWrites=true&w=majority"

# Azure Authentication
AZURE_CLIENT_ID="your-azure-client-id"
AZURE_CLIENT_SECRET="your-azure-client-secret"
AZURE_TENANT_ID="your-azure-tenant-id"

# Server Configuration
PORT=8003
```

### 6. Setup Database

#### Option A: Local MongoDB
```bash
# Install MongoDB (Ubuntu/Debian)
sudo apt update
sudo apt install -y mongodb

# Start MongoDB service
sudo systemctl start mongod
sudo systemctl enable mongod
```

#### Option B: MongoDB Atlas (Cloud)
1. Create account at [MongoDB Atlas](https://www.mongodb.com/atlas)
2. Create a cluster
3. Get connection string and update `MONGO_URI` in `.env`

### 7. Setup Azure Authentication

1. Go to [Azure Portal](https://portal.azure.com)
2. Navigate to "App registrations"
3. Create new registration:
   - Name: `AI Quiz App`
   - Redirect URI: `http://localhost:8003/auth/callback`
4. Note down:
   - Application (client) ID → `AZURE_CLIENT_ID`
   - Directory (tenant) ID → `AZURE_TENANT_ID`
5. Create client secret:
   - Go to "Certificates & secrets"
   - Create new client secret → `AZURE_CLIENT_SECRET`

### 8. Run the Application

```bash
python3 run.py
```

The application will be available at: `http://localhost:8003`

## 📖 Usage

### User Interface

1. **Homepage** - View available quizzes for the past 7 days
2. **Take Quiz** - Interactive quiz interface with auto-save
3. **Results** - Detailed score breakdown and review answers
4. **Leaderboards** - See top performers

### Admin Interface

Access admin dashboard at: `http://localhost:8003/admin`

- **📊 Analytics Dashboard** - View participation statistics
- **📝 Quiz Management** - Upload and manage quizzes
- **📈 Performance Reports** - Detailed analytics per quiz

### API Endpoints

#### Public Endpoints
- `GET /health` - Health check
- `GET /api/analytics/7-days` - Get 7-day analytics data
- `GET /api/analytics/quiz/{date}` - Get specific quiz analytics

#### Authenticated Endpoints
- `GET /admin/analytics` - Admin analytics dashboard
- `POST /api/upload-quiz` - Upload new quiz

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `FLASK_CONFIG` | Flask configuration mode | No | `development` |
| `FLASK_DEBUG` | Enable debug mode | No | `True` |
| `SECRET_KEY` | Flask session secret key | Yes | - |
| `MONGO_URI` | MongoDB connection string | Yes | - |
| `AZURE_CLIENT_ID` | Azure app client ID | Yes | - |
| `AZURE_CLIENT_SECRET` | Azure app client secret | Yes | - |
| `AZURE_TENANT_ID` | Azure tenant ID | Yes | - |
| `PORT` | Server port | No | `8003` |

### Quiz Data Format

Upload quizzes using JSON format:

```json
[
  {
    "question": "What is artificial intelligence?",
    "options": {
      "A": "Human intelligence",
      "B": "Machine intelligence",
      "C": "Natural intelligence",
      "D": "Emotional intelligence"
    },
    "answer": "B"
  }
]
```

## 🚀 Deployment

### Production Deployment

1. **Set Production Environment**:
```bash
export FLASK_CONFIG=production
export FLASK_DEBUG=False
```

2. **Use Production Database**:
   - Use MongoDB Atlas or dedicated MongoDB server
   - Update `MONGO_URI` with production connection string

3. **Secure Configuration**:
   - Generate strong `SECRET_KEY`
   - Use environment variables for sensitive data
   - Configure proper Azure redirect URIs

4. **Run with Production Server**:
```bash
# Install gunicorn
pip install gunicorn

# Run with gunicorn
gunicorn -w 4 -b 0.0.0.0:8003 run:app
```

### Docker Deployment (Optional)

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8003

CMD ["python3", "run.py"]
```

## 📊 Analytics Features

- **📈 Daily Statistics** - Participation rates and average scores
- **🏆 Top Performers** - Leaderboards with medals and rankings
- **📋 Detailed Reports** - Question-wise analysis and score distribution
- **📱 Export Data** - CSV export for external analysis
- **🎯 Completion Rates** - Track quiz engagement metrics

## 🛠️ Development

### Project Structure

```
new_quiz_app/
├── app/                    # Flask application
│   ├── __init__.py        # App factory
│   └── routes/            # Route blueprints
├── config/                # Configuration files
├── models/                # Data models
├── services/              # Business logic
├── templates/             # Jinja2 templates
├── static/                # CSS, JS, images
├── utils/                 # Utility functions
├── requirements.txt       # Python dependencies
├── run.py                # Application entry point
└── env.example           # Environment template
```

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-flask

# Run tests
pytest
```

### Adding New Features

1. Create new routes in `app/routes/`
2. Add business logic in `services/`
3. Create templates in `templates/`
4. Update models if needed in `models/`

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Troubleshooting

### Common Issues

1. **Port already in use**:
```bash
# Kill existing processes
pkill -f "python.*run.py"
# Or change port in .env file
```

2. **MongoDB connection failed**:
   - Check MongoDB is running: `sudo systemctl status mongod`
   - Verify connection string in `.env`
   - Check network connectivity for Atlas

3. **Azure authentication not working**:
   - Verify Azure app registration settings
   - Check redirect URI matches your domain
   - Ensure client secret is not expired

4. **Template not found errors**:
   - Verify template paths in Flask app initialization
   - Check file permissions

### Getting Help

- 📧 Create an issue on GitHub
- 📖 Check the [documentation](docs/)
- 💬 Join our community discussions

## 🏆 Acknowledgments

- Built with [Flask](https://flask.palletsprojects.com/)
- UI powered by [Bootstrap](https://getbootstrap.com/)
- Charts using [Chart.js](https://www.chartjs.org/)
- Authentication via [Microsoft Azure](https://azure.microsoft.com/)
- Database by [MongoDB](https://www.mongodb.com/)

---

**🚀 Happy Quizzing!** 

Made with ❤️ for interactive learning experiences. 