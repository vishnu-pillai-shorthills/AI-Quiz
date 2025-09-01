"""
Quiz routes for taking quizzes and managing attempts
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from services.auth_service import AuthService
from services.quiz_service import QuizService
from datetime import date

# Create blueprint
quiz_bp = Blueprint('quiz', __name__, url_prefix='/quiz')

# Initialize services
auth_service = AuthService()
quiz_service = QuizService()

@quiz_bp.route('/')
@quiz_bp.route('/<quiz_date>')
def take_quiz(quiz_date=None):
    """Take quiz for a specific date or today"""
    if not auth_service.is_authenticated():
        flash("Please sign in to take the quiz", "info")
        return redirect(url_for('auth.login'))
    
    # If no date specified, use today
    if not quiz_date:
        quiz_date = quiz_service.get_today_string()
    
    user_id = auth_service.get_user_id()
    if not user_id:
        flash("Error: Could not identify user", "error")
        return redirect(url_for('auth.login'))
    
    # Check if user has already completed this quiz
    existing_attempt = quiz_service.get_user_attempt(user_id, quiz_date)
    if existing_attempt and existing_attempt.is_completed:
        flash(f"You have already completed the quiz for {quiz_date}. View your results below.", "info")
        return redirect(url_for('quiz.view_result', quiz_date=quiz_date))
    
    # Check if user can attempt this quiz
    can_attempt, message = quiz_service.can_user_attempt_quiz(user_id, quiz_date)
    if not can_attempt:
        flash(message, "warning")
        return redirect(url_for('main.index'))
    
    # Get quiz
    quiz = quiz_service.get_quiz_by_date(quiz_date)
    if not quiz:
        flash(f"No quiz available for date {quiz_date}", "error")
        return redirect(url_for('main.index'))
    
    # Start or resume attempt
    success, message, attempt = quiz_service.start_quiz_attempt(user_id, quiz_date)
    if not success:
        flash(message, "error")
        return redirect(url_for('main.index'))
    
    # Get user's current answers for this attempt
    user_answers = {}
    if attempt and attempt.answers:
        for answer in attempt.answers:
            user_answers[answer['question_index']] = answer['selected_answer']
    
    return render_template("quiz/take_quiz.html", 
                         quiz=quiz, 
                         quiz_date=quiz_date,
                         user_answers=user_answers,
                         attempt=attempt)

@quiz_bp.route('/<quiz_date>/save-answer', methods=['POST'])
def save_answer(quiz_date):
    """Save user's answer for a question"""
    if not auth_service.is_authenticated():
        return jsonify({"success": False, "message": "Authentication required"}), 401
    
    user_id = auth_service.get_user_id()
    if not user_id:
        return jsonify({"success": False, "message": "User identification failed"}), 400
    
    try:
        data = request.get_json()
        question_index = data.get('question_index')
        selected_answer = data.get('selected_answer')
        
        if question_index is None or selected_answer is None:
            return jsonify({"success": False, "message": "Missing question index or answer"}), 400
        
        # Save answer
        success, message = quiz_service.save_answer(user_id, quiz_date, question_index, selected_answer)
        
        if success:
            return jsonify({"success": True, "message": message})
        else:
            return jsonify({"success": False, "message": message}), 400
            
    except Exception as e:
        return jsonify({"success": False, "message": f"Error saving answer: {str(e)}"}), 500

@quiz_bp.route('/<quiz_date>/save-progress', methods=['POST'])
def save_progress(quiz_date):
    """Save multiple answers at once (auto-save)."""
    if not auth_service.is_authenticated():
        return jsonify({"success": False, "message": "Authentication required"}), 401
    
    user_id = auth_service.get_user_id()
    if not user_id:
        return jsonify({"success": False, "message": "User identification failed"}), 400
    
    try:
        data = request.get_json() or {}
        answers = data.get('answers', {})  # {question_index: "A"}
        print(f"🔍 DEBUG save_progress: user_id={user_id}, quiz_date={quiz_date}")
        print(f"🔍 DEBUG received answers: {answers}")
        
        if not isinstance(answers, dict):
            return jsonify({"success": False, "message": "Invalid answers payload"}), 400
        
        if not answers:
            return jsonify({"success": True, "message": "No answers to save"})
        
        # Save each provided answer
        saved_count = 0
        for k, v in answers.items():
            try:
                q_index = int(k)
            except Exception:
                # keys may already be ints
                q_index = k
            if q_index is None or v is None:
                continue
            
            success, msg = quiz_service.save_answer(user_id, quiz_date, q_index, v)
            if success:
                saved_count += 1
            else:
                print(f"⚠️ Failed to save answer {q_index}: {msg}")
        
        print(f"✅ Saved {saved_count} answers")
        return jsonify({"success": True, "message": f"Progress saved ({saved_count} answers)"})
    except Exception as e:
        print(f"❌ Error in save_progress: {e}")
        return jsonify({"success": False, "message": f"Error saving progress: {str(e)}"}), 500

