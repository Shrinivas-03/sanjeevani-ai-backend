# React Native API Integration Guide

This guide explains how to integrate the user profile APIs into your React Native application.

## Authentication

All profile-related API endpoints require a valid JSON Web Token (JWT) to be passed in the `Authorization` header of your request. The token should be prefixed with `Bearer `.

```javascript
const headers = {
  'Content-Type': 'application/json',
  'Authorization': `Bearer ${your_jwt_token}`,
};
```

Replace `${your_jwt_token}` with the actual JWT token you receive after a successful login.

---

## 1. Fetching User Details

To get the details of the currently logged-in user, make a `GET` request to the `/api/auth/user-details` endpoint.

### Endpoint

`GET /api/auth/user-details`

### Example Request

Here is an example of how to fetch user details in a React Native app:

```javascript
const fetchUserDetails = async (token) => {
  try {
    const response = await fetch('http://<your-backend-ip>:5000/api/auth/user-details', {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.error || 'Failed to fetch user details');
    }

    console.log('User Details:', data.user);
    return data.user;
  } catch (error) {
    console.error('Error fetching user details:', error.message);
  }
};

// Usage:
// const userToken = 'your_jwt_token';
// fetchUserDetails(userToken);
```

### Success Response

A successful request will return a JSON object containing the user's details.

```json
{
  "user": {
    "id": "e95f278a-e98c-40d9-845b-62c4259ceb1a",
    "full_name": "shrinivas",
    "email": "shrinivasnadager03@gmail.com",
    "blood_group": "AB-",
    "existing_diseases": "bp",
    "created_at": "2025-10-23T09:04:09.173469+00:00"
  }
}
```

---

## 2. Editing User Profile

To update the profile details of the logged-in user, make a `PUT` request to the `/api/auth/edit-profile` endpoint.

### Endpoint

`PUT /api/auth/edit-profile`

### Request Body

The request body should be a JSON object containing the fields you want to update. The available fields are `fullName`, `bloodGroup`, and `existingDiseases`.

```json
{
  "fullName": "Shrinivas Nadager",
  "bloodGroup": "O+",
  "existingDiseases": "None"
}
```

### Example Request

Here is an example of how to update the user profile in a React Native app:

```javascript
const updateUserProfile = async (token, profileData) => {
  try {
    const response = await fetch('http://<your-backend-ip>:5000/api/auth/edit-profile', {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify(profileData),
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.error || 'Failed to update profile');
    }

    console.log('Profile updated successfully:', data.profile);
    return data.profile;
  } catch (error) {
    console.error('Error updating profile:', error.message);
  }
};

// Usage:
// const userToken = 'your_jwt_token';
// const newProfileData = {
//   fullName: 'Shrinivas N',
//   existingDiseases: 'None',
// };
// updateUserProfile(userToken, newProfileData);
```

### Success Response

A successful request will return a JSON object with a success message and the updated profile information.

```json
{
  "success": true,
  "message": "Profile updated successfully",
  "profile": {
    "id": "e95f278a-e98c-40d9-845b-62c4259ceb1a",
    "full_name": "Shrinivas N",
    "email": "shrinivasnadager03@gmail.com",
    "blood_group": "AB-",
    "existing_diseases": "None",
    "updated_at": "2025-11-04T12:30:00.123456+00:00"
  }
}
```

**Important:**

*   Replace `<your-backend-ip>` with the actual IP address of the machine running your Flask backend. When running on the same machine, you can often use your machine's local IP address. You cannot use `localhost` or `127.0.0.1` from a physical device unless you have set up port forwarding.
*   Ensure your Flask application is running and accessible from the device or emulator where you are running your React Native app.
