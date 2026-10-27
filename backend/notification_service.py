import os
from twilio.rest import Client
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NotificationService:
    def __init__(self):
        """Initialize notification service with API credentials"""
        self.twilio_client = None
        self.sendgrid_client = None
        self.notification_enabled = os.getenv('NOTIFICATION_ENABLED', 'true').lower() == 'true'
        self.high_confidence_threshold = float(os.getenv('HIGH_CONFIDENCE_THRESHOLD', '0.9'))
        
        # Initialize Twilio
        twilio_sid = os.getenv('TWILIO_ACCOUNT_SID')
        twilio_token = os.getenv('TWILIO_AUTH_TOKEN')
        if twilio_sid and twilio_token:
            try:
                self.twilio_client = Client(twilio_sid, twilio_token)
                logger.info("Twilio client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Twilio client: {e}")
        
        # Initialize SendGrid
        sendgrid_key = os.getenv('SENDGRID_API_KEY')
        if sendgrid_key:
            try:
                self.sendgrid_client = SendGridAPIClient(api_key=sendgrid_key)
                logger.info("SendGrid client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize SendGrid client: {e}")
    
    def send_email_notification(self, to_email, to_name, missing_person_name, 
                               found_person_data, similarity_score, match_id):
        """
        Send email notification for high-confidence match
        
        Args:
            to_email (str): Recipient email address
            to_name (str): Recipient name
            missing_person_name (str): Name of missing person
            found_person_data (dict): Data about found person
            similarity_score (float): Match confidence score
            match_id (str): Match ID for reference
        """
        if not self.sendgrid_client or not self.notification_enabled:
            logger.warning("SendGrid not configured or notifications disabled")
            return False
        
        try:
            from_email = os.getenv('FROM_EMAIL', 'noreply@missingpersonfinder.com')
            from_name = os.getenv('FROM_NAME', 'AI Missing Person Finder')
            
            # Create email content
            subject = f"High-Confidence Match Found for {missing_person_name}"
            
            html_content = self._create_email_html(
                to_name, missing_person_name, found_person_data, 
                similarity_score, match_id
            )
            
            text_content = self._create_email_text(
                to_name, missing_person_name, found_person_data, 
                similarity_score, match_id
            )
            
            # Create mail object
            message = Mail(
                from_email=(from_email, from_name),
                to_emails=to_email,
                subject=subject,
                html_content=html_content,
                plain_text_content=text_content
            )
            
            # Send email
            response = self.sendgrid_client.send(message)
            
            if response.status_code in [200, 201, 202]:
                logger.info(f"Email notification sent successfully to {to_email}")
                return True
            else:
                logger.error(f"Failed to send email: {response.status_code} - {response.body}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending email notification: {e}")
            return False
    
    def send_sms_notification(self, to_phone, missing_person_name, similarity_score, match_id):
        """
        Send SMS notification for high-confidence match
        
        Args:
            to_phone (str): Recipient phone number
            missing_person_name (str): Name of missing person
            similarity_score (float): Match confidence score
            match_id (str): Match ID for reference
        """
        if not self.twilio_client or not self.notification_enabled:
            logger.warning("Twilio not configured or notifications disabled")
            return False
        
        try:
            twilio_phone = os.getenv('TWILIO_PHONE_NUMBER')
            if not twilio_phone:
                logger.error("Twilio phone number not configured")
                return False
            
            # Create SMS message
            message_body = (
                f"🚨 HIGH-CONFIDENCE MATCH FOUND!\n\n"
                f"Missing Person: {missing_person_name}\n"
                f"Confidence: {similarity_score:.1%}\n"
                f"Match ID: {match_id}\n\n"
                f"Please check the AI Missing Person Finder dashboard for details."
            )
            
            # Send SMS
            message = self.twilio_client.messages.create(
                body=message_body,
                from_=twilio_phone,
                to=to_phone
            )
            
            logger.info(f"SMS notification sent successfully to {to_phone}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending SMS notification: {e}")
            return False
    
    def _create_email_html(self, to_name, missing_person_name, found_person_data, 
                          similarity_score, match_id):
        """Create HTML content for email notification"""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }}
                .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 8px 8px; }}
                .alert {{ background: #d4edda; border: 1px solid #c3e6cb; color: #155724; padding: 15px; border-radius: 5px; margin: 20px 0; }}
                .match-details {{ background: white; padding: 20px; border-radius: 5px; margin: 20px 0; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                .confidence {{ font-size: 24px; font-weight: bold; color: #28a745; }}
                .footer {{ text-align: center; margin-top: 30px; color: #666; font-size: 14px; }}
                .button {{ display: inline-block; background: #007bff; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; margin: 10px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔍 AI Missing Person Finder</h1>
                    <h2>High-Confidence Match Found!</h2>
                </div>
                
                <div class="content">
                    <p>Dear {to_name},</p>
                    
                    <div class="alert">
                        <strong>🎉 Great News!</strong> We have found a potential match for {missing_person_name} 
                        with a confidence score of <span class="confidence">{similarity_score:.1%}</span>
                    </div>
                    
                    <div class="match-details">
                        <h3>Match Details:</h3>
                        <ul>
                            <li><strong>Missing Person:</strong> {missing_person_name}</li>
                            <li><strong>Confidence Score:</strong> {similarity_score:.1%}</li>
                            <li><strong>Match ID:</strong> {match_id}</li>
                            <li><strong>Found Location:</strong> {found_person_data.get('address', 'Location not specified')}</li>
                            <li><strong>Date Found:</strong> {found_person_data.get('created_at', 'Unknown')}</li>
                        </ul>
                    </div>
                    
                    <p>This is an automated notification from our AI facial recognition system. 
                    Please verify this match through our official channels.</p>
                    
                    <div style="text-align: center;">
                        <a href="#" class="button">View Match Details</a>
                    </div>
                    
                    <div class="footer">
                        <p>This is an automated message from AI Missing Person Finder.<br>
                        If you believe this is an error, please contact our support team.</p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
    
    def _create_email_text(self, to_name, missing_person_name, found_person_data, 
                          similarity_score, match_id):
        """Create plain text content for email notification"""
        return f"""
        HIGH-CONFIDENCE MATCH FOUND!

        Dear {to_name},

        Great News! We have found a potential match for {missing_person_name} 
        with a confidence score of {similarity_score:.1%}.

        Match Details:
        - Missing Person: {missing_person_name}
        - Confidence Score: {similarity_score:.1%}
        - Match ID: {match_id}
        - Found Location: {found_person_data.get('address', 'Location not specified')}
        - Date Found: {found_person_data.get('created_at', 'Unknown')}

        This is an automated notification from our AI facial recognition system. 
        Please verify this match through our official channels.

        ---
        This is an automated message from AI Missing Person Finder.
        If you believe this is an error, please contact our support team.
        """
    
    def should_send_notification(self, similarity_score):
        """Check if notification should be sent based on confidence threshold"""
        return (self.notification_enabled and 
                similarity_score >= self.high_confidence_threshold)
    
    def log_notification(self, match_id, notification_type, recipient, success, error_message=None):
        """Log notification attempt to database"""
        try:
            # This would typically log to a notifications collection
            log_entry = {
                'match_id': match_id,
                'notification_type': notification_type,  # 'email' or 'sms'
                'recipient': recipient,
                'success': success,
                'error_message': error_message,
                'timestamp': datetime.now()
            }
            
            # For now, just log to console
            logger.info(f"Notification log: {log_entry}")
            
        except Exception as e:
            logger.error(f"Error logging notification: {e}")

# Global instance
notification_service = NotificationService()
