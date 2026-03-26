from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from werkzeug.utils import safe_join
from .extensions import mysql
from .config import Config
import os


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.url_map.strict_slashes = False

    base_dir = os.path.abspath(os.path.join(app.root_path, ".."))
    upload_root = os.path.join(base_dir, "uploads")
    app.config["UPLOAD_FOLDER"] = upload_root

    mysql.init_app(app)

    allowed_origins = [
        origin.strip()
        for origin in os.getenv("ALLOWED_ORIGINS", "").split(",")
        if origin.strip()
    ]

    cors_resources = {
        r"/api/*": {
            "origins": allowed_origins or "*",
            "methods": ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
            "allow_headers": ["Authorization", "Content-Type"],
            "supports_credentials": True,
        }
    }
    CORS(app, resources=cors_resources)

    @app.before_request
    def handle_preflight():
        if request.method == "OPTIONS":
            return ("", 204)

    from .routes.auth import auth_bp
    from .routes.trains import trains_bp
    from .routes.users import users_bp

    app.register_blueprint(auth_bp, url_prefix="/api")
    app.register_blueprint(trains_bp, url_prefix="/api/trains")
    app.register_blueprint(users_bp, url_prefix="/api/users")

    @app.route("/uploads/<path:filename>")
    def uploaded_file(filename):
        safe_path = safe_join(app.config["UPLOAD_FOLDER"], filename)
        if not safe_path or not os.path.isfile(safe_path):
            return jsonify({"success": False, "message": "File not found"}), 404

        directory, file_name = os.path.split(safe_path)
        return send_from_directory(directory, file_name)

    @app.route("/")
    def home():
        return {"success": True, "message": "RailManager API v2.0"}

    @app.route("/health")
    def health():
        return jsonify({"success": True, "message": "API is running"})

    return app
