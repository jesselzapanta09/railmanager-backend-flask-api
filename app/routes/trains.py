from flask import Blueprint, request, jsonify
from app.utils.db import get_cursor
from app.middleware.auth import authenticate_token, require_admin
from app.utils.upload import save_file
from app.extensions import mysql
import os

trains_bp = Blueprint("trains", __name__)

# ── GET ALL TRAINS ─────────────────────────
@trains_bp.route("/", methods=["GET"])
@authenticate_token
def get_trains():
    cur = get_cursor()
    cur.execute("SELECT * FROM trains ORDER BY id DESC")
    trains = cur.fetchall()
    return jsonify({"success": True, "count": len(trains), "data": trains})


# ── GET SINGLE TRAIN ───────────────────────
@trains_bp.route("/<int:id>", methods=["GET"])
@authenticate_token
def get_train(id):
    cur = get_cursor()
    cur.execute("SELECT * FROM trains WHERE id=%s", (id,))
    train = cur.fetchone()
    if not train:
        return jsonify({"success": False, "message": "Train not found"}), 404
    return jsonify({"success": True, "data": train})


# ── CREATE TRAIN ───────────────────────────
@trains_bp.route("/", methods=["POST"])
@authenticate_token
@require_admin
def create_train():
    data = request.form
    file = request.files.get("image")

    train_name = data.get("train_name")
    price = data.get("price")
    route = data.get("route")

    if not train_name or not price or not route:
        return jsonify({"success": False, "message": "train_name, price, and route required"}), 400

    image = save_file(file, "trains") if file else None

    cur = get_cursor()
    cur.execute(
        "INSERT INTO trains (train_name, price, route, image) VALUES (%s,%s,%s,%s)",
        (train_name, price, route, image)
    )
    mysql.connection.commit()

    return jsonify({"success": True, "message": "Train created", "id": cur.lastrowid}), 201


# ── UPDATE TRAIN ───────────────────────────
@trains_bp.route("/<int:id>", methods=["PUT"])
@authenticate_token
@require_admin
def update_train(id):
    data = request.form
    file = request.files.get("image")

    train_name = data.get("train_name")
    price = data.get("price")
    route = data.get("route")

    cur = get_cursor()
    cur.execute("SELECT * FROM trains WHERE id=%s", (id,))
    train = cur.fetchone()
    if not train:
        return jsonify({"success": False, "message": "Train not found"}), 404

    image = train["image"]

    if file:
        if image:
            old_path = os.path.join("uploads", image.replace("/uploads/", ""))
            if os.path.exists(old_path):
                os.remove(old_path)
        image = save_file(file, "trains")

    # Remove image
    if data.get("remove_image") == "true":
        if image:
            old_path = os.path.join("uploads", image.replace("/uploads/", ""))
            if os.path.exists(old_path):
                os.remove(old_path)
        image = None

    cur.execute(
        "UPDATE trains SET train_name=%s, price=%s, route=%s, image=%s WHERE id=%s",
        (train_name, price, route, image, id)
    )
    mysql.connection.commit()

    return jsonify({"success": True, "message": "Train updated", "data": {
        "id": id, "train_name": train_name, "price": price, "route": route, "image": image
    }})


# ── DELETE TRAIN ───────────────────────────
@trains_bp.route("/<int:id>", methods=["DELETE"])
@authenticate_token
@require_admin
def delete_train(id):
    cur = get_cursor()
    cur.execute("SELECT * FROM trains WHERE id=%s", (id,))
    train = cur.fetchone()
    if not train:
        return jsonify({"success": False, "message": "Train not found"}), 404

    image = train["image"]
    if image:
        path = os.path.join("uploads", image.replace("/uploads/", ""))
        if os.path.exists(path):
            os.remove(path)

    cur.execute("DELETE FROM trains WHERE id=%s", (id,))
    mysql.connection.commit()

    return jsonify({"success": True, "message": "Train deleted"})