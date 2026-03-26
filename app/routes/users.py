from flask import Blueprint, request, jsonify
from app.utils.db import get_cursor
from app.middleware.auth import authenticate_token, require_admin
from app.utils.upload import save_file
import bcrypt, os

users_bp = Blueprint("users", __name__)

# ── GET ALL USERS ──────────────────────────────────────────────
@users_bp.route("/", methods=["GET"])
@authenticate_token
@require_admin
def get_users():
    cur = get_cursor()
    cur.execute(
        "SELECT id, username, email, role, avatar, email_verified_at, created_at FROM users WHERE id != %s ORDER BY id DESC",
        (request.user["id"],)
    )
    users = cur.fetchall()

    return jsonify({
        "success": True,
        "count": len(users),
        "data": users
    })


# ── GET SINGLE USER ────────────────────────────────────────────
@users_bp.route("/<int:id>", methods=["GET"])
@authenticate_token
@require_admin
def get_user(id):
    cur = get_cursor()
    cur.execute(
        "SELECT id, username, email, role, avatar, email_verified_at, created_at FROM users WHERE id = %s",
        (id,)
    )
    user = cur.fetchone()

    if not user:
        return jsonify({"success": False, "message": "User not found"}), 404

    return jsonify({"success": True, "data": user})


# ── CREATE USER ────────────────────────────────────────────────
@users_bp.route("/", methods=["POST"])
@authenticate_token
@require_admin
def create_user():
    data = request.form
    file = request.files.get("avatar")

    username = data.get("username")
    email = data.get("email")
    password = data.get("password")
    role = data.get("role", "user")

    if not username or not email or not password:
        return jsonify({
            "success": False,
            "message": "username, email, and password are required"
        }), 400

    if role not in ["admin", "user"]:
        return jsonify({
            "success": False,
            "message": "role must be admin or user"
        }), 400

    cur = get_cursor()

    # Check duplicates
    cur.execute(
        "SELECT id FROM users WHERE email=%s OR username=%s",
        (email, username)
    )
    if cur.fetchone():
        return jsonify({
            "success": False,
            "message": "Username or email already exists"
        }), 409

    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
    avatar = save_file(file, "avatars")

    cur.execute(
        "INSERT INTO users (username,email,password,role,avatar,email_verified_at) VALUES (%s,%s,%s,%s,%s,NULL)",
        (username, email, hashed, role, avatar)
    )
    cur.connection.commit()

    return jsonify({
        "success": True,
        "message": "User created successfully",
        "data": {
            "id": cur.lastrowid,
            "username": username,
            "email": email,
            "role": role,
            "avatar": avatar
        }
    }), 201


# ── UPDATE USER ────────────────────────────────────────────────
@users_bp.route("/<int:id>", methods=["PUT"])
@authenticate_token
@require_admin
def update_user(id):
    data = request.form
    file = request.files.get("avatar")

    username = data.get("username")
    email = data.get("email")
    role = data.get("role")
    password = data.get("password")

    if id == request.user["id"]:
        return jsonify({
            "success": False,
            "message": "Use Edit Profile to update your own account"
        }), 400

    if not username or not email or not role:
        return jsonify({
            "success": False,
            "message": "username, email, and role are required"
        }), 400

    if role not in ["admin", "user"]:
        return jsonify({
            "success": False,
            "message": "role must be admin or user"
        }), 400

    cur = get_cursor()

    cur.execute("SELECT * FROM users WHERE id=%s", (id,))
    existing = cur.fetchone()

    if not existing:
        return jsonify({"success": False, "message": "User not found"}), 404

    # Check duplicates
    cur.execute(
        "SELECT id FROM users WHERE (username=%s OR email=%s) AND id!=%s",
        (username, email, id)
    )
    if cur.fetchone():
        return jsonify({
            "success": False,
            "message": "Username or email already taken"
        }), 409

    avatar = existing["avatar"]

    # Upload new avatar
    if file:
        if avatar:
            old = os.path.join("uploads", avatar.replace("/uploads/", ""))
            if os.path.exists(old):
                os.remove(old)
        avatar = save_file(file, "avatars")

    # Remove avatar
    if data.get("remove_avatar") == "true":
        if avatar:
            old = os.path.join("uploads", avatar.replace("/uploads/", ""))
            if os.path.exists(old):
                os.remove(old)
        avatar = None

    fields = ["username=%s", "email=%s", "role=%s", "avatar=%s"]
    values = [username, email, role, avatar]

    if email != existing["email"]:
        fields.append("email_verified_at=NULL")

    if password:
        if len(password) < 6:
            return jsonify({
                "success": False,
                "message": "Password must be at least 6 characters"
            }), 400
        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
        fields.append("password=%s")
        values.append(hashed)

    values.append(id)

    cur.execute(f"UPDATE users SET {', '.join(fields)} WHERE id=%s", values)
    cur.connection.commit()

    return jsonify({
        "success": True,
        "message": "User updated successfully",
        "data": {
            "id": id,
            "username": username,
            "email": email,
            "role": role,
            "avatar": avatar
        }
    })


# ── DELETE USER ────────────────────────────────────────────────
@users_bp.route("/<int:id>", methods=["DELETE"])
@authenticate_token
@require_admin
def delete_user(id):
    if id == request.user["id"]:
        return jsonify({
            "success": False,
            "message": "You cannot delete your own account"
        }), 400

    cur = get_cursor()

    cur.execute("SELECT * FROM users WHERE id=%s", (id,))
    user = cur.fetchone()

    if not user:
        return jsonify({"success": False, "message": "User not found"}), 404

    avatar = user["avatar"]

    if avatar:
        path = os.path.join("uploads", avatar.replace("/uploads/", ""))
        if os.path.exists(path):
            os.remove(path)

    cur.execute("DELETE FROM users WHERE id=%s", (id,))
    cur.connection.commit()

    return jsonify({
        "success": True,
        "message": "User deleted successfully"
    })