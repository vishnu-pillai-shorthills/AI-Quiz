"""
Main application routes
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from services.auth_service import AuthService
from services.quiz_service import QuizService
from services.analytics_service import AnalyticsService
from datetime import date

# Create blueprint
main_bp = Blueprint('main', __name__)

# Initialize services
auth_service = AuthService()
quiz_service = QuizService()
analytics_service = AnalyticsService()

@main_bp.route('/')
def index():
    """Main landing page"""
    if not auth_service.is_authenticated():
        return redirect(url_for('auth.login'))
    
    # Get user info
    user_info = auth_service.get_current_user_info()
    user_id = auth_service.get_user_id()
    
    # Get recent quizzes (past 7 days)
    recent_quizzes = quiz_service.get_recent_quizzes(7)
    
    # Add status information for each quiz
    quiz_data = []
    for quiz_info in recent_quizzes:
        quiz_date = quiz_info['quiz_date']
        status = quiz_service.get_user_quiz_status(user_id, quiz_date) if user_id else {
            'status': 'not_attempted',
            'message': 'Please log in to attempt',
            'action': 'login',
            'button_text': 'Login Required',
            'button_class': 'btn-secondary'
        }
        
        quiz_data.append({
            'quiz': quiz_info['quiz'],
            'quiz_date': quiz_date,
            'total_questions': quiz_info['total_questions'],
            'status': status
        })
    
    return render_template("main/index.html", 
                         quiz_data=quiz_data,
                         user=user_info,
                         today=quiz_service.get_today_string())

@main_bp.route('/admin')
def admin_dashboard():
    """Admin dashboard"""
    if not auth_service.is_authenticated():
        flash("Please sign in to access admin panel", "info")
        return redirect(url_for('auth.login'))
    
    # Check if user is admin (you can implement admin role checking here)
    user_info = auth_service.get_current_user_info()
    
    # Get recent quizzes
    recent_quizzes = []
    from config.database import db
    if db.is_connected():
        try:
            recent_quizzes = list(db.quizzes_collection.find(
                {},
                sort=[("created_at", -1)],
                limit=10
            ))
        except Exception as e:
            flash(f"Error loading quizzes: {str(e)}", "error")
    else:
        flash("Database not connected", "warning")
    
    return render_template("admin/dashboard.html", 
                         user=user_info,
                         recent_quizzes=recent_quizzes)

@main_bp.route('/admin/quizzes')
def admin_quizzes():
    """Admin quiz management"""
    if not auth_service.is_authenticated():
        flash("Please sign in to access admin panel", "info")
        return redirect(url_for('auth.login'))
    
    # Get all quizzes
    quizzes = []
    from config.database import db
    if db.is_connected():
        try:
            quizzes = list(db.quizzes_collection.find(
                {},
                sort=[("quiz_date", -1)]
            ))
        except Exception as e:
            flash(f"Error loading quizzes: {str(e)}", "error")
    else:
        flash("Database not connected", "warning")
    
    return render_template("admin/quizzes.html", quizzes=quizzes)

@main_bp.route('/admin/upload-quiz', methods=['GET', 'POST'])
def admin_upload_quiz():
    """Admin quiz upload"""
    if not auth_service.is_authenticated():
        flash("Please sign in to access admin panel", "info")
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        try:
            # Handle quiz upload
            quiz_date = request.form.get('quiz_date')
            quiz_file = request.files.get('quiz_file')
            
            if not quiz_date or not quiz_file:
                flash("Please provide both date and quiz file", "error")
                return render_template("admin/upload_quiz.html")
            
            # Read and parse quiz file
            import json
            quiz_data = json.load(quiz_file)
            quiz_data['quiz_date'] = quiz_date
            
            # Create quiz
            success, message, quiz = quiz_service.create_quiz(quiz_data)
            
            if success:
                flash(f"Quiz uploaded successfully for {quiz_date}", "success")
                return redirect(url_for('main.admin_quizzes'))
            else:
                flash(f"Error uploading quiz: {message}", "error")
                
        except Exception as e:
            flash(f"Error processing quiz file: {str(e)}", "error")
    
    return render_template("admin/upload_quiz.html")

@main_bp.route('/admin/analytics')
@main_bp.route('/admin/analytics/')
def admin_analytics():
    """Admin analytics dashboard"""
    if not auth_service.is_authenticated():
        flash("Please sign in to access admin panel", "info")
        return redirect(url_for('auth.login'))
    
    # Get 7-day analytics
    analytics_data = analytics_service.get_last_7_days_stats()
    
    if "error" in analytics_data:
        flash(f"Error loading analytics: {analytics_data['error']}", "error")
        analytics_data = {"error": analytics_data["error"]}
    
    return render_template("admin/analytics.html", analytics=analytics_data)

@main_bp.route('/admin/analytics/quiz/<quiz_date>')
def admin_quiz_analytics(quiz_date):
    """Detailed analytics for a specific quiz"""
    if not auth_service.is_authenticated():
        flash("Please sign in to access admin panel", "info")
        return redirect(url_for('auth.login'))
    
    # Get detailed quiz analytics
    quiz_analytics = analytics_service.get_quiz_analytics(quiz_date)
    
    if "error" in quiz_analytics:
        flash(f"Error loading quiz analytics: {quiz_analytics['error']}", "error")
    
    return render_template("admin/quiz_analytics.html", 
                         quiz_analytics=quiz_analytics,
                         quiz_date=quiz_date)

@main_bp.route('/api/analytics/7-days', methods=['GET'])
def api_analytics_7_days():
    """API endpoint for 7-day analytics (no authentication required for testing)"""
    try:
        analytics_data = analytics_service.get_last_7_days_stats()
        return jsonify(analytics_data)
    except Exception as e:
        return jsonify({"error": f"Error getting analytics: {str(e)}"}), 500

@main_bp.route('/api/analytics/quiz/<quiz_date>', methods=['GET'])
def api_analytics_quiz(quiz_date):
    """API endpoint for specific quiz analytics (no authentication required for testing)"""
    try:
        quiz_analytics = analytics_service.get_quiz_analytics(quiz_date)
        return jsonify(quiz_analytics)
    except Exception as e:
        return jsonify({"error": f"Error getting quiz analytics: {str(e)}"}), 500

@main_bp.route('/api/debug/session', methods=['GET'])
def debug_session():
    """Debug endpoint to check session data (for troubleshooting authentication)"""
    from flask import session
    return jsonify({
        "session_keys": list(session.keys()),
        "has_user_key": "user" in session,
        "user_value": session.get("user"),
        "is_authenticated": auth_service.is_authenticated(),
        "session_id": session.get("_id", "No session ID"),
        "all_session_data": dict(session) if session else {}
    })

@main_bp.route('/api/admin/analytics', methods=['GET'])
def api_admin_analytics():
    """API endpoint for admin analytics (no authentication required for testing)"""
    try:
        # Get 7-day analytics
        analytics_data = analytics_service.get_last_7_days_stats()
        
        if "error" in analytics_data:
            return jsonify({"error": analytics_data["error"]}), 500
        
        return jsonify(analytics_data)
    except Exception as e:
        return jsonify({"error": f"Error loading analytics: {str(e)}"}), 500

@main_bp.route('/api/upload-quiz-test', methods=['POST'])
def api_upload_quiz_test():
    """API endpoint for uploading quiz without authentication (for testing)"""
    try:
        # Get JSON data from request
        data = request.get_json()
        
        if not data:
            return jsonify({"success": False, "message": "No JSON data provided"}), 400
        
        # Check if data is an array (your format) or object (standard format)
        if isinstance(data, list):
            # Your format: array of questions
            questions = data
            quiz_date = request.args.get('quiz_date') or date.today().strftime('%Y-%m-%d')
            
            # Create quiz data structure
            quiz_data = {
                "quiz_date": quiz_date,
                "questions": questions
            }
        elif isinstance(data, dict):
            # Standard format: object with quiz_date and questions
            quiz_data = data
        else:
            return jsonify({"success": False, "message": "Invalid data format"}), 400
        
        # Validate quiz data
        if 'questions' not in quiz_data:
            return jsonify({"success": False, "message": "Questions array is required"}), 400
        
        if not quiz_data['questions']:
            return jsonify({"success": False, "message": "Questions array cannot be empty"}), 400
        
        # Create quiz
        success, message, quiz = quiz_service.create_quiz(quiz_data)
        
        if success:
            return jsonify({
                "success": True,
                "message": f"Quiz uploaded successfully for {quiz_data['quiz_date']}",
                "quiz_id": str(quiz.id) if hasattr(quiz, 'id') else None,
                "questions_count": len(quiz_data['questions'])
            })
        else:
            return jsonify({"success": False, "message": message}), 400
            
    except Exception as e:
        return jsonify({"success": False, "message": f"Error uploading quiz: {str(e)}"}), 500

@main_bp.route('/api/upload-quiz', methods=['POST'])
def api_upload_quiz():
    """API endpoint for uploading quiz with custom payload format (no authentication required)"""
    try:
        # Get JSON data from request
        data = request.get_json()
        
        if not data:
            return jsonify({"success": False, "message": "No JSON data provided"}), 400
        
        # Check if data is an array (your format) or object (standard format)
        if isinstance(data, list):
            # Your format: array of questions
            questions = data
            quiz_date = request.args.get('quiz_date') or date.today().strftime('%Y-%m-%d')
            
            # Create quiz data structure
            quiz_data = {
                "quiz_date": quiz_date,
                "questions": questions
            }
        elif isinstance(data, dict):
            # Standard format: object with quiz_date and questions
            quiz_data = data
        else:
            return jsonify({"success": False, "message": "Invalid data format"}), 400
        
        # Validate quiz data
        if 'questions' not in quiz_data:
            return jsonify({"success": False, "message": "Questions array is required"}), 400
        
        if not quiz_data['questions']:
            return jsonify({"success": False, "message": "Questions array cannot be empty"}), 400
        
        # Create quiz
        success, message, quiz = quiz_service.create_quiz(quiz_data)
        
        if success:
            return jsonify({
                "success": True,
                "message": f"Quiz uploaded successfully for {quiz_data['quiz_date']}",
                "quiz_id": str(quiz.id) if hasattr(quiz, 'id') else None,
                "questions_count": len(quiz_data['questions'])
            })
        else:
            return jsonify({"success": False, "message": message}), 400
            
    except Exception as e:
        return jsonify({"success": False, "message": f"Error uploading quiz: {str(e)}"}), 500

@main_bp.route('/api/test', methods=['GET'])
def api_test():
    """Simple test endpoint without authentication"""
    return jsonify({
        "success": True,
        "message": "API is working!",
        "timestamp": date.today().isoformat()
    })

@main_bp.route('/health')
def health_check():
    """Health check endpoint"""
    if hasattr(quiz_service, 'db') and quiz_service.db:
        db_healthy, db_message = quiz_service.db.health_check()
    else:
        # Try to get database instance directly
        from config.database import db
        db_healthy, db_message = db.health_check()
    
    return jsonify({
        "status": "healthy" if db_healthy else "unhealthy",
        "database": db_message,
        "timestamp": date.today().isoformat()
    })

@main_bp.route('/api/quiz-stats/<quiz_date>')
def quiz_stats(quiz_date):
    """Get quiz statistics for a specific date"""
    if not auth_service.is_authenticated():
        return jsonify({"error": "Authentication required"}), 401
    
    try:
        stats = quiz_service.get_quiz_statistics(quiz_date)
        
        if "error" in stats:
            return jsonify(stats), 404
        
        return jsonify(stats)
    except Exception as e:
        return jsonify({"error": f"Service error: {str(e)}"}), 500 