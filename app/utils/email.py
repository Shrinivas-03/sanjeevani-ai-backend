from flask_mail import Message
from app import mail
import random
import string

def generate_otp(length=6):
    """Generate a random numeric OTP"""
    return ''.join(random.choices(string.digits, k=length))

def send_otp_email(email, otp, full_name="User"):
    """Send OTP to user's email"""
    try:
        msg = Message(
            subject="Sanjeevani AI - Email Verification OTP",
            recipients=[email]
        )
        
        msg.html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    background-color: #f4f4f4;
                    margin: 0;
                    padding: 0;
                }}
                .container {{
                    max-width: 600px;
                    margin: 50px auto;
                    background-color: #ffffff;
                    padding: 30px;
                    border-radius: 10px;
                    box-shadow: 0 0 10px rgba(0,0,0,0.1);
                }}
                .header {{
                    text-align: center;
                    color: #22c55e;
                    margin-bottom: 30px;
                }}
                .otp-box {{
                    background-color: #f0fdf4;
                    border: 2px solid #22c55e;
                    border-radius: 8px;
                    padding: 20px;
                    text-align: center;
                    margin: 30px 0;
                }}
                .otp-code {{
                    font-size: 32px;
                    font-weight: bold;
                    color: #22c55e;
                    letter-spacing: 8px;
                }}
                .content {{
                    color: #333;
                    line-height: 1.6;
                }}
                .footer {{
                    margin-top: 30px;
                    text-align: center;
                    color: #666;
                    font-size: 12px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🏥 Sanjeevani AI</h1>
                    <h2>Email Verification</h2>
                </div>
                <div class="content">
                    <p>Hello {full_name},</p>
                    <p>Thank you for signing up with Sanjeevani AI! To complete your registration, please use the following One-Time Password (OTP):</p>
                </div>
                <div class="otp-box">
                    <div class="otp-code">{otp}</div>
                </div>
                <div class="content">
                    <p>This OTP is valid for <strong>10 minutes</strong>. Please do not share this code with anyone.</p>
                    <p>If you didn't request this verification, please ignore this email.</p>
                </div>
                <div class="footer">
                    <p>© 2025 Sanjeevani AI. All rights reserved.</p>
                    <p>This is an automated email, please do not reply.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        return False
