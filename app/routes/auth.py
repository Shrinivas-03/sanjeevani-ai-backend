from flask import Blueprint, request, jsonify, current_app
from app import supabase
import bcrypt
import jwt
import re
from datetime import datetime, timedelta
from functools import wraps
from app.utils.email import generate_otp, send_otp_email

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@auth_bp.route("/test", methods=["GET"])
def test():
    """Test endpoint to check if API is working"""
    return jsonify(
        {"message": "API is working!", "timestamp": datetime.utcnow().isoformat()}
    ), 200


def validate_email(email):
    """Validate email format"""
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return re.match(pattern, email) is not None


def validate_password(password):
    """Validate password strength (min 6 characters)"""
    return len(password) >= 6


def hash_password(password):
    """Hash password using bcrypt"""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password, hashed_password):
    """Verify password against bcrypt hash"""
    return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))


def generate_tokens(user_id, email):
    """Generate access and refresh tokens"""
    access_token_payload = {
        "user_id": user_id,
        "email": email,
        "type": "access",
        "exp": datetime.utcnow()
        + timedelta(seconds=current_app.config["JWT_ACCESS_TOKEN_EXPIRES"]),
        "iat": datetime.utcnow(),
    }

    refresh_token_payload = {
        "user_id": user_id,
        "email": email,
        "type": "refresh",
        "exp": datetime.utcnow()
        + timedelta(seconds=current_app.config["JWT_REFRESH_TOKEN_EXPIRES"]),
        "iat": datetime.utcnow(),
    }

    access_token = jwt.encode(
        access_token_payload, current_app.config["JWT_SECRET_KEY"], algorithm="HS256"
    )
    refresh_token = jwt.encode(
        refresh_token_payload, current_app.config["JWT_SECRET_KEY"], algorithm="HS256"
    )

    return access_token, refresh_token


def token_required(f):
    """Decorator to protect routes with JWT"""

    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        # Get token from Authorization header
        if "Authorization" in request.headers:
            auth_header = request.headers["Authorization"]
            try:
                token = auth_header.split(" ")[1]  # Bearer <token>
            except IndexError:
                return jsonify({"error": "Invalid token format"}), 401

        if not token:
            return jsonify({"error": "Token is missing"}), 401

        try:
            # Decode token
            payload = jwt.decode(
                token, current_app.config["JWT_SECRET_KEY"], algorithms=["HS256"]
            )

            # Check if it's an access token
            if payload.get("type") != "access":
                return jsonify({"error": "Invalid token type"}), 401

            # Get user from database
            user_result = (
                supabase.table("users")
                .select("*")
                .eq("id", payload["user_id"])
                .execute()
            )

            if not user_result.data or len(user_result.data) == 0:
                return jsonify({"error": "User not found"}), 401

            current_user = user_result.data[0]

        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token has expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401
        except Exception as e:
            return jsonify({"error": "Token verification failed"}), 401

        return f(current_user, *args, **kwargs)

    return decorated


