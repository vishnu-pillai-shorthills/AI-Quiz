"""
Quiz service for managing quizzes and user attempts
"""
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional, Tuple
from models.quiz import Quiz
from models.quiz_attempt import QuizAttempt
from models.user import User
from config.database import db
from config.config import Config

class QuizService:
    """Service for managing quiz operations"""
    
    def __init__(self):
        self.config = Config()
    
    def get_today_string(self) -> str:
        """Get today's date as string in YYYY-MM-DD format"""
        return date.today().strftime('%Y-%m-%d')
    
    def get_quiz_by_date(self, quiz_date: str) -> Optional[Quiz]:
        """Get quiz for a specific date"""
        if not db.is_connected():
            print("⚠️  Database not connected, returning None")
            return None
        
        try:
            quiz_doc = db.quizzes_collection.find_one({"quiz_date": quiz_date})
            if quiz_doc:
                return Quiz.from_dict(quiz_doc)
        except Exception as e:
            print(f"Error getting quiz: {e}")
        
        return None
    
    def get_todays_quiz(self) -> Optional[Quiz]:
        """Get today's quiz"""
        return self.get_quiz_by_date(self.get_today_string())
    
    def get_recent_quizzes(self, days: int = 7) -> List[Dict]:
        """Get quizzes from the past N days with attempt status for user"""
        if not db.is_connected():
            print("⚠️  Database not connected, returning empty list")
            return []
        
        try:
            # Calculate date range
            today = date.today()
            start_date = today - timedelta(days=days-1)  # Include today
            
            # Generate list of dates
            date_list = []
            for i in range(days):
                check_date = start_date + timedelta(days=i)
                date_list.append(check_date.strftime('%Y-%m-%d'))
            
            # Get quizzes for these dates
            quizzes = list(db.quizzes_collection.find({
                "quiz_date": {"$in": date_list}
            }).sort("quiz_date", -1))  # Most recent first
            
            # Convert to Quiz objects
            quiz_list = []
            for quiz_doc in quizzes:
                quiz = Quiz.from_dict(quiz_doc)
                quiz_list.append({
                    'quiz': quiz,
                    'quiz_date': quiz.quiz_date,
                    'total_questions': quiz.total_questions
                })
            
            return quiz_list
            
        except Exception as e:
            print(f"Error getting recent quizzes: {e}")
            return []
    
    def get_user_quiz_status(self, user_id: str, quiz_date: str) -> Dict:
        """Get user's status for a specific quiz"""
        attempt = self.get_user_attempt(user_id, quiz_date)
        
        if not attempt:
            return {
                'status': 'not_attempted',
                'message': 'Ready to start',
                'action': 'attempt',
                'button_text': '🚀 Start Quiz',
                'button_class': 'btn-success'
            }
        elif attempt.is_completed:
            return {
                'status': 'completed',
                'message': f'Completed with {attempt.score}/{attempt.total_questions} ({attempt.percentage:.0f}%)',
                'action': 'view_results',
                'button_text': '📊 View Results',
                'button_class': 'btn-primary'
            }
        else:
            return {
                'status': 'in_progress',
                'message': f'In progress ({len(attempt.answers)} questions answered)',
                'action': 'resume',
                'button_text': '▶️ Resume Quiz',
                'button_class': 'btn-warning'
            }
    
    def create_quiz(self, quiz_data: Dict) -> Tuple[bool, str, Optional[Quiz]]:
        """Create a new quiz"""
        if not hasattr(db, 'is_connected') or not db.is_connected():
            return False, "Database not connected", None
        
        try:
            # Create quiz instance
            quiz = Quiz(
                quiz_date=quiz_data['quiz_date'],
                questions=quiz_data['questions']
            )
            
            # Validate quiz
            validation_errors = quiz.validate()
            if validation_errors:
                return False, f"Validation errors: {', '.join(validation_errors)}", None
            
            # Check if quiz already exists for this date
            existing_quiz = db.quizzes_collection.find_one({"quiz_date": quiz.quiz_date})
            if existing_quiz:
                return False, f"Quiz already exists for date {quiz.quiz_date}", None
            
            # Insert quiz
            result = db.quizzes_collection.insert_one(quiz.to_dict())
            quiz.id = str(result.inserted_id)
            
            return True, "Quiz created successfully", quiz
            
        except Exception as e:
            return False, f"Error creating quiz: {str(e)}", None
    
    def get_user_attempt(self, user_id: str, quiz_date: str) -> Optional[QuizAttempt]:
        """Get user's attempt for a specific quiz date"""
        if not hasattr(db, 'is_connected') or not db.is_connected():
            return None
        
        try:
            attempt_doc = db.attempts_collection.find_one({
                "user_id": user_id,
                "quiz_date": quiz_date
            })
            
            if attempt_doc:
                return QuizAttempt.from_dict(attempt_doc)
        except Exception as e:
            print(f"Error getting user attempt: {e}")
        
        return None
    
    def can_user_attempt_quiz(self, user_id: str, quiz_date: str) -> Tuple[bool, str]:
        """Check if user can attempt quiz for a specific date"""
        if not hasattr(db, 'is_connected') or not db.is_connected():
            return False, "Database not connected"
        
        # Check if quiz exists
        quiz = self.get_quiz_by_date(quiz_date)
        if not quiz:
            return False, f"No quiz available for date {quiz_date}"
        
        # Check if user has already attempted this quiz
        existing_attempt = self.get_user_attempt(user_id, quiz_date)
        if existing_attempt and existing_attempt.is_completed:
            return False, "You have already completed this quiz"
        
        return True, "User can attempt quiz"
    
    def start_quiz_attempt(self, user_id: str, quiz_date: str) -> Tuple[bool, str, Optional[QuizAttempt]]:
        """Start a new quiz attempt for user"""
        can_attempt, message = self.can_user_attempt_quiz(user_id, quiz_date)
        if not can_attempt:
            return False, message, None
        
        if not hasattr(db, 'is_connected') or not db.is_connected():
            return False, "Database not connected", None
        
        try:
            # Check if there's an existing incomplete attempt
            existing_attempt = self.get_user_attempt(user_id, quiz_date)
            
            if existing_attempt and not existing_attempt.is_completed:
                # Resume existing attempt
                return True, "Resuming existing attempt", existing_attempt
            
            # Create new attempt
            attempt = QuizAttempt(user_id=user_id, quiz_date=quiz_date)
            
            # Get quiz to set total questions
            quiz = self.get_quiz_by_date(quiz_date)
            if quiz:
                attempt.total_questions = quiz.get_total_questions()
            
            # Insert attempt
            result = db.attempts_collection.insert_one(attempt.to_dict())
            attempt.id = str(result.inserted_id)
            
            return True, "New attempt started", attempt
            
        except Exception as e:
            return False, f"Error starting attempt: {str(e)}", None
    
    def save_answer(self, user_id: str, quiz_date: str, question_index: int, selected_answer: str) -> Tuple[bool, str]:
        """Save user's answer for a question"""
        if not hasattr(db, 'is_connected') or not db.is_connected():
            return False, "Database not connected"
        
        try:
            # Get user's attempt
            attempt = self.get_user_attempt(user_id, quiz_date)
            if not attempt:
                return False, "No active attempt found"
            
            # Do not allow saving after completion
            if attempt.is_completed:
                return False, "Quiz already completed"
            
            # Add/update answer
            attempt.add_answer(question_index, selected_answer)
            
            # Convert attempt.id to ObjectId if it's a string
            from bson import ObjectId
            attempt_id = ObjectId(attempt.id) if isinstance(attempt.id, str) else attempt.id
            
            # Update in database
            result = db.attempts_collection.update_one(
                {"_id": attempt_id},
                {"$set": {
                    "answers": attempt.answers,
                    "auto_saved": True
                }}
            )
            
            if result.matched_count == 0:
                return False, f"No attempt found with id {attempt.id}"
            
            return True, "Answer saved successfully"
            
        except Exception as e:
            return False, f"Error saving answer: {str(e)}"
    
    def submit_quiz(self, user_id: str, quiz_date: str) -> Tuple[bool, str, Optional[Dict]]:
        """Submit completed quiz and calculate score"""
        if not hasattr(db, 'is_connected') or not db.is_connected():
            return False, "Database not connected", None
        
        try:
            # Get user's attempt
            attempt = self.get_user_attempt(user_id, quiz_date)
            if not attempt:
                return False, "No active attempt found", None
            
            if attempt.is_completed:
                return False, "Quiz already completed", None
            
            # Get quiz for correct answers
            quiz = self.get_quiz_by_date(quiz_date)
            if not quiz:
                return False, "Quiz not found", None
            
            # Prepare correct answers dictionary
            correct_answers = {}
            for i, question in enumerate(quiz.questions):
                correct_answers[i] = question['answer']
            
            # Calculate score
            score_result = attempt.calculate_score(correct_answers)
            
            # Mark attempt as completed
            attempt.complete_attempt()
            
            # Convert attempt.id to ObjectId if it's a string
            from bson import ObjectId
            attempt_id = ObjectId(attempt.id) if isinstance(attempt.id, str) else attempt.id
            
            # Update in database
            # Persist a normalized answers array with is_correct flags
            answers_with_flags = attempt.get_answers_summary()
            
            result = db.attempts_collection.update_one(
                {"_id": attempt_id},
                {"$set": {
                    "score": attempt.score,
                    "total_questions": attempt.total_questions,
                    "percentage": attempt.percentage,
                    "is_completed": True,
                    "completed_at": attempt.completed_at,
                    "answers": answers_with_flags
                }}
            )
            
            if result.matched_count == 0:
                return False, f"Failed to update attempt {attempt.id}", None
            
            return True, "Quiz submitted successfully", score_result
            
        except Exception as e:
            return False, f"Error submitting quiz: {str(e)}", None
    
    def get_quiz_statistics(self, quiz_date: str) -> Dict:
        """Get statistics for a specific quiz date"""
        if not hasattr(db, 'is_connected') or not db.is_connected():
            return {"error": "Database not connected"}
        
        try:
            # Get quiz
            quiz = self.get_quiz_by_date(quiz_date)
            if not quiz:
                return {"error": f"No quiz found for date {quiz_date}"}
            
            # Get all attempts for this date
            attempts = list(db.attempts_collection.find({"quiz_date": quiz_date}))
            
            if not attempts:
                return {
                    "quiz_date": quiz_date,
                    "total_questions": quiz.get_total_questions(),
                    "total_attempts": 0,
                    "completed_attempts": 0,
                    "average_score": 0,
                    "average_percentage": 0
                }
            
            # Calculate statistics
            total_attempts = len(attempts)
            completed_attempts = len([a for a in attempts if a.get('is_completed', False)])
            
            completed_scores = [a.get('score', 0) for a in attempts if a.get('is_completed', False)]
            completed_percentages = [a.get('percentage', 0) for a in attempts if a.get('is_completed', False)]
            
            average_score = sum(completed_scores) / len(completed_scores) if completed_scores else 0
            average_percentage = sum(completed_percentages) / len(completed_percentages) if completed_percentages else 0
            
            return {
                "quiz_date": quiz_date,
                "total_questions": quiz.get_total_questions(),
                "total_attempts": total_attempts,
                "completed_attempts": completed_attempts,
                "incomplete_attempts": total_attempts - completed_attempts,
                "average_score": round(average_score, 2),
                "average_percentage": round(average_percentage, 2),
                "completion_rate": round((completed_attempts / total_attempts * 100), 2) if total_attempts > 0 else 0
            }
            
        except Exception as e:
            return {"error": f"Error getting statistics: {str(e)}"}
    
    def get_user_quiz_history(self, user_id: str) -> List[Dict]:
        """Get user's quiz attempt history"""
        if not hasattr(db, 'is_connected') or not db.is_connected():
            return []
        
        try:
            attempts = list(db.attempts_collection.find(
                {"user_id": user_id},
                sort=[("attempted_at", -1)]
            ))
            
            history = []
            for attempt_doc in attempts:
                attempt = QuizAttempt.from_dict(attempt_doc)
                history.append({
                    "quiz_date": attempt.quiz_date,
                    "score": attempt.score,
                    "total_questions": attempt.total_questions,
                    "percentage": attempt.percentage,
                    "is_completed": attempt.is_completed,
                    "attempted_at": attempt.attempted_at,
                    "completed_at": attempt.completed_at
                })
            
            return history
            
        except Exception as e:
            print(f"Error getting user history: {e}")
            return [] 