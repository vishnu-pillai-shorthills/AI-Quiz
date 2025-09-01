"""
Quiz data model
"""
from datetime import datetime
from typing import List, Dict, Optional
from bson import ObjectId

class Quiz:
    """Quiz model representing a daily quiz"""
    
    def __init__(self, quiz_date: str, questions: List[Dict], total_questions: int = None):
        self.quiz_date = quiz_date
        self.questions = questions
        self.total_questions = total_questions or len(questions)
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def to_dict(self) -> Dict:
        """Convert quiz to dictionary for database storage"""
        return {
            'quiz_date': self.quiz_date,
            'questions': self.questions,
            'total_questions': self.total_questions,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Quiz':
        """Create quiz instance from dictionary"""
        quiz = cls(
            quiz_date=data['quiz_date'],
            questions=data['questions'],
            total_questions=data.get('total_questions')
        )
        
        if '_id' in data:
            quiz.id = str(data['_id'])
        
        if 'created_at' in data:
            quiz.created_at = data['created_at']
        
        if 'updated_at' in data:
            quiz.updated_at = data['updated_at']
        
        return quiz
    
    def validate(self) -> List[str]:
        """Validate quiz data and return list of errors"""
        errors = []
        
        if not self.quiz_date:
            errors.append("Quiz date is required")
        
        if not self.questions:
            errors.append("Questions are required")
        
        if self.total_questions <= 0:
            errors.append("Total questions must be greater than 0")
        
        # Validate each question
        for i, question in enumerate(self.questions):
            question_errors = self._validate_question(question, i)
            errors.extend(question_errors)
        
        return errors
    
    def _validate_question(self, question: Dict, index: int) -> List[str]:
        """Validate individual question"""
        errors = []
        
        if 'question' not in question:
            errors.append(f"Question {index + 1}: Missing question text")
        
        if 'options' not in question:
            errors.append(f"Question {index + 1}: Missing options")
        elif not isinstance(question['options'], dict):
            errors.append(f"Question {index + 1}: Options must be a dictionary")
        
        if 'answer' not in question:
            errors.append(f"Question {index + 1}: Missing correct answer")
        
        # Validate options format
        if 'options' in question and isinstance(question['options'], dict):
            if len(question['options']) < 2:
                errors.append(f"Question {index + 1}: Must have at least 2 options")
            
            # Check if answer exists in options
            if 'answer' in question and question['answer'] not in question['options']:
                errors.append(f"Question {index + 1}: Answer must be one of the options")
        
        return errors
    
    def get_question_by_index(self, index: int) -> Optional[Dict]:
        """Get question by index (0-based)"""
        if 0 <= index < len(self.questions):
            return self.questions[index]
        return None
    
    def get_total_questions(self) -> int:
        """Get total number of questions"""
        return len(self.questions)
    
    def is_valid(self) -> bool:
        """Check if quiz is valid"""
        return len(self.validate()) == 0
    
    def __repr__(self):
        return f"<Quiz {self.quiz_date}: {self.total_questions} questions>" 