@auth_bp.route("/signup", methods=["POST"])
def signup():
    """Step 1: Create account and send OTP for email verification"""
    try:
        # Get data from request
        data = request.get_json()

        # Debug: Log received data (remove passwords in production)
        print(f"[DEBUG] Signup request data: {data}")

        # Extract fields with proper None handling
        full_name = (data.get("fullName") or "").strip()
        email = (data.get("email") or "").strip().lower()
        password = data.get("password", "")
        blood_group = (data.get("bloodGroup") or "").strip()
        existing_diseases = (data.get("existingDiseases") or "").strip()

        # Validation
        if not full_name:
            print(f"[ERROR] Full name missing")
            return jsonify({"error": "Full name is required"}), 400

        if not email or not validate_email(email):
            print(f"[ERROR] Invalid email: {email}")
            return jsonify({"error": "Valid email address is required"}), 400

        if not password or not validate_password(password):
            print(f"[ERROR] Invalid password length")
            return jsonify(
                {"error": "Password must be at least 6 characters long"}
            ), 400

        if not blood_group:
            print(f"[ERROR] Blood group missing")
            return jsonify({"error": "Blood group is required"}), 400

        # Check if user already exists
        existing_user = supabase.table("users").select("*").eq("email", email).execute()

        if existing_user.data and len(existing_user.data) > 0:
            user = existing_user.data[0]
            # If user exists but not verified, allow resend OTP
            if not user.get("is_verified", False):
                # Generate new OTP
                otp = generate_otp()
                otp_expiry = datetime.utcnow() + timedelta(
                    minutes=current_app.config["OTP_EXPIRY_MINUTES"]
                )

                # Update OTP in database
                supabase.table("users").update(
                    {"otp": otp, "otp_expiry": otp_expiry.isoformat()}
                ).eq("email", email).execute()

                # Send OTP email
                if send_otp_email(email, otp, full_name):
                    return jsonify(
                        {
                            "message": "OTP sent to your email. Please verify to complete registration.",
                            "email": email,
                            "requires_verification": True,
                        }
                    ), 200
                else:
                    return jsonify(
                        {"error": "Failed to send OTP email. Please try again."}
                    ), 500
            else:
                return jsonify({"error": "User with this email already exists"}), 409

        # Hash password with bcrypt
        hashed_password = hash_password(password)

        # Generate OTP
        otp = generate_otp()
        otp_expiry = datetime.utcnow() + timedelta(
            minutes=current_app.config["OTP_EXPIRY_MINUTES"]
        )

        # Create user in Supabase (unverified)
        user_data = {
            "full_name": full_name,
            "email": email,
            "password": hashed_password,
            "blood_group": blood_group,
            "existing_diseases": existing_diseases if existing_diseases else None,
            "is_verified": False,
            "otp": otp,
            "otp_expiry": otp_expiry.isoformat(),
        }

        result = supabase.table("users").insert(user_data).execute()

        if result.data:
            # Send OTP email
            if send_otp_email(email, otp, full_name):
                return jsonify(
                    {
                        "message": "Account created! OTP sent to your email. Please verify to complete registration.",
                        "email": email,
                        "requires_verification": True,
                    }
                ), 201
            else:
                # Delete user if email sending fails
                supabase.table("users").delete().eq("email", email).execute()
                return jsonify(
                    {"error": "Failed to send OTP email. Please try again."}
                ), 500
        else:
            return jsonify({"error": "Failed to create account"}), 500

    except Exception as e:
        print(f"Signup error: {str(e)}")
        return jsonify(
            {"error": "An error occurred during signup. Please try again."}
        ), 500


@auth_bp.route("/login", methods=["POST"])
def login():
    try:
        # Get data from request
        data = request.get_json()

        email = data.get("email", "").strip().lower()
        password = data.get("password", "")

        # Validation
        if not email or not password:
            return jsonify({"error": "Email and password are required"}), 400

        # Find user
        result = supabase.table("users").select("*").eq("email", email).execute()

        if not result.data or len(result.data) == 0:
            return jsonify({"error": "Invalid email or password"}), 401

        user = result.data[0]

        # Check if user is verified
        if not user.get("is_verified", False):
            return jsonify(
                {
                    "error": "Email not verified. Please verify your email first.",
                    "requires_verification": True,
                    "email": email,
                }
            ), 403

        # Verify password with bcrypt
        if not verify_password(password, user["password"]):
            return jsonify({"error": "Invalid email or password"}), 401

        # Generate JWT tokens
        access_token, refresh_token = generate_tokens(user["id"], user["email"])

        # Return user data without password along with tokens
        return jsonify(
            {
                "message": "Login successful",
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "Bearer",
                "expires_in": current_app.config["JWT_ACCESS_TOKEN_EXPIRES"],
                "user": {
                    "id": user["id"],
                    "full_name": user["full_name"],
                    "email": user["email"],
                    "blood_group": user["blood_group"],
                    "existing_diseases": user["existing_diseases"],
                    "created_at": user["created_at"],
                },
            }
        ), 200

    except Exception as e:
        print(f"Login error: {str(e)}")
        return jsonify(
            {"error": "An error occurred during login. Please try again."}
        ), 500


@auth_bp.route("/refresh", methods=["POST"])
def refresh():
    """Refresh access token using refresh token"""
    try:
        data = request.get_json()
        refresh_token = data.get("refresh_token")

        if not refresh_token:
            return jsonify({"error": "Refresh token is required"}), 400

        try:
            # Decode refresh token
            payload = jwt.decode(
                refresh_token,
                current_app.config["JWT_SECRET_KEY"],
                algorithms=["HS256"],
            )

            # Check if it's a refresh token
            if payload.get("type") != "refresh":
                return jsonify({"error": "Invalid token type"}), 401

            # Generate new access token
            access_token, _ = generate_tokens(payload["user_id"], payload["email"])

            return jsonify(
                {
                    "access_token": access_token,
                    "token_type": "Bearer",
                    "expires_in": current_app.config["JWT_ACCESS_TOKEN_EXPIRES"],
                }
            ), 200

        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Refresh token has expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid refresh token"}), 401

    except Exception as e:
        print(f"Refresh token error: {str(e)}")
        return jsonify({"error": "An error occurred while refreshing token"}), 500


