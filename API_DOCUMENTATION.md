# API Documentation - Sanjeevani AI Backend

Base URL: `http://localhost:5000`

---

## 🔐 Authentication Endpoints

### 1. Test API
**GET** `/api/auth/test`

No authentication required.

**Response:**
```json
{
  "message": "API is working!",
  "timestamp": "2025-10-17T..."
}
```

---

### 2. Signup (Create Account & Send OTP)
**POST** `/api/auth/signup`

**Request Body:**
```json
{
  "fullName": "John Doe",
  "email": "john@example.com",
  "password": "password123",
  "bloodGroup": "A+",
  "existingDiseases": "Diabetes"
}
```

**Response (201):**
```json
{
  "message": "Account created! OTP sent to your email. Please verify to complete registration.",
  "email": "john@example.com",
  "requires_verification": true
}
```

---

### 3. Verify OTP
**POST** `/api/auth/verify-otp`

**Request Body:**
```json
{
  "email": "john@example.com",
  "otp": "123456"
}
```

**Response (200):**
```json
{
  "message": "Email verified successfully!",
  "access_token": "eyJhbGci...",
  "refresh_token": "eyJhbGci...",
  "token_type": "Bearer",
  "expires_in": 3600,
  "user": {
    "id": "uuid",
    "full_name": "John Doe",
    "email": "john@example.com",
    "blood_group": "A+",
    "existing_diseases": "Diabetes",
    "created_at": "2025-10-17T..."
  }
}
```

---

### 4. Resend OTP
**POST** `/api/auth/resend-otp`

**Request Body:**
```json
{
  "email": "john@example.com"
}
```

**Response (200):**
```json
{
  "message": "OTP sent successfully to your email",
  "email": "john@example.com"
}
```

---

### 5. Login
**POST** `/api/auth/login`

**Request Body:**
```json
{
  "email": "john@example.com",
  "password": "password123"
}
```

**Response (200):**
```json
{
  "message": "Login successful",
  "access_token": "eyJhbGci...",
  "refresh_token": "eyJhbGci...",
  "token_type": "Bearer",
  "expires_in": 3600,
  "user": {
    "id": "uuid",
    "full_name": "John Doe",
    "email": "john@example.com",
    "blood_group": "A+",
    "existing_diseases": "Diabetes",
    "created_at": "2025-10-17T..."
  }
}
```

---

### 6. Refresh Token
**POST** `/api/auth/refresh`

**Request Body:**
```json
{
  "refresh_token": "eyJhbGci..."
}
```

**Response (200):**
```json
{
  "access_token": "eyJhbGci...",
  "token_type": "Bearer",
  "expires_in": 3600
}
```

---

## 👤 Profile Endpoints (Protected)

**All profile endpoints require `Authorization` header:**
```
Authorization: Bearer <access_token>
```

---

### 7. Get Current User
**GET** `/api/auth/me`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200):**
```json
{
  "user": {
    "id": "uuid",
    "full_name": "John Doe",
    "email": "john@example.com",
    "blood_group": "A+",
    "existing_diseases": "Diabetes",
    "created_at": "2025-10-17T..."
  }
}
```

---

### 8. Get Profile Details
**GET** `/api/auth/profile`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200):**
```json
{
  "success": true,
  "profile": {
    "id": "uuid",
    "full_name": "John Doe",
    "email": "john@example.com",
    "blood_group": "A+",
    "existing_diseases": "Diabetes",
    "is_verified": true,
    "created_at": "2025-10-17T...",
    "updated_at": "2025-10-17T..."
  }
}
```

---

### 9. Update Profile
**PUT** `/api/auth/profile`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "fullName": "John Updated",
  "bloodGroup": "B+",
  "existingDiseases": "Diabetes, Hypertension"
}
```

**Response (200):**
```json
{
  "success": true,
  "message": "Profile updated successfully",
  "profile": {
    "id": "uuid",
    "full_name": "John Updated",
    "email": "john@example.com",
    "blood_group": "B+",
    "existing_diseases": "Diabetes, Hypertension",
    "updated_at": "2025-10-17T..."
  }
}
```

---

### 10. Logout
**POST** `/api/auth/logout`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200):**
```json
{
  "success": true,
  "message": "Logged out successfully"
}
```

**Note:** Since JWT is stateless, actual logout happens on the client side by removing stored tokens. This endpoint is mainly for logging/analytics.

---

## 🔴 Error Responses

### 400 - Bad Request
```json
{
  "error": "Full name is required"
}
```

### 401 - Unauthorized
```json
{
  "error": "Invalid email or password"
}
```

```json
{
  "error": "Token is missing"
}
```

```json
{
  "error": "Token has expired"
}
```

### 403 - Forbidden
```json
{
  "error": "Email not verified. Please verify your email first.",
  "requires_verification": true,
  "email": "john@example.com"
}
```

### 404 - Not Found
```json
{
  "error": "User not found"
}
```

### 409 - Conflict
```json
{
  "error": "User with this email already exists"
}
```

### 500 - Internal Server Error
```json
{
  "error": "An error occurred during signup. Please try again."
}
```

---

## 📱 Frontend Integration Examples

### Complete Authentication Flow

```javascript
// 1. Signup
const signup = async (userData) => {
  const response = await fetch('http://localhost:5000/api/auth/signup', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(userData)
  });
  return await response.json();
};

// 2. Verify OTP
const verifyOTP = async (email, otp) => {
  const response = await fetch('http://localhost:5000/api/auth/verify-otp', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, otp })
  });
  const data = await response.json();
  
  // Store tokens
  localStorage.setItem('access_token', data.access_token);
  localStorage.setItem('refresh_token', data.refresh_token);
  
  return data;
};

// 3. Get Profile
const getProfile = async () => {
  const token = localStorage.getItem('access_token');
  
  const response = await fetch('http://localhost:5000/api/auth/profile', {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  
  return await response.json();
};

// 4. Update Profile
const updateProfile = async (profileData) => {
  const token = localStorage.getItem('access_token');
  
  const response = await fetch('http://localhost:5000/api/auth/profile', {
    method: 'PUT',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(profileData)
  });
  
  return await response.json();
};

// 5. Logout
const logout = async () => {
  const token = localStorage.getItem('access_token');
  
  await fetch('http://localhost:5000/api/auth/logout', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  
  // Remove tokens
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
};
```

---

## 🧪 Testing with cURL

### Signup
```bash
curl -X POST http://localhost:5000/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "fullName": "John Doe",
    "email": "john@example.com",
    "password": "password123",
    "bloodGroup": "A+",
    "existingDiseases": "None"
  }'
```

### Get Profile (Protected)
```bash
curl -X GET http://localhost:5000/api/auth/profile \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Update Profile (Protected)
```bash
curl -X PUT http://localhost:5000/api/auth/profile \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "fullName": "John Updated",
    "bloodGroup": "B+"
  }'
```

### Logout (Protected)
```bash
curl -X POST http://localhost:5000/api/auth/logout \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```
