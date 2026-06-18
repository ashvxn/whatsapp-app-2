import os
import uuid
import re
from flask import Blueprint, request, jsonify, current_app
from datetime import datetime
from extensions import db
from models import Campaign, CampaignRecipient, Contact

campaigns_bp = Blueprint("campaigns", __name__, url_prefix="/api/campaigns")

def slugify(text):
    text = text.lower()
    return re.sub(r'[^a-z0-9.]+', '_', text).strip('_')

# List all campaigns
@campaigns_bp.route("", methods=["GET"])
def get_campaigns():
    campaigns = Campaign.query.all()
    results = []
    for c in campaigns:
        total_sent = CampaignRecipient.query.filter_by(campaign_id=c.id).count()
        total_read = CampaignRecipient.query.filter_by(campaign_id=c.id, status='read').count()
        results.append({
            "id": c.id,
            "template_name": c.template_name,
            "payload": c.payload,
            "scheduled_at": c.scheduled_at.isoformat() if c.scheduled_at else None,
            "created_at": c.created_at.isoformat() if c.created_at else None,
            "status": c.status,
            "stats": {"sent": total_sent, "read": total_read}
        })
    return jsonify(results)

# Get single campaign
@campaigns_bp.route("/<int:id>", methods=["GET"])
def get_campaign(id):
    c = Campaign.query.get_or_404(id)
    recipients = CampaignRecipient.query.filter_by(campaign_id=id).all()
    return jsonify({
        "id": c.id,
        "template_name": c.template_name,
        "payload": c.payload,
        "scheduled_at": c.scheduled_at.isoformat() if c.scheduled_at else None,
        "status": c.status,
        "recipients": [
            {
                "contact_name": r.contact.name,
                "phone": r.contact.phone,
                "status": r.status,
                "updated_at": r.updated_at.isoformat() if r.updated_at else None
            } for r in recipients
        ]
    })

# Delete a campaign
@campaigns_bp.route("/<int:id>", methods=["DELETE"])
def delete_campaign(id):
    c = Campaign.query.get_or_404(id)
    db.session.delete(c)
    db.session.commit()
    return jsonify({"message": "Campaign deleted"})

# Create a campaign
@campaigns_bp.route("", methods=["POST"])
def create_campaign():
    if request.content_type.startswith('multipart/form-data'):
        data = request.form
        image_file = request.files.get('image')
    else:
        data = request.json
        image_file = None

    if not data.get("template_name"):
        return jsonify({"error": "template_name required"}), 400

    scheduled_at = None
    if data.get("scheduled_at"):
        scheduled_at = datetime.fromisoformat(data["scheduled_at"])

    tags = data.get("tags")
    if tags and not isinstance(tags, list):
        tags = [t for t in str(tags).split(",") if t.strip()]

    payload = {
        "tag": data.get("tag"),
        "tags": tags,
        "message": data.get("message"),
        "image_url": data.get("image_url")
    }

    if image_file:
        safe_filename = slugify(image_file.filename)
        filename = f"{uuid.uuid4().hex}_{safe_filename}"
        filepath = os.path.join("static/posters", filename)
        image_file.save(filepath)
        public_base = current_app.config.get("PUBLIC_URL", request.host_url).rstrip("/")
        public_url = f"{public_base}/static/posters/{filename}"
        payload["image_url"] = public_url

    campaign = Campaign(
        template_name=data["template_name"],
        payload=payload,
        scheduled_at=scheduled_at,
        status="scheduled"
    )

    db.session.add(campaign)
    db.session.commit()

    return jsonify({"message": "Campaign created"}), 201