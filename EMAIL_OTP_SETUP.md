# Email OTP Verification Setup Guide

## Prerequisites

1. **Gmail Account** (or any SMTP email service)
2. **App Password** (for Gmail with 2FA enabled)

## Setup Steps

### 1. Configure Gmail for Sending Emails

#### For Gmail:
1. Enable 2-Factor Authentication on your Google Account
2. Go to: https://myaccount.google.com/security
3. Navigate to: Security → 2-Step Verification → App passwords
4. Select "Mail" and generate a 16-character app password
5. Copy this password (you'll need it for `.env`)

### 2. Update Environment Variables

Create a `.env` file in the root directory and add:

```env
# Email Configuration
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USE_SSL=False
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-16-char-app-password
MAIL_DEFAULT_SENDER=your-email@gmail.com

# OTP Settings
OTP_EXPIRY_MINUTES=10
```

### 3. Update Supabase Table

Run the updated SQL from `SUPABASE_SETUP.md` to add OTP fields to users table:
- `is_verified` (BOOLEAN)
- `otp` (VARCHAR)
- `otp_expiry` (TIMESTAMP)

### 4. Install Dependencies

```powershell
pip install -r requirements.txt
```

## OTP Flow

1. **Signup** → Creates unverified user, generates OTP, sends email
2. **User receives email** → 6-digit OTP valid for 10 minutes
3. **Verify OTP** → User enters OTP, gets verified, receives JWT tokens
4. **Resend OTP** → If expired, user can request new OTP
5. **Login** → Only verified users can login

## Testing

### 1. Test Signup
```bash
curl -X POST http://localhost:5000/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "fullName": "John Doe",
    "email": "test@example.com",
    "password": "password123",
    "bloodGroup": "A+",
    "existingDiseases": "None"
  }'
```

### 2. Check Email for OTP

### 3. Verify OTP
```bash
curl -X POST http://localhost:5000/api/auth/verify-otp \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "otp": "123456"
  }'
```

## Troubleshooting

### Email not sending:
- Check MAIL_USERNAME and MAIL_PASSWORD in `.env`
- Verify 2FA is enabled on Gmail
- Ensure app password is correct (not regular password)
- Check spam/junk folder

### OTP expired:
- Use `/api/auth/resend-otp` endpoint
- Check OTP_EXPIRY_MINUTES setting

### User already exists:
- If user exists but unverified, signup will resend OTP
- If user exists and verified, returns error

## Email Template

The OTP email includes:
- Professional Sanjeevani AI branding
- Clear OTP display (6-digit code)
- Expiry information (10 minutes)
- Security warning (don't share OTP)

## Security Notes

1. OTP is stored temporarily in database
2. OTP is cleared after successful verification
3. OTP expires after configured minutes
4. Failed OTP attempts are logged
5. Email must be verified before login
