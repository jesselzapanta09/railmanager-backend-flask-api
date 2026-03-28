from flask import Blueprint, jsonify

about_bp = Blueprint("about", __name__)

@about_bp.route("/", methods=["GET"])
def get_about():
    return jsonify({
        "title": "Flask API",
        "subtitle": "Backend Engine"
    })