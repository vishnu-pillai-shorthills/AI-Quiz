"""
Quiz Attempt model to track user quiz attempts and answers
"""
from datetime import datetime
from typing import List, Dict, Optional
from bson import ObjectId

class QuizAttempt:
    """Model representing a user's attempt at a quiz"""
    
    def __init__(self, user_id: str, quiz_date: str, answers: List[Dict] = None):
        self.user_id = user_id
        self.quiz_date = quiz_date
        self.answers = answers or []
        self.score = 0
        self.total_questions = 0
        self.percentage = 0.0
        self.attempted_at = datetime.utcnow()
        self.completed_at = None
        self.is_completed = False
        self.auto_saved = False
    
    def to_dict(self) -> Dict:
        """Convert attempt to dictionary for database storage"""
        return {
            'user_id': self.user_id,
            'quiz_date': self.quiz_date,
            'answers': self.answers,
            'score': self.score,
            'total_questions': self.total_questions,
            'percentage': self.percentage,
            'attempted_at': self.attempted_at,
            'completed_at': self.completed_at,
            'is_completed': self.is_completed,
            'auto_saved': self.auto_saved
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'QuizAttempt':
        """Create attempt instance from dictionary"""
        attempt = cls(
            user_id=data['user_id'],
            quiz_date=data['quiz_date'],
            answers=data.get('answers', [])
        )
        
        if '_id' in data:
            attempt.id = str(data['_id'])
        
        attempt.score = data.get('score', 0)
        attempt.total_questions = data.get('total_questions', 0)
        attempt.percentage = data.get('percentage', 0.0)
        attempt.attempted_at = data.get('attempted_at', datetime.utcnow())
        attempt.completed_at = data.get('completed_at')
        attempt.is_completed = data.get('is_completed', False)
        attempt.auto_saved = data.get('auto_saved', False)
        
        return attempt
    
    def add_answer(self, question_index: int, selected_answer: str, is_correct: bool = None):
        """Add or update an answer for a question"""
        # Find existing answer for this question
        existing_answer = self.get_answer_for_question(question_index)
        
        if existing_answer:
            # Update existing answer
            existing_answer['selected_answer'] = selected_answer
            existing_answer['is_correct'] = is_correct
            existing_answer['answered_at'] = datetime.utcnow()
        else:
            # Add new answer
            answer = {
                'question_index': question_index,
                'selected_answer': selected_answer,
                'is_correct': is_correct,
                'answered_at': datetime.utcnow()
            }
            self.answers.append(answer)
    
    def get_answer_for_question(self, question_index: int) -> Optional[Dict]:
        """Get answer for a specific question"""
        for answer in self.answers:
            if answer['question_index'] == question_index:
                return answer
        return None
    
    def calculate_score(self, correct_answers: Dict[int, str]) -> Dict:
        """Calculate score based on correct answers"""
        self.total_questions = len(correct_answers)
        self.score = 0
        
        for question_index, correct_answer in correct_answers.items():
            user_answer = self.get_answer_for_question(question_index)
            if user_answer and user_answer['selected_answer'] == correct_answer:
                self.score += 1
                user_answer['is_correct'] = True
            elif user_answer:
                user_answer['is_correct'] = False
        
        self.percentage = (self.score / self.total_questions * 100) if self.total_questions > 0 else 0
        
        return {
            'score': self.score,
            'total_questions': self.total_questions,
            'percentage': round(self.percentage, 2)
        }
    
    def complete_attempt(self):
        """Mark attempt as completed"""
        self.is_completed = True
        self.completed_at = datetime.utcnow()
    
    def get_progress(self) -> Dict:
        """Get attempt progress information"""
        answered_questions = len(self.answers)
        return {
            'answered_questions': answered_questions,
            'total_questions': self.total_questions,
            'progress_percentage': (answered_questions / self.total_questions * 100) if self.total_questions > 0 else 0,
            'is_completed': self.is_completed
        }
    
    def get_answers_summary(self) -> List[Dict]:
        """Get summary of all answers"""
        summary = []
        for answer in self.answers:
            summary.append({
                'question_index': answer['question_index'],
                'selected_answer': answer['selected_answer'],
                'is_correct': answer.get('is_correct'),
                'answered_at': answer['answered_at']
            })
        return summary
    
    def validate(self) -> List[str]:
        """Validate attempt data and return list of errors"""
        errors = []
        
        if not self.user_id:
            errors.append("User ID is required")
        
        if not self.quiz_date:
            errors.append("Quiz date is required")
        
        if self.score < 0:
            errors.append("Score cannot be negative")
        
        if self.total_questions < 0:
            errors.append("Total questions cannot be negative")
        
        if self.percentage < 0 or self.percentage > 100:
            errors.append("Percentage must be between 0 and 100")
        
        return errors
    
    def is_valid(self) -> bool:
        """Check if attempt is valid"""
        return len(self.validate()) == 0
    
    def __repr__(self):
        return f"<QuizAttempt {self.user_id} - {self.quiz_date}: {self.score}/{self.total_questions}>" 