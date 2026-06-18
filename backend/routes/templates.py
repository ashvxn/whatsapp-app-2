from flask import Blueprint, jsonify

templates_bp = Blueprint("templates", __name__, url_prefix="/api/templates")

# List of templates (Now matching the Meta ones)
TEMPLATES = [
    {
        "name": "first",
        "type": "image",
        "label": "Poster + Text Blast"
    }
]

@templates_bp.route("", methods=["GET"])
def list_templates():
    return jsonify(TEMPLATES)