from functools import wraps
from flask import request, jsonify
import jwt
from app.extensions import mysql
import os


def authenticate_token(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        parts = auth_header.split(" ")

        if len(parts) != 2 or parts[0] != "Bearer" or not parts[1]:
            return jsonify({"success": False, "message": "Access token required"}), 401

        token = parts[1]

        cur = mysql.connection.cursor()
        cur.execute("SELECT id FROM token_blacklist WHERE token = %s", (token,))
        if cur.fetchone():
            return jsonify({"success": False, "message": "Token has been invalidated"}), 401

        try:
            decoded = jwt.decode(token, os.getenv("JWT_SECRET"), algorithms=["HS256"])
            request.user = {
                "id": decoded.get("id"),
                "role": decoded.get("role"),
                "email": decoded.get("email"),
            }
            request.token = token
        except jwt.ExpiredSignatureError:
            return jsonify({"success": False, "message": "Token has expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"success": False, "message": "Invalid token"}), 403

        return f(*args, **kwargs)

    return decorated


def require_admin(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if request.user.get("role") != "admin":
            return jsonify({"success": False, "message": "Admin access required"}), 403
        return f(*args, **kwargs)

    return decorated
