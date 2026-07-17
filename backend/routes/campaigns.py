import os
import uuid
import re
import json
from flask import Blueprint, request, jsonify, current_app
from datetime import datetime
from extensions import db
from models import Campaign, CampaignRecipient, Contact
from services.tags import filter_contacts_by_tags, is_hidden
from services.scheduler import send_batch

campaigns_bp = Blueprint("campaigns", __name__, url_prefix="/api/campaigns")

def slugify(text):
    text = text.lower()
    return re.sub(r'[^a-z0-9.]+', '_', text).strip('_')

POSTERS_DIR = "static/posters"

# List previously uploaded poster images (for the gallery / image picker)
@campaigns_bp.route("/posters", methods=["GET"])
def list_posters():
    public_base = current_app.config["PUBLIC_URL"]
    items = []
    if os.path.isdir(POSTERS_DIR):
        for filename in os.listdir(POSTERS_DIR):
            filepath = os.path.join(POSTERS_DIR, filename)
            if os.path.isfile(filepath):
                items.append({
                    "filename": filename,
                    "url": f"{public_base}/static/posters/{filename}",
                    "uploaded_at": datetime.utcfromtimestamp(os.path.getmtime(filepath)).isoformat()
                })
    items.sort(key=lambda x: x["uploaded_at"], reverse=True)
    return jsonify(items)

# Preview how many opted-in contacts a set of tags would target
@campaigns_bp.route("/audience-count", methods=["GET"])
def audience_count():
    tags_param = request.args.get("tags", "")
    match_type = request.args.get("match_type", "any")
    tags = [t for t in tags_param.split(",") if t.strip()]

    contacts = Contact.query.filter_by(opted_in=True).all()
    contacts = [c for c in contacts if not is_hidden(c)]
    matched = filter_contacts_by_tags(contacts, tags, match_type)
    return jsonify({"count": len(matched)})

# List all campaigns
@campaigns_bp.route("", methods=["GET"])
def get_campaigns():
    campaigns = Campaign.query.all()
    results = []
    for c in campaigns:
        total_sent = CampaignRecipient.query.filter(
            CampaignRecipient.campaign_id == c.id, CampaignRecipient.status != 'failed'
        ).count()
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

# Retry sending to this campaign's failed recipients
@campaigns_bp.route("/<int:id>/retry", methods=["POST"])
def retry_campaign(id):
    campaign = Campaign.query.get_or_404(id)
    failed_recipients = CampaignRecipient.query.filter_by(campaign_id=id, status="failed").all()

    if not failed_recipients:
        return jsonify({"message": "No failed recipients to retry"}), 400

    contacts = [r.contact for r in failed_recipients]

    sent_count, failed_count, retry_cost = send_batch(current_app._get_current_object(), campaign, contacts)

    for r in failed_recipients:
        db.session.delete(r)

    campaign.total_estimated_cost = (campaign.total_estimated_cost or 0.0) + retry_cost
    still_failed = CampaignRecipient.query.filter_by(campaign_id=id, status="failed").count()
    campaign.status = "completed" if still_failed == 0 else "partial"
    db.session.commit()

    return jsonify({
        "retried": len(contacts),
        "sent": sent_count,
        "failed": failed_count
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

    variables = data.get("variables")
    if variables and not isinstance(variables, list):
        try:
            variables = json.loads(variables)
        except (TypeError, ValueError):
            variables = None

    match_type = data.get("match_type", "any")
    if match_type not in ("any", "exact"):
        match_type = "any"

    payload = {
        "tag": data.get("tag"),
        "tags": tags,
        "match_type": match_type,
        "message": data.get("message"),
        "image_url": data.get("image_url"),
        "variables": variables
    }

    if image_file:
        safe_filename = slugify(image_file.filename)
        filename = f"{uuid.uuid4().hex}_{safe_filename}"
        filepath = os.path.join("static/posters", filename)
        image_file.save(filepath)
        public_base = current_app.config["PUBLIC_URL"]
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