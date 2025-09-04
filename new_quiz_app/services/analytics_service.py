"""
Analytics service for quiz performance and participation statistics
"""
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional, Tuple
from config.database import db
from models.quiz_attempt import QuizAttempt
from models.user import User
from bson import ObjectId


class AnalyticsService:
    """Service for analyzing quiz performance and participation"""
    
    def __init__(self):
        pass
    
    def get_last_7_days_stats(self) -> Dict:
        """Get comprehensive statistics for the last 7 days of quizzes"""
        if not db.is_connected():
            return {"error": "Database not connected"}
        
        try:
            # Calculate date range (last 7 days including today)
            today = date.today()
            start_date = today - timedelta(days=6)  # 7 days including today
            
            # Generate list of dates
            date_list = []
            for i in range(7):
                check_date = start_date + timedelta(days=i)
                date_list.append(check_date.strftime('%Y-%m-%d'))
            
            # Get quizzes for these dates
            quizzes = list(db.quizzes_collection.find({
                "quiz_date": {"$in": date_list}
            }).sort("quiz_date", 1))
            
            # Get all attempts for these dates (both completed and incomplete)
            all_attempts = list(db.attempts_collection.find({
                "quiz_date": {"$in": date_list}
            }))
            
            # Get only completed attempts for scoring calculations
            attempts = [a for a in all_attempts if a.get('is_completed', False)]
            
            # Get user information for all participants
            user_ids = list(set([attempt['user_id'] for attempt in attempts]))
            users = list(db.users_collection.find({
                "user_id": {"$in": user_ids}
            }))
            user_lookup = {user['user_id']: user for user in users}
            
            # Process statistics for each day
            daily_stats = []
            overall_stats = {
                "total_participants": len(user_ids),
                "total_attempts": len(attempts),
                "total_quizzes": len(quizzes),
                "date_range": f"{start_date.strftime('%Y-%m-%d')} to {today.strftime('%Y-%m-%d')}"
            }
            
            for quiz_date in date_list:
                quiz_info = next((q for q in quizzes if q['quiz_date'] == quiz_date), None)
                day_attempts = [a for a in attempts if a['quiz_date'] == quiz_date]
                day_all_attempts = [a for a in all_attempts if a['quiz_date'] == quiz_date]
                
                # Get day name
                try:
                    from datetime import datetime
                    date_obj = datetime.strptime(quiz_date, '%Y-%m-%d')
                    day_name = date_obj.strftime('%A')
                except:
                    day_name = 'Unknown'
                
                # Calculate completion rate
                completion_rate = round((len(day_attempts) / len(day_all_attempts) * 100), 2) if day_all_attempts else 0
                
                if quiz_info and day_attempts:
                    # Calculate statistics for this day
                    scores = [attempt['score'] for attempt in day_attempts]
                    percentages = [attempt['percentage'] for attempt in day_attempts]
                    
                    # Get top 3 performers
                    top_performers = sorted(day_attempts, key=lambda x: x['percentage'], reverse=True)[:3]
                    top_3 = []
                    for performer in top_performers:
                        user_info = user_lookup.get(performer['user_id'], {})
                        top_3.append({
                            "name": user_info.get('name', 'Unknown User'),
                            "email": user_info.get('email', 'Unknown'),
                            "score": performer['score'],
                            "total_questions": performer['total_questions'],
                            "percentage": performer['percentage']
                        })
                    
                    day_stat = {
                        "date": quiz_date,
                        "day_name": day_name,
                        "quiz_title": f"Quiz for {quiz_date}",
                        "total_questions": quiz_info.get('total_questions', 0),
                        "participants_count": len(day_attempts),
                        "average_score": round(sum(scores) / len(scores), 2) if scores else 0,
                        "average_percentage": round(sum(percentages) / len(percentages), 2) if percentages else 0,
                        "highest_score": max(scores) if scores else 0,
                        "lowest_score": min(scores) if scores else 0,
                        "top_3_performers": top_3,
                        "completion_rate": completion_rate
                    }
                    
                elif quiz_info:
                    # Quiz exists but no attempts
                    day_stat = {
                        "date": quiz_date,
                        "day_name": day_name,
                        "quiz_title": f"Quiz for {quiz_date}",
                        "total_questions": quiz_info.get('total_questions', 0),
                        "participants_count": 0,
                        "average_score": 0,
                        "average_percentage": 0,
                        "highest_score": 0,
                        "lowest_score": 0,
                        "top_3_performers": [],
                        "completion_rate": completion_rate
                    }
                else:
                    # No quiz for this date
                    day_stat = {
                        "date": quiz_date,
                        "day_name": day_name,
                        "quiz_title": f"No quiz available",
                        "total_questions": 0,
                        "participants_count": 0,
                        "average_score": 0,
                        "average_percentage": 0,
                        "highest_score": 0,
                        "lowest_score": 0,
                        "top_3_performers": [],
                        "completion_rate": completion_rate
                    }
                
                daily_stats.append(day_stat)
            
            return {
                "success": True,
                "overall_stats": overall_stats,
                "daily_stats": daily_stats,
                "date_range": date_list
            }
            
        except Exception as e:
            print(f"Error getting analytics: {e}")
            return {"error": f"Error calculating statistics: {str(e)}"}
    
    def get_quiz_analytics(self, quiz_date: str) -> Dict:
        """Get detailed analytics for a specific quiz date"""
        if not db.is_connected():
            return {"error": "Database not connected"}
        
        try:
            # Get quiz info
            quiz = db.quizzes_collection.find_one({"quiz_date": quiz_date})
            if not quiz:
                return {"error": f"No quiz found for {quiz_date}"}
            
            # Get all attempts for this quiz
            attempts = list(db.attempts_collection.find({
                "quiz_date": quiz_date,
                "is_completed": True
            }))
            
            if not attempts:
                return {
                    "quiz_date": quiz_date,
                    "total_questions": quiz.get('total_questions', 0),
                    "participants_count": 0,
                    "message": "No completed attempts found"
                }
            
            # Get user information
            user_ids = [attempt['user_id'] for attempt in attempts]
            users = list(db.users_collection.find({
                "user_id": {"$in": user_ids}
            }))
            user_lookup = {user['user_id']: user for user in users}
            
            # Calculate detailed statistics
            scores = [attempt['score'] for attempt in attempts]
            percentages = [attempt['percentage'] for attempt in attempts]
            
            # Score distribution
            score_ranges = {
                "90-100%": len([p for p in percentages if p >= 90]),
                "80-89%": len([p for p in percentages if 80 <= p < 90]),
                "70-79%": len([p for p in percentages if 70 <= p < 80]),
                "60-69%": len([p for p in percentages if 60 <= p < 70]),
                "Below 60%": len([p for p in percentages if p < 60])
            }
            
            # All participants with details
            all_participants = []
            for attempt in sorted(attempts, key=lambda x: x['percentage'], reverse=True):
                user_info = user_lookup.get(attempt['user_id'], {})
                all_participants.append({
                    "rank": len(all_participants) + 1,
                    "name": user_info.get('name', 'Unknown User'),
                    "email": user_info.get('email', 'Unknown'),
                    "score": attempt['score'],
                    "total_questions": attempt['total_questions'],
                    "percentage": attempt['percentage'],
                    "completed_at": attempt.get('completed_at', 'Unknown')
                })
            
            return {
                "success": True,
                "quiz_date": quiz_date,
                "total_questions": quiz.get('total_questions', 0),
                "participants_count": len(attempts),
                "average_score": round(sum(scores) / len(scores), 2),
                "average_percentage": round(sum(percentages) / len(percentages), 2),
                "highest_score": max(scores),
                "lowest_score": min(scores),
                "score_distribution": score_ranges,
                "all_participants": all_participants
            }
            
        except Exception as e:
            print(f"Error getting quiz analytics: {e}")
            return {"error": f"Error calculating quiz statistics: {str(e)}"}
    
    def get_user_performance(self, user_id: str, days: int = 30) -> Dict:
        """Get performance analytics for a specific user"""
        if not db.is_connected():
            return {"error": "Database not connected"}
        
        try:
            # Calculate date range
            today = date.today()
            start_date = today - timedelta(days=days-1)
            date_list = []
            for i in range(days):
                check_date = start_date + timedelta(days=i)
                date_list.append(check_date.strftime('%Y-%m-%d'))
            
            # Get user info
            user = db.users_collection.find_one({"user_id": user_id})
            if not user:
                return {"error": "User not found"}
            
            # Get user's attempts
            attempts = list(db.attempts_collection.find({
                "user_id": user_id,
                "quiz_date": {"$in": date_list},
                "is_completed": True
            }).sort("quiz_date", 1))
            
            if not attempts:
                return {
                    "user_name": user.get('name', 'Unknown'),
                    "user_email": user.get('email', 'Unknown'),
                    "attempts_count": 0,
                    "message": "No completed attempts found"
                }
            
            # Calculate performance metrics
            scores = [attempt['score'] for attempt in attempts]
            percentages = [attempt['percentage'] for attempt in attempts]
            
            performance_data = {
                "user_name": user.get('name', 'Unknown'),
                "user_email": user.get('email', 'Unknown'),
                "attempts_count": len(attempts),
                "average_score": round(sum(scores) / len(scores), 2),
                "average_percentage": round(sum(percentages) / len(percentages), 2),
                "best_score": max(scores),
                "worst_score": min(scores),
                "best_percentage": max(percentages),
                "worst_percentage": min(percentages),
                "improvement_trend": percentages[-1] - percentages[0] if len(percentages) > 1 else 0,
                "attempts_by_date": [
                    {
                        "date": attempt['quiz_date'],
                        "score": attempt['score'],
                        "percentage": attempt['percentage'],
                        "total_questions": attempt['total_questions']
                    }
                    for attempt in attempts
                ]
            }
            
            return {"success": True, **performance_data}
            
        except Exception as e:
            print(f"Error getting user performance: {e}")
            return {"error": f"Error calculating user performance: {str(e)}"} 