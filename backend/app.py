from flask import Flask, send_from_directory, make_response, request, jsonify
from flask_cors import CORS
from config import Config
from extensions import db
from sqlalchemy import text
import os
import hmac
import mimetypes

from routes.contacts import contacts_bp
from routes.campaigns import campaigns_bp
from routes.templates import templates_bp
from routes.webhook import webhook
from routes.analytics import analytics_bp
from routes.calls import calls_bp
from routes.auth import auth_bp
from flask_cors import CORS


def create_app():
    app = Flask(__name__, 
                static_folder="../frontend/dist", 
                static_url_path="/")
    app.config.from_object(Config)
    # CORS(app)
    CORS(app, origins="*", allow_headers="*")  # or specify your frontend URL

    # ✅ ENSURE DIRECTORIES EXIST
    os.makedirs("static/posters", exist_ok=True)
    os.makedirs("static/id_proofs", exist_ok=True)

    # ✅ INIT DB WITH APP
    db.init_app(app)

    # ✅ REGISTER ROUTES
    app.register_blueprint(contacts_bp)
    app.register_blueprint(campaigns_bp)
    app.register_blueprint(templates_bp)
    app.register_blueprint(webhook)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(calls_bp)
    app.register_blueprint(auth_bp)

    @app.before_request
    def require_api_auth():
        if request.method == "OPTIONS" or not request.path.startswith("/api/") or request.path == "/api/login":
            return
        auth_header = request.headers.get("Authorization", "")
        token = auth_header[7:] if auth_header.startswith("Bearer ") else None
        expected = app.config.get("AUTH_TOKEN")
        if not token or not hmac.compare_digest(token, expected):
            return jsonify({"error": "Unauthorized"}), 401

    @app.before_request
    def log_everything():
        if request.path == "/webhook/whatsapp":
            print(f"DEBUG ALERT: Request hitting {request.path} [{request.method}]")
            if request.method == "POST":
                print(f"DEBUG BODY: {request.get_data(as_text=True)}")

    # ✅ BYPASS NGROK INTERIM PAGE (Global)
    @app.after_request
    def add_ngrok_skip_header(response):
        response.headers["ngrok-skip-browser-warning"] = "true"
        return response

    # ✅ PRIVACY POLICY
    @app.route("/privacy")
    def privacy():
        return "<h1>Privacy Policy</h1><p>Obsidyne Bot does not share your data.</p>"

    # ✅ EXPLICIT ROUTE FOR POSTERS
    @app.route("/static/posters/<path:filename>")
    def serve_poster(filename):
        response = make_response(send_from_directory("static/posters", filename))
        mime_type, _ = mimetypes.guess_type(filename)
        if mime_type:
            response.headers["Content-Type"] = mime_type
        return response

    # ✅ QUIZ IMAGES
    @app.route("/quiz/<path:filename>")
    def serve_quiz_image(filename):
        response = make_response(send_from_directory("quiz", filename))
        mime_type, _ = mimetypes.guess_type(filename)
        if mime_type:
            response.headers["Content-Type"] = mime_type
        return response

    @app.route("/")
    def index():
        return app.send_static_file("index.html")

    @app.errorhandler(404)
    def not_found(e):
        if request.path.startswith('/api/'):
            return jsonify(error="Not found"), 404
        return app.send_static_file("index.html")

    # ✅ CREATE TABLES
    with app.app_context():
        db.create_all()
        # Migrate existing DBs: add created_at to campaign if missing
        try:
            with db.engine.connect() as conn:
                result = conn.execute(text("PRAGMA table_info(campaign)"))
                existing_columns = [row[1] for row in result.fetchall()]
                if 'created_at' not in existing_columns:
                    conn.execute(text("ALTER TABLE campaign ADD COLUMN created_at DATETIME"))
                    conn.commit()
                    print("Migration: added created_at column to campaign table")
        except Exception as e:
            print(f"Migration error: {e}")

    # ✅ START SCHEDULER
    from services.scheduler import start_scheduler
    start_scheduler(app)

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5006, threaded=True)