@quiz_bp.route('/<quiz_date>/submit', methods=['POST'])
def submit_quiz(quiz_date):
    """Submit completed quiz"""
    if not auth_service.is_authenticated():
        flash("Please sign in to submit the quiz", "info")
        return redirect(url_for('auth.login'))
    
    user_id = auth_service.get_user_id()
    if not user_id:
        flash("Error: Could not identify user", "error")
        return redirect(url_for('main.index'))
    
    # Submit quiz
    success, message, score_result = quiz_service.submit_quiz(user_id, quiz_date)
    
    if success:
        flash("Quiz submitted successfully!", "success")
        return render_template("quiz/result.html", 
                             quiz_date=quiz_date,
                             score_result=score_result)
    else:
        flash(message, "error")
        return redirect(url_for('quiz.take_quiz', quiz_date=quiz_date))

@quiz_bp.route('/<quiz_date>/result')
def view_result(quiz_date):
    """View quiz result"""
    if not auth_service.is_authenticated():
        flash("Please sign in to view results", "info")
        return redirect(url_for('auth.login'))
    
    user_id = auth_service.get_user_id()
    if not user_id:
        flash("Error: Could not identify user", "error")
        return redirect(url_for('main.index'))
    
    # Get user's attempt
    attempt = quiz_service.get_user_attempt(user_id, quiz_date)
    if not attempt:
        flash("No attempt found for this quiz", "error")
        return redirect(url_for('main.index'))
    
    if not attempt.is_completed:
        flash("Quiz not yet completed", "info")
        return redirect(url_for('quiz.take_quiz', quiz_date=quiz_date))
    
    # Get quiz for question details
    quiz = quiz_service.get_quiz_by_date(quiz_date)
    if not quiz:
        flash("Quiz not found", "error")
        return redirect(url_for('main.index'))
    
    # Prepare result data
    answers_summary = attempt.get_answers_summary()
    print(f"🔍 DEBUG view_result: Found {len(answers_summary)} answers")
    for ans in answers_summary:
        print(f"  Question {ans['question_index']}: {ans['selected_answer']} ({'correct' if ans.get('is_correct') else 'incorrect'})")
    
    # Create a lookup dict for faster answer matching
    answer_lookup = {}
    for ans in answers_summary:
        answer_lookup[ans['question_index']] = ans
    print(f"🔍 DEBUG answer_lookup keys: {list(answer_lookup.keys())}")
    
    result_data = {
        'score': attempt.score,
        'total_questions': attempt.total_questions,
        'percentage': attempt.percentage,
        'completed_at': attempt.completed_at,
        'answers': answers_summary,
        'answer_lookup': answer_lookup,
        'questions': quiz.questions
    }
    
    return render_template("quiz/result.html", 
                         quiz_date=quiz_date,
                         result_data=result_data)

@quiz_bp.route('/history')
def quiz_history():
    """View user's quiz history"""
    if not auth_service.is_authenticated():
        flash("Please sign in to view your history", "info")
        return redirect(url_for('auth.login'))
    
    user_id = auth_service.get_user_id()
    if not user_id:
        flash("Error: Could not identify user", "error")
        return redirect(url_for('main.index'))
    
    # Get user's quiz history
    history = quiz_service.get_user_quiz_history(user_id)
    
    return render_template("quiz/history.html", history=history)

@quiz_bp.route('/<quiz_date>/progress')
def quiz_progress(quiz_date):
    """Get quiz progress for AJAX updates"""
    if not auth_service.is_authenticated():
        return jsonify({"success": False, "message": "Authentication required"}), 401
    
    user_id = auth_service.get_user_id()
    if not user_id:
        return jsonify({"success": False, "message": "User identification failed"}), 400
    
    # Get user's attempt
    attempt = quiz_service.get_user_attempt(user_id, quiz_date)
    if not attempt:
        return jsonify({"success": False, "message": "No attempt found"}), 404
    
    # Get progress information
    progress = attempt.get_progress()
    
    return jsonify({
        "success": True,
        "progress": progress,
        "answers": attempt.get_answers_summary()
    }) 