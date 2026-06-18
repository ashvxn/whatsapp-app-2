from flask import Blueprint, request, jsonify, current_app

auth_bp = Blueprint("auth", __name__, url_prefix="/api")

@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.json or {}
    username = data.get("username", "")
    password = data.get("password", "")

    if username == current_app.config.get("LOGIN_USERNAME") and password == current_app.config.get("LOGIN_PASSWORD"):
        return jsonify({"token": current_app.config.get("AUTH_TOKEN")})
    return jsonify({"error": "Invalid username or password"}), 401
