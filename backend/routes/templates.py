from flask import Blueprint, jsonify

templates_bp = Blueprint("templates", __name__, url_prefix="/api/templates")

# List of templates (Now matching the Meta ones)
TEMPLATES = [
    {
        "name": "first",
        "type": "image",
        "label": "Poster + Text Blast (Kochi)"
    },
    {
        "name": "second",
        "type": "image",
        "label": "Poster + Text Blast (Palakkad)"
    },
    {
        "name": "third",
        "type": "image",
        "label": "Kochi Descriptive",
        "variables": ["Paragraph 1", "Paragraph 2", "Point 1", "Point 2", "Point 3", "Point 4", "Point 5", "Paragraph 3"]
    },
    {
        "name": "fourth",
        "type": "image",
        "label": "Palakkad Descriptive",
        "variables": ["Paragraph 1", "Paragraph 2", "Point 1", "Point 2", "Point 3", "Point 4", "Point 5", "Paragraph 3"]
    }
]

@templates_bp.route("", methods=["GET"])
def list_templates():
    return jsonify(TEMPLATES)