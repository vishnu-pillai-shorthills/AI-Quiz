#!/usr/bin/env python3
"""
AI Quiz Analytics Email Report Service - Refresh Token Version (No Browser)
Uses refresh token for automated sending with delegated permissions
Based on the working NiFi email sender approach
"""

import requests
import json
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import io
import base64
import csv
import sys

load_dotenv()

class QuizAnalyticsEmailReporterRefreshToken:
    def __init__(self):
        # Microsoft Graph API configuration using refresh token approach
        self.tenant_id = os.getenv('AZURE_TENANT_ID') or os.getenv('MICROSOFT_TENANT_ID')
        self.client_id = os.getenv('AZURE_CLIENT_ID') or os.getenv('MICROSOFT_CLIENT_ID')
        self.client_secret = os.getenv('AZURE_CLIENT_SECRET') or os.getenv('MICROSOFT_CLIENT_SECRET')
        
        # Refresh token for automated authentication (no browser needed)
        # self.refresh_token = os.getenv('AZURE_REFRESH_TOKEN')
        self.refresh_token = ""

        # self.api_url = "https://aiquiz.shorthills.ai/api/admin/analytics"
        self.api_url = "http://localhost:8002/api/admin/analytics"
        # Graph API endpoints
        self.token_url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token"
        self.send_mail_url = "https://graph.microsoft.com/v1.0/me/sendMail"
        
    def log_message(self, message, level="INFO"):
        """Log message with timestamp"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{timestamp}] {level}: {message}")
        
    def get_access_token(self):
        """Get a fresh access token using the refresh token (no browser needed)"""
        if not all([self.tenant_id, self.client_id, self.client_secret, self.refresh_token]):
            missing = []
            if not self.tenant_id: missing.append('AZURE_TENANT_ID')
            if not self.client_id: missing.append('AZURE_CLIENT_ID') 
            if not self.client_secret: missing.append('AZURE_CLIENT_SECRET')
            if not self.refresh_token: missing.append('AZURE_REFRESH_TOKEN')
            
            self.log_message(f"Missing environment variables: {', '.join(missing)}", "ERROR")
            return None
            
        self.log_message("🔐 Getting fresh access token using refresh token...")
        
        token_data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'grant_type': 'refresh_token',
            'refresh_token': self.refresh_token,
            'scope': 'User.Read Files.Read Files.Read.All Files.ReadWrite Files.ReadWrite.All Mail.Send Mail.ReadWrite offline_access'
        }
        
        try:
            response = requests.post(self.token_url, data=token_data)
            
            if response.status_code == 200:
                token_response = response.json()
                access_token = token_response.get('access_token')
                
                # Update refresh token if a new one is provided
                new_refresh_token = token_response.get('refresh_token')
                if new_refresh_token:
                    self.refresh_token = new_refresh_token
                    self.log_message("🔄 Refresh token updated")
                
                self.log_message("✅ Access token obtained successfully")
                return access_token
            else:
                self.log_message(f"❌ Failed to get access token. Status: {response.status_code}", "ERROR")
                self.log_message(f"Response: {response.text}", "ERROR")
                return None
                
        except Exception as e:
            self.log_message(f"❌ Exception getting access token: {str(e)}", "ERROR")
            return None
    
    def fetch_analytics_data(self):
        """Fetch 7-day analytics data from the API"""
        try:
            self.log_message("📊 Fetching analytics data from API...")
            response = requests.get(self.api_url, timeout=30)
            response.raise_for_status()
            data = response.json()
            self.log_message("✅ Analytics data fetched successfully")
            return data
        except requests.exceptions.RequestException as e:
            self.log_message(f"❌ Error fetching analytics data: {e}", "ERROR")
            return None
    
    def format_analytics_html(self, data):
        """Format analytics data into a beautiful HTML email"""
        if not data or not data.get('success'):
            return "<p>Unable to fetch analytics data.</p>"
        
        overall_stats = data.get('overall_stats', {})
        daily_stats = data.get('daily_stats', [])
        
        # Calculate additional metrics
        total_participants = overall_stats.get('total_participants', 0)  # People who opened
        total_submitted = overall_stats.get('total_submitted', overall_stats.get('total_attempts', 0))  # People who submitted
        total_attempts = overall_stats.get('total_attempts', 0)  # Total completed attempts
        total_quizzes = overall_stats.get('total_quizzes', 0)
        date_range = overall_stats.get('date_range', 'N/A')
        
        # Calculate completion rate as (submitted/opened) * 100
        # total_participants = people who opened quizzes
        # total_submitted = people who submitted quizzes
        completion_percentage = (total_submitted / max(total_participants, 1)) * 100
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 900px;
                    margin: 0 auto;
                    padding: 20px;
                    background-color: #f8fafc;
                }}
                .header {{
                    background-color: #1e293b;
                    color: #ffffff !important;
                    padding: 30px;
                    border-radius: 15px;
                    text-align: center;
                    margin-bottom: 30px;
                    border: 2px solid #334155;
                }}
                .header h1 {{
                    margin: 0 !important;
                    font-size: 28px !important;
                    font-weight: 700 !important;
                    color: #ffffff !important;
                    line-height: 1.2 !important;
                }}
                .header p {{
                    margin: 10px 0 0 0 !important;
                    color: #ffffff !important;
                    font-size: 14px !important;
                    font-weight: 400 !important;
                    line-height: 1.4 !important;
                }}
                .table-container {{
                    background: white;
                    border-radius: 8px;
                    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                    margin-bottom: 30px;
                    overflow: hidden;
                }}
                .table-header {{
                    background: linear-gradient(135deg, #3b82f6, #1d4ed8);
                    color: white;
                    padding: 20px 25px;
                    font-weight: bold;
                    font-size: 16px;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                }}
                th, td {{
                    padding: 15px 20px;
                    text-align: left;
                    border-bottom: 1px solid #e2e8f0;
                }}
                th {{
                    background: #f1f5f9;
                    text-align: center;
                    font-size: 14px;
                    font-weight: 600;
                    color: #475569;
                }}
                tr:hover {{
                    background: #f8fafc;
                }}
                .status-badge {{
                    padding: 4px 8px;
                    border-radius: 4px;
                    font-size: 12px;
                    font-weight: 500;
                }}
                .status-active {{
                    background: #dcfce7;
                    color: #166534;
                }}
                .status-inactive {{
                    background: #fef2f2;
                    color: #991b1b;
                }}
                .footer {{
                    text-align: center;
                    margin-top: 30px;
                    padding: 20px;
                    background: #f8fafc;
                    border-radius: 8px;
                    color: #64748b;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>📊 Weekly Quiz Report</h1>
                <p>Performance Summary ({date_range})</p>
                <p>Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
            </div>
            
            <div class="table-container">
                <div class="table-header">Daily Quiz Performance</div>
                <table>
                    <thead>
                        <tr>
                            <th>Date</th>
                            <th>Quiz Status</th>
                            <th>Opened Quiz</th>
                            <th>Submitted</th>
                            <th>Avg Score</th>
                            <th>Completion Rate</th>
                            <th>Participation Rate</th>
                        </tr>
                    </thead>
                    <tbody>
        """
        
        for day in daily_stats:
            # Skip weekends (Saturday = 5, Sunday = 6)
            date_obj = datetime.strptime(day['date'], '%Y-%m-%d')
            if date_obj.weekday() in [5, 6]:  # Saturday or Sunday
                continue
                
            date = date_obj.strftime('%b %d, %Y')
            day_name = day.get('day_name', 'Unknown')
            
            quiz_status = "No Quiz" if day['quiz_title'] == "No quiz available" else "Active"
            status_class = "status-inactive" if quiz_status == "No Quiz" else "status-active"
            
            participants_opened = day.get('total_opened', day.get('participants_count', 0))  # People who opened the quiz
            participants_submitted = day.get('submitted_count', day.get('participants_count', 0))  # People who submitted
            avg_score = day.get('average_score', 0)
            avg_percentage = day.get('average_percentage', 0)
            
            # Calculate completion rate for this day (submitted/opened)
            day_completion_rate = (participants_submitted / max(participants_opened, 1)) * 100 if participants_opened > 0 else 0
            
            # Calculate participation rate (opened/265)
            participation_rate = (participants_opened / 265) * 100
            
            html_content += f"""
                        <tr>
                            <td><strong>{date}</strong><br><small>{day_name}</small></td>
                            <td><span class="status-badge {status_class}">{quiz_status}</span></td>
                            <td style="text-align: center;">{participants_opened}</td>
                            <td style="text-align: center;">{participants_submitted}</td>
                            <td style="text-align: center;">{avg_score:.1f}/10 ({avg_percentage:.0f}%)</td>
                            <td style="text-align: center;"><strong>{day_completion_rate:.0f}%</strong></td>
                            <td style="text-align: center;"><strong>{participation_rate:.1f}%</strong></td>
                        </tr>
            """
        
        html_content += """
                    </tbody>
                </table>
            </div>
            
            <div class="footer">
                <p>📧 This is an automated report from the AI Quiz Analytics System</p>
                <p>For questions or support, please contact the development team</p>
                <p><strong>AI Quiz Platform</strong> | Shorthills Technologies</p>
            </div>
        </body>
        </html>
        """
        
        return html_content
    
    def create_csv_attachment(self, data):
        """Create CSV attachment with detailed analytics data"""
        if not data or not data.get('success'):
            return None
        
        daily_stats = data.get('daily_stats', [])
        
        # Create CSV in memory
        csv_buffer = io.StringIO()
        writer = csv.writer(csv_buffer)
        
        # Write header
        writer.writerow([
            'Date', 'Day', 'Quiz Title', 'Opened Quiz', 'Submitted Quiz', 'Average Score', 
            'Average Percentage', 'Completion Rate', 'Participation Rate'
        ])
        
        # Write data rows (exclude weekends)
        for day in daily_stats:
            # Skip weekends (Saturday = 5, Sunday = 6)
            date_obj = datetime.strptime(day['date'], '%Y-%m-%d')
            if date_obj.weekday() in [5, 6]:  # Saturday or Sunday
                continue
                
            participants_opened = day.get('total_opened', day.get('participants_count', 0))
            participants_submitted = day.get('submitted_count', day.get('participants_count', 0))
            completion_rate = (participants_submitted / max(participants_opened, 1)) * 100 if participants_opened > 0 else 0
            participation_rate = (participants_opened / 265) * 100
            
            writer.writerow([
                day['date'],
                day.get('day_name', ''),
                day.get('quiz_title', ''),
                participants_opened,
                participants_submitted,
                day.get('average_score', 0),
                day.get('average_percentage', 0),
                f"{completion_rate:.1f}%",
                f"{participation_rate:.1f}%"
            ])
        
        return csv_buffer.getvalue()
    
    def send_email_report(self, recipients, cc_recipients=None, subject=None):
        """Send the analytics report via Microsoft Graph API using refresh token"""
        # Get access token using refresh token
        access_token = self.get_access_token()
        if not access_token:
            return False
        
        # Fetch analytics data
        analytics_data = self.fetch_analytics_data()
        if not analytics_data:
            self.log_message("❌ Failed to fetch analytics data", "ERROR")
            return False
        
        # Prepare email content
        if not subject:
            date_range = analytics_data.get('overall_stats', {}).get('date_range', 'N/A')
            subject = f"AI Quiz Analytics Report - {date_range}"
        
        self.log_message("🎨 Generating HTML report...")
        html_content = self.format_analytics_html(analytics_data)
        
        # Prepare recipients list
        if isinstance(recipients, str):
            recipients = [recipients]
        
        recipient_list = [{"emailAddress": {"address": email}} for email in recipients]
        
        # Prepare CC recipients list
        cc_recipient_list = []
        if cc_recipients:
            if isinstance(cc_recipients, str):
                cc_recipients = [cc_recipients]
            cc_recipient_list = [{"emailAddress": {"address": email}} for email in cc_recipients]
        
        # Create email message in Microsoft Graph format
        email_payload = {
            "message": {
                "subject": subject,
                "body": {
                    "contentType": "HTML",
                    "content": html_content
                },
                "toRecipients": recipient_list
            },
            "saveToSentItems": "true"
        }
        
        # Add CC recipients if provided
        if cc_recipient_list:
            email_payload["message"]["ccRecipients"] = cc_recipient_list
        
        # Add CSV attachment if available
        self.log_message("📎 Creating CSV attachment...")
        csv_content = self.create_csv_attachment(analytics_data)
        if csv_content:
            csv_base64 = base64.b64encode(csv_content.encode()).decode()
            filename = f"quiz_analytics_{datetime.now().strftime('%Y%m%d')}.csv"
            
            email_payload["message"]["attachments"] = [{
                "@odata.type": "#microsoft.graph.fileAttachment",
                "name": filename,
                "contentType": "text/csv",
                "contentBytes": csv_base64
            }]
            self.log_message(f"✅ CSV attachment created: {filename}")
        
        # Send email via Graph API
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        try:
            recipient_emails = [r['emailAddress']['address'] for r in recipient_list]
            cc_emails = [r['emailAddress']['address'] for r in cc_recipient_list] if cc_recipient_list else []
            
            self.log_message(f"📤 Sending email...")
            self.log_message(f"📮 To: {', '.join(recipient_emails)}")
            if cc_emails:
                self.log_message(f"📄 CC: {', '.join(cc_emails)}")
            self.log_message(f"📧 Subject: {subject}")
            
            response = requests.post(self.send_mail_url, headers=headers, json=email_payload)
            
            if response.status_code == 202:  # Accepted
                self.log_message("✅ Email sent successfully!")
                self.log_message("🎉 Analytics report delivered!")
                return True
            else:
                self.log_message(f"❌ Failed to send email. Status: {response.status_code}", "ERROR")
                self.log_message(f"Response: {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log_message(f"❌ Exception sending email: {str(e)}", "ERROR")
            return False

def main():
    """Main function - fully automated email sending using refresh token"""
    print("🚀 AI Quiz Analytics Email Reporter (Refresh Token Version)")
    print("=" * 60)
    print("📧 No browser required - uses refresh token for automation!")
    print()
    
    reporter = QuizAnalyticsEmailReporterRefreshToken()
    
    # Configure recipients
    recipients = [
        "vishnu@shorthills.ai",
        "aftab.ansari@shorthills.ai"
        # Add more TO recipients as needed
    ]
    
    # Configure CC recipients
    cc_recipients = [
        # "satyam.anand@shorthills.ai"
        # "sourjyendra.krishna@shorthills.ai"
        # Add CC recipients as needed
    ]
    
    print(f"🎯 To: {', '.join(recipients)}")
    if cc_recipients:
        print(f"📄 CC: {', '.join(cc_recipients)}")
    print()
    
    # Send report (fully automated)
    success = reporter.send_email_report(recipients, cc_recipients)
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 SUCCESS: Analytics report sent automatically!")
        print("📬 Check recipient inboxes for the report")
    else:
        print("💥 FAILED: Could not send analytics report")
        print("📋 Add AZURE_REFRESH_TOKEN to your .env file")

if __name__ == "__main__":
    main() 