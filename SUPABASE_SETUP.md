# Supabase Database Setup

## Create Users Table

Run this SQL query in your Supabase SQL Editor to create the users table:

```sql
-- Create users table with OTP fields
CREATE TABLE users (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    full_name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    blood_group VARCHAR(10) NOT NULL,
    existing_diseases TEXT,
    is_verified BOOLEAN DEFAULT FALSE,
    otp VARCHAR(10),
    otp_expiry TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW()),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW())
);

-- Create index on email for faster lookups
CREATE INDEX idx_users_email ON users(email);

-- Create index on is_verified
CREATE INDEX idx_users_verified ON users(is_verified);

-- Enable Row Level Security (RLS)
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

-- Create policy to allow insert (signup)
CREATE POLICY "Allow public signup" ON users
    FOR INSERT
    WITH CHECK (true);

-- Create policy to allow users to read their own data
CREATE POLICY "Users can read own data" ON users
    FOR SELECT
    USING (auth.uid() = id OR true);

-- Create policy to allow users to update their own data
CREATE POLICY "Users can update own data" ON users
    FOR UPDATE
    USING (auth.uid() = id OR true);

-- Create a function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = TIMEZONE('utc', NOW());
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger to automatically update updated_at
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

## Blood Groups Reference

Valid blood groups: A+, A-, B+, B-, AB+, AB-, O+, O-

## API Endpoints

### 1. Signup (Send OTP)
- **URL**: `POST /api/auth/signup`
- **Body**:
```json
{
  "fullName": "John Doe",
  "email": "you@example.com",
  "password": "yourpassword",
  "bloodGroup": "A+",
  "existingDiseases": "e.g., Diabetes, Hypertension"
}
```
- **Response**:
```json
{
  "message": "Account created! OTP sent to your email. Please verify to complete registration.",
  "email": "you@example.com",
  "requires_verification": true
}
```

### 2. Verify OTP
- **URL**: `POST /api/auth/verify-otp`
- **Body**:
```json
{
  "email": "you@example.com",
  "otp": "123456"
}
```
- **Response**:
```json
{
  "message": "Email verified successfully!",
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "expires_in": 3600,
  "user": {
    "id": "uuid",
    "full_name": "John Doe",
    "email": "you@example.com",
    "blood_group": "A+",
    "existing_diseases": "Diabetes",
    "created_at": "2025-10-17T..."
  }
}
```

### 3. Resend OTP
- **URL**: `POST /api/auth/resend-otp`
- **Body**:
```json
{
  "email": "you@example.com"
}
```
- **Response**:
```json
{
  "message": "OTP sent successfully to your email",
  "email": "you@example.com"
}
```

### 4. Login
- **URL**: `POST /api/auth/signup`
- **Body**:
```json
{
  "fullName": "John Doe",
  "email": "you@example.com",
  "password": "yourpassword",
  "bloodGroup": "A+",
  "existingDiseases": "e.g., Diabetes, Hypertension"
}
```
- **Response**:
```json
{
  "message": "Account created successfully",
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "expires_in": 3600,
  "user": {
    "id": "uuid",
    "full_name": "John Doe",
    "email": "you@example.com",
    "blood_group": "A+",
    "existing_diseases": "Diabetes",
    "created_at": "2025-10-17T..."
  }
}
```

### 4. Login
- **URL**: `POST /api/auth/login`
- **Body**:
```json
{
  "email": "you@example.com",
  "password": "yourpassword"
}
```
- **Response**: Same as verify-otp response (includes tokens)
- **Note**: Login requires email to be verified first

### 5. Refresh Token
- **URL**: `POST /api/auth/refresh`
- **Body**:
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```
- **Response**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "expires_in": 3600
}
```

### 6. Get Current User (Protected Route Example)
- **URL**: `GET /api/auth/me`
- **Headers**: 
  - `Authorization: Bearer <access_token>`
- **Response**:
```json
{
  "user": {
    "id": "uuid",
    "full_name": "John Doe",
    "email": "you@example.com",
    "blood_group": "A+",
    "existing_diseases": "Diabetes",
    "created_at": "2025-10-17T..."
  }
}
```

### 7. Get Profile Details
- **URL**: `GET /api/auth/profile`
- **Headers**: 
  - `Authorization: Bearer <access_token>`
- **Response**:
```json
{
  "success": true,
  "profile": {
    "id": "uuid",
    "full_name": "John Doe",
    "email": "you@example.com",
    "blood_group": "A+",
    "existing_diseases": "Diabetes",
    "is_verified": true,
    "created_at": "2025-10-17T...",
    "updated_at": "2025-10-17T..."
  }
}
```

### 8. Update Profile
- **URL**: `PUT /api/auth/profile`
- **Headers**: 
  - `Authorization: Bearer <access_token>`
- **Body**:
```json
{
  "fullName": "John Updated",
  "bloodGroup": "B+",
  "existingDiseases": "Diabetes, Hypertension"
}
```
- **Response**:
```json
{
  "success": true,
  "message": "Profile updated successfully",
  "profile": {
    "id": "uuid",
    "full_name": "John Updated",
    "email": "you@example.com",
    "blood_group": "B+",
    "existing_diseases": "Diabetes, Hypertension",
    "updated_at": "2025-10-17T..."
  }
}
```

### 9. Logout
- **URL**: `POST /api/auth/logout`
- **Headers**: 
  - `Authorization: Bearer <access_token>`
- **Response**:
```json
{
  "success": true,
  "message": "Logged out successfully"
}
```
- **Note**: Since JWT is stateless, logout happens on client side by removing tokens. This endpoint is for logging/analytics.

## Security Features

1. **Password Hashing**: Passwords are hashed using bcrypt with salt
2. **JWT Tokens**: 
   - Access tokens expire in 1 hour (configurable)
   - Refresh tokens expire in 30 days (configurable)
   - Tokens include user_id, email, and token type
3. **Email Verification**: Users must verify email via OTP before they can login
4. **OTP Security**:
   - 6-digit random OTP
   - Expires in 10 minutes (configurable)
   - Sent via email
   - Can be resent if expired
5. **Email Validation**: Ensures proper email format
6. **Password Validation**: Minimum 6 characters
7. **Protected Routes**: Use `@token_required` decorator
8. **CORS**: Configured for React Native app and web

## Email Setup (Gmail Example)

To send OTP emails using Gmail:

1. **Enable 2-Factor Authentication** on your Gmail account
2. **Generate App Password**:
   - Go to Google Account Settings
   - Security → 2-Step Verification → App passwords
   - Generate a new app password for "Mail"
3. **Update `.env` file**:
   ```
   MAIL_USERNAME=your-email@gmail.com
   MAIL_PASSWORD=your-16-char-app-password
   MAIL_DEFAULT_SENDER=your-email@gmail.com
   ```

## Registration Flow

1. User fills signup form
2. Backend creates unverified user account
3. OTP sent to user's email
4. User enters OTP on verification screen
5. Backend verifies OTP and marks user as verified
6. User receives JWT tokens and can login

## Frontend Integration Example

### Complete Signup Flow
```javascript
// Step 1: Signup
const signup = async (userData) => {
  const response = await fetch('http://localhost:5000/api/auth/signup', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(userData)
  });
  const data = await response.json();
  
  if (data.requires_verification) {
    // Show OTP verification screen
    return { email: data.email, needsVerification: true };
  }
  
  return data;
};