@auth_bp.route("/me", methods=["GET"])
@token_required
def get_current_user(current_user):
    """Get current user information (protected route)"""
    return jsonify(
        {
            "user": {
                "id": current_user["id"],
                "full_name": current_user["full_name"],
                "email": current_user["email"],
                "blood_group": current_user["blood_group"],
                "existing_diseases": current_user["existing_diseases"],
                "created_at": current_user["created_at"],
            }
        }
    ), 200


@auth_bp.route("/user-details", methods=["GET"])
@token_required
def get_user_details(current_user):
    """Get user details for the logged-in user"""
    return jsonify(
        {
            "user": {
                "id": current_user["id"],
                "full_name": current_user["full_name"],
                "email": current_user["email"],
                "blood_group": current_user["blood_group"],
                "existing_diseases": current_user["existing_diseases"],
                "created_at": current_user["created_at"],
            }
        }
    ), 200


@auth_bp.route("/profile", methods=["GET"])
@token_required
def get_profile(current_user):
    """Get detailed user profile (protected route)"""
    return jsonify(
        {
            "success": True,
            "profile": {
                "id": current_user["id"],
                "full_name": current_user["full_name"],
                "email": current_user["email"],
                "blood_group": current_user["blood_group"],
                "existing_diseases": current_user["existing_diseases"],
                "is_verified": current_user.get("is_verified", False),
                "created_at": current_user["created_at"],
                "updated_at": current_user.get("updated_at"),
            },
        }
    ), 200


@auth_bp.route("/profile", methods=["PUT"])
@token_required
def update_profile(current_user):
    """Update user profile (protected route)"""
    try:
        data = request.get_json()

        # Fields that can be updated
        update_data = {}

        if "fullName" in data and data["fullName"]:
            update_data["full_name"] = data["fullName"].strip()

        if "bloodGroup" in data and data["bloodGroup"]:
            update_data["blood_group"] = data["bloodGroup"].strip()

        if "existingDiseases" in data:
            update_data["existing_diseases"] = (data["existingDiseases"] or "").strip()

        if not update_data:
            return jsonify({"error": "No fields to update"}), 400

        # Update in database
        result = (
            supabase.table("users")
            .update(update_data)
            .eq("id", current_user["id"])
            .execute()
        )

        if result.data:
            updated_user = result.data[0]
            return jsonify(
                {
                    "success": True,
                    "message": "Profile updated successfully",
                    "profile": {
                        "id": updated_user["id"],
                        "full_name": updated_user["full_name"],
                        "email": updated_user["email"],
                        "blood_group": updated_user["blood_group"],
                        "existing_diseases": updated_user["existing_diseases"],
                        "updated_at": updated_user.get("updated_at"),
                    },
                }
            ), 200
        else:
            return jsonify({"error": "Failed to update profile"}), 500

    except Exception as e:
        print(f"Profile update error: {str(e)}")
        return jsonify({"error": "An error occurred while updating profile"}), 500


@auth_bp.route("/edit-profile", methods=["PUT"])
@token_required
def edit_profile(current_user):
    """Edit user profile (protected route)"""
    try:
        data = request.get_json()

        # Fields that can be updated
        update_data = {}

        if "fullName" in data and data["fullName"]:
            update_data["full_name"] = data["fullName"].strip()

        if "bloodGroup" in data and data["bloodGroup"]:
            update_data["blood_group"] = data["bloodGroup"].strip()

        if "existingDiseases" in data:
            update_data["existing_diseases"] = (data["existingDiseases"] or "").strip()

        if not update_data:
            return jsonify({"error": "No fields to update"}), 400

        # Update in database
        result = (
            supabase.table("users")
            .update(update_data)
            .eq("id", current_user["id"])
            .execute()
        )

        if result.data:
            updated_user = result.data[0]
            return jsonify(
                {
                    "success": True,
                    "message": "Profile updated successfully",
                    "profile": {
                        "id": updated_user["id"],
                        "full_name": updated_user["full_name"],
                        "email": updated_user["email"],
                        "blood_group": updated_user["blood_group"],
                        "existing_diseases": updated_user["existing_diseases"],
                        "updated_at": updated_user.get("updated_at"),
                    },
                }
            ), 200
        else:
            return jsonify({"error": "Failed to update profile"}), 500

    except Exception as e:
        print(f"Profile update error: {str(e)}")
        return jsonify({"error": "An error occurred while updating profile"}), 500


