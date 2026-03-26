from datetime import datetime, timedelta
import os
import secrets

import bcrypt
import jwt
from flask import Blueprint, request, jsonify

from app.extensions import mysql
from app.utils.db import get_cursor
from app.utils.mailer import send_reset_email, send_verification_email
from app.utils.upload import save_file
from app.middleware.auth import authenticate_token


auth_bp = Blueprint("auth", __name__)


def create_token(user_id, type_, expires_in_hours=24):
    token = secrets.token_hex(32)
    expires_at = datetime.now() + timedelta(hours=expires_in_hours)

    cur = get_cursor()
    cur.execute("DELETE FROM user_tokens WHERE user_id=%s AND type=%s", (user_id, type_))
    cur.execute(
        "INSERT INTO user_tokens (user_id, token, type, expires_at) VALUES (%s, %s, %s, %s)",
        (user_id, token, type_, expires_at),
    )
    mysql.connection.commit()
    return token


def create_access_token(user):
    payload = {
        "id": user["id"],
        "email": user["email"],
        "role": user["role"],
        "exp": datetime.utcnow() + timedelta(hours=24),
    }
    return jwt.encode(payload, os.getenv("JWT_SECRET"), algorithm="HS256")


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")

    if not username or not email or not password:
        return jsonify({"success": False, "message": "All fields are required"}), 400

    cur = get_cursor()
    cur.execute("SELECT id FROM users WHERE email=%s OR username=%s", (email, username))
    if cur.fetchone():
        return jsonify({"success": False, "message": "Username or email already exists"}), 409

    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    cur.execute(
        "INSERT INTO users (username, email, password, role) VALUES (%s, %s, %s, %s)",
        (username, email, hashed, "admin"),
    )
    mysql.connection.commit()

    user_id = cur.lastrowid
    token = create_token(user_id, "email_verify", 24)
    send_verification_email(email, username, token)

    return jsonify(
        {
            "success": True,
            "message": "Account created! Please check your email to verify your account.",
            "data": {"id": user_id, "username": username, "email": email, "role": "admin"},
        }
    ), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"success": False, "message": "Email and password are required"}), 400

    cur = get_cursor()
    cur.execute("SELECT * FROM users WHERE email=%s", (email,))
    user = cur.fetchone()
    if not user:
        return jsonify({"success": False, "message": "Invalid email or password"}), 401

    if not bcrypt.checkpw(password.encode("utf-8"), user["password"].encode("utf-8")):
        return jsonify({"success": False, "message": "Invalid email or password"}), 401

    if not user["email_verified_at"]:
        return (
            jsonify(
                {
                    "success": False,
                    "message": "Please verify your email before logging in.",
                    "code": "EMAIL_NOT_VERIFIED",
                }
            ),
            403,
        )

    access_token = create_access_token(user)
    return jsonify(
        {
            "success": True,
            "message": "Login successful",
            "data": {
                "token": access_token,
                "user": {
                    "id": user["id"],
                    "username": user["username"],
                    "email": user["email"],
                    "role": user["role"],
                    "avatar": user.get("avatar"),
                },
            },
        }
    )


@auth_bp.route("/logout", methods=["POST"])
@authenticate_token
def logout():
    token = request.token
    cur = get_cursor()
    cur.execute("INSERT INTO token_blacklist (token) VALUES (%s)", (token,))
    mysql.connection.commit()
    return jsonify({"success": True, "message": "Logged out successfully"})


@auth_bp.route("/verify-email")
def verify_email():
    token = request.args.get("token")
    if not token:
        return jsonify({"success": False, "message": "Token is required"}), 400

    cur = get_cursor()
    cur.execute("SELECT * FROM user_tokens WHERE token=%s AND type='email_verify'", (token,))
    row = cur.fetchone()
    if not row:
        return jsonify({"success": False, "message": "Invalid or expired verification link."}), 400
    if datetime.now() > row["expires_at"]:
        return jsonify({"success": False, "message": "Verification link has expired."}), 400

    cur.execute("UPDATE users SET email_verified_at=NOW() WHERE id=%s", (row["user_id"],))
    cur.execute("DELETE FROM user_tokens WHERE id=%s", (row["id"],))
    mysql.connection.commit()
    return jsonify({"success": True, "message": "Email verified successfully! You can now log in."})


@auth_bp.route("/resend-verification", methods=["POST"])
def resend_verification():
    data = request.get_json(silent=True) or {}
    email = data.get("email")

    if not email:
        return jsonify({"success": False, "message": "Email is required"}), 400

    cur = get_cursor()
    cur.execute("SELECT * FROM users WHERE email=%s", (email,))
    user = cur.fetchone()

    if not user:
        return jsonify({"success": True, "message": "If that email exists, a verification link has been sent."})

    if user.get("email_verified_at"):
        return jsonify({"success": False, "message": "Email is already verified."}), 400

    token = create_token(user["id"], "email_verify", 24)
    send_verification_email(user["email"], user["username"], token)

    return jsonify({"success": True, "message": "Verification email sent successfully."})


