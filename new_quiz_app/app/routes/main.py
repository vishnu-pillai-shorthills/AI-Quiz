"""
Main application routes
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from services.auth_service import AuthService
from services.quiz_service import QuizService
from datetime import date

# Create blueprint
main_bp = Blueprint('main', __name__)

# Initialize services
auth_service = AuthService()
quiz_service = QuizService()

@main_bp.route('/')
def index():
    """Main landing page"""
    if not auth_service.is_authenticated():
        return redirect(url_for('auth.login'))
    
    # Get today's quiz
    today = quiz_service.get_today_string()
    quiz = quiz_service.get_todays_quiz()
    
    if not quiz:
        return render_template("main/no_quiz.html", date=today)
    
    # Get user info
    user_info = auth_service.get_current_user_info()
    
    # Check if user has attempted today's quiz
    user_id = auth_service.get_user_id()
    user_attempt = None
    can_attempt = True
    attempt_message = ""
    
    if user_id:
        can_attempt, attempt_message = quiz_service.can_user_attempt_quiz(user_id, today)
        if not can_attempt:
            user_attempt = quiz_service.get_user_attempt(user_id, today)
    
    return render_template("main/index.html", 
                         quiz=quiz,
                         today=today,
                         user=user_info,
                         can_attempt=can_attempt,
                         attempt_message=attempt_message,
                         user_attempt=user_attempt)

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
    if hasattr(quiz_service, 'db') and quiz_service.db and quiz_service.db.is_connected():
        try:
            recent_quizzes = list(quiz_service.db.quizzes_collection.find(
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
    if hasattr(quiz_service, 'db') and quiz_service.db and quiz_service.db.is_connected():
        try:
            quizzes = list(quiz_service.db.quizzes_collection.find(
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