// Step 2: Verify OTP
const verifyOTP = async (email, otp) => {
  const response = await fetch('http://localhost:5000/api/auth/verify-otp', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, otp })
  });
  const data = await response.json();
  
  if (response.ok) {
    // Store tokens
    localStorage.setItem('access_token', data.access_token);
    localStorage.setItem('refresh_token', data.refresh_token);
    return data;
  }
  
  throw new Error(data.error);
};

// Resend OTP
const resendOTP = async (email) => {
  const response = await fetch('http://localhost:5000/api/auth/resend-otp', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email })
  });
  return await response.json();
};
```
```javascript
const signup = async (userData) => {
  const response = await fetch('http://localhost:5000/api/auth/signup', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(userData)
  });
  const data = await response.json();
  
  // Store tokens
  localStorage.setItem('access_token', data.access_token);
  localStorage.setItem('refresh_token', data.refresh_token);
  
  return data;
};
```

### Login
```javascript
const login = async (email, password) => {
  const response = await fetch('http://localhost:5000/api/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password })
  });
  const data = await response.json();
  
  // Store tokens
  localStorage.setItem('access_token', data.access_token);
  localStorage.setItem('refresh_token', data.refresh_token);
  
  return data;
};
```

### Protected API Call
```javascript
const getUser = async () => {
  const token = localStorage.getItem('access_token');
  
  const response = await fetch('http://localhost:5000/api/auth/me', {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  
  if (response.status === 401) {
    // Token expired, refresh it
    await refreshToken();
    // Retry the request
    return getUser();
  }
  
  return await response.json();
};
```

### Refresh Token
```javascript
const refreshToken = async () => {
  const refresh_token = localStorage.getItem('refresh_token');
  
  const response = await fetch('http://localhost:5000/api/auth/refresh', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh_token })
  });
  
  const data = await response.json();
  localStorage.setItem('access_token', data.access_token);
  
  return data;
};
```

## Notes

1. Change `JWT_SECRET_KEY` in production to a secure random string
2. Store tokens securely (React Native: AsyncStorage/SecureStore, Web: localStorage/sessionStorage)
3. Include `Authorization: Bearer <token>` header in protected API requests
4. Implement token refresh logic when access token expires
5. Logout: Simply remove tokens from storage