@auth_bp.route("/forgot-password", methods=["POST"])
def forgot_password():
    data = request.get_json(silent=True) or {}
    email = data.get("email")
    if not email:
        return jsonify({"success": False, "message": "Email is required"}), 400

    cur = get_cursor()
    cur.execute("SELECT * FROM users WHERE email=%s", (email,))
    user = cur.fetchone()
    if user:
        token = create_token(user["id"], "password_reset", 1)
        send_reset_email(email, user["username"], token)

    return jsonify({"success": True, "message": "If that email exists, a reset link has been sent."})


@auth_bp.route("/reset-password", methods=["POST"])
def reset_password():
    data = request.get_json(silent=True) or {}
    token = data.get("token")
    password = data.get("password")

    if not token or not password:
        return jsonify({"success": False, "message": "Token and new password are required"}), 400
    if len(password) < 6:
        return jsonify({"success": False, "message": "Password must be at least 6 characters"}), 400

    cur = get_cursor()
    cur.execute("SELECT * FROM user_tokens WHERE token=%s AND type='password_reset'", (token,))
    row = cur.fetchone()
    if not row or datetime.now() > row["expires_at"]:
        return jsonify({"success": False, "message": "Invalid or expired reset link."}), 400

    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    cur.execute("UPDATE users SET password=%s WHERE id=%s", (hashed, row["user_id"]))
    cur.execute("DELETE FROM user_tokens WHERE id=%s", (row["id"],))
    mysql.connection.commit()
    return jsonify({"success": True, "message": "Password reset successfully! You can now log in."})


@auth_bp.route("/change-password", methods=["POST"])
@authenticate_token
def change_password():
    user_id = request.user["id"]
    data = request.get_json(silent=True) or {}
    current_password = data.get("currentPassword")
    new_password = data.get("newPassword")

    if not current_password or not new_password:
        return jsonify({"success": False, "message": "Both passwords are required"}), 400
    if len(new_password) < 6:
        return jsonify({"success": False, "message": "New password must be at least 6 characters"}), 400

    cur = get_cursor()
    cur.execute("SELECT * FROM users WHERE id=%s", (user_id,))
    user = cur.fetchone()
    if not user or not bcrypt.checkpw(current_password.encode("utf-8"), user["password"].encode("utf-8")):
        return jsonify({"success": False, "message": "Current password is incorrect"}), 401

    hashed = bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    cur.execute("UPDATE users SET password=%s WHERE id=%s", (hashed, user_id))
    mysql.connection.commit()
    return jsonify({"success": True, "message": "Password changed successfully!"})


@auth_bp.route("/update-profile", methods=["POST"])
@authenticate_token
def update_profile():
    user_id = request.user["id"]
    data = request.form
    file = request.files.get("avatar")

    username = data.get("username")
    email = data.get("email")
    remove_avatar = data.get("remove_avatar")

    if not username:
        return jsonify({"success": False, "message": "Username is required"}), 400

    cur = get_cursor()
    cur.execute("SELECT * FROM users WHERE id=%s", (user_id,))
    user = cur.fetchone()

    if not user:
        return jsonify({"success": False, "message": "User not found"}), 404

    if username != user["username"]:
        cur.execute("SELECT id FROM users WHERE username=%s AND id!=%s", (username, user_id))
        if cur.fetchone():
            return jsonify({"success": False, "message": "Username is already taken"}), 409

    new_email = email or user["email"]
    if new_email != user["email"]:
        cur.execute("SELECT id FROM users WHERE email=%s AND id!=%s", (new_email, user_id))
        if cur.fetchone():
            return jsonify({"success": False, "message": "Email is already in use by another account"}), 409

    avatar_url = user.get("avatar")
    if file:
        if avatar_url and os.path.exists(avatar_url.lstrip("/")):
            os.remove(avatar_url.lstrip("/"))
        avatar_url = save_file(file, "avatars")

    if remove_avatar == "true":
        if avatar_url and os.path.exists(avatar_url.lstrip("/")):
            os.remove(avatar_url.lstrip("/"))
        avatar_url = None

    email_changed = new_email != user["email"]
    update_sql = "UPDATE users SET username=%s, email=%s, avatar=%s"
    params = [username, new_email, avatar_url]
    if email_changed:
        update_sql += ", email_verified_at=NULL"
    update_sql += " WHERE id=%s"
    params.append(user_id)

    cur.execute(update_sql, tuple(params))
    mysql.connection.commit()

    if email_changed:
        token = create_token(user_id, "email_verify", 24)
        send_verification_email(new_email, username, token)

    cur.execute("SELECT id, username, email, role, avatar FROM users WHERE id=%s", (user_id,))
    updated_user = cur.fetchone()
    return jsonify(
        {
            "success": True,
            "message": "Email updated! Please verify your new email address."
            if email_changed
            else "Profile updated successfully!",
            "data": updated_user,
            "emailChanged": email_changed,
        }
    )