@auth_bp.route("/logout", methods=["POST"])
@token_required
def logout(current_user):
    """Logout user (protected route)
    Note: Since we're using stateless JWT, actual logout happens on client side
    by removing tokens. This endpoint is mainly for logging/analytics purposes.
    """
    try:
        # You can log the logout event or invalidate refresh token here if needed
        print(f"[INFO] User {current_user['email']} logged out at {datetime.utcnow()}")

        return jsonify({"success": True, "message": "Logged out successfully"}), 200

    except Exception as e:
        print(f"Logout error: {str(e)}")
        return jsonify({"error": "An error occurred during logout"}), 500


@auth_bp.route("/verify-otp", methods=["POST"])
def verify_otp():
    """Step 2: Verify OTP and complete registration"""
    try:
        data = request.get_json()

        email = data.get("email", "").strip().lower()
        otp = data.get("otp", "").strip()

        # Validation
        if not email or not otp:
            return jsonify({"error": "Email and OTP are required"}), 400

        # Find user
        result = supabase.table("users").select("*").eq("email", email).execute()

        if not result.data or len(result.data) == 0:
            return jsonify({"error": "User not found"}), 404

        user = result.data[0]

        # Check if already verified
        if user.get("is_verified", False):
            return jsonify({"error": "Email already verified"}), 400

        # Check OTP
        if user.get("otp") != otp:
            return jsonify({"error": "Invalid OTP"}), 401

        # Check OTP expiry
        otp_expiry = datetime.fromisoformat(user["otp_expiry"].replace("Z", "+00:00"))
        if datetime.utcnow() > otp_expiry.replace(tzinfo=None):
            return jsonify({"error": "OTP has expired. Please request a new one."}), 401

        # Mark user as verified and clear OTP
        supabase.table("users").update(
            {"is_verified": True, "otp": None, "otp_expiry": None}
        ).eq("email", email).execute()

        # Generate JWT tokens
        access_token, refresh_token = generate_tokens(user["id"], user["email"])

        # Return success with tokens
        return jsonify(
            {
                "message": "Email verified successfully!",
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "Bearer",
                "expires_in": current_app.config["JWT_ACCESS_TOKEN_EXPIRES"],
                "user": {
                    "id": user["id"],
                    "full_name": user["full_name"],
                    "email": user["email"],
                    "blood_group": user["blood_group"],
                    "existing_diseases": user["existing_diseases"],
                    "created_at": user["created_at"],
                },
            }
        ), 200

    except Exception as e:
        print(f"OTP verification error: {str(e)}")
        return jsonify(
            {"error": "An error occurred during OTP verification. Please try again."}
        ), 500


@auth_bp.route("/resend-otp", methods=["POST"])
def resend_otp():
    """Resend OTP to user's email"""
    try:
        data = request.get_json()

        email = data.get("email", "").strip().lower()

        # Validation
        if not email:
            return jsonify({"error": "Email is required"}), 400

        # Find user
        result = supabase.table("users").select("*").eq("email", email).execute()

        if not result.data or len(result.data) == 0:
            return jsonify({"error": "User not found"}), 404

        user = result.data[0]

        # Check if already verified
        if user.get("is_verified", False):
            return jsonify({"error": "Email already verified"}), 400

        # Generate new OTP
        otp = generate_otp()
        otp_expiry = datetime.utcnow() + timedelta(
            minutes=current_app.config["OTP_EXPIRY_MINUTES"]
        )

        # Update OTP in database
        supabase.table("users").update(
            {"otp": otp, "otp_expiry": otp_expiry.isoformat()}
        ).eq("email", email).execute()

        # Send OTP email
        if send_otp_email(email, otp, user["full_name"]):
            return jsonify(
                {"message": "OTP sent successfully to your email", "email": email}
            ), 200
        else:
            return jsonify(
                {"error": "Failed to send OTP email. Please try again."}
            ), 500

    except Exception as e:
        print(f"Resend OTP error: {str(e)}")
        return jsonify(
            {"error": "An error occurred while resending OTP. Please try again."}
        ), 500
