from extensions import db
from datetime import datetime

class Contact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    phone = db.Column(db.String(20), unique=True)
    opted_in = db.Column(db.Boolean, default=True)
    tags = db.Column(db.String(255))
    received_campaigns = db.relationship('CampaignRecipient', backref='contact', cascade="all, delete-orphan", lazy=True)

class Campaign(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    template_name = db.Column(db.String(100))
    payload = db.Column(db.JSON)
    scheduled_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default="scheduled")
    category = db.Column(db.String(20), default="marketing") # marketing, utility, service
    total_estimated_cost = db.Column(db.Float, default=0.0)
    recipients = db.relationship('CampaignRecipient', backref='campaign', cascade="all, delete-orphan", lazy=True)

class ConversationHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    phone = db.Column(db.String(20), index=True)
    role = db.Column(db.String(10))  # "user" or "model"
    content = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class CampaignRecipient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaign.id'), nullable=False)
    contact_id = db.Column(db.Integer, db.ForeignKey('contact.id'), nullable=False)
    whatsapp_msg_id = db.Column(db.String(100), unique=True)
    status = db.Column(db.String(20), default="sent")
    estimated_cost = db.Column(db.Float, default=0.0)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class CallRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    phone = db.Column(db.String(20), index=True)
    caller_name = db.Column(db.String(100))
    preferred_time = db.Column(db.String(200))
    notes = db.Column(db.Text)
    status = db.Column(db.String(20), default="pending")  # pending, confirmed, done
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class ScholarshipApplication(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    contact_id = db.Column(db.Integer, db.ForeignKey('contact.id'), unique=True, nullable=False)
    full_name = db.Column(db.String(100))
    phone_number = db.Column(db.String(20))
    email = db.Column(db.String(120))
    location = db.Column(db.String(120))
    qualification = db.Column(db.String(120))
    id_proof_path = db.Column(db.String(255))
    id_proof_media_id = db.Column(db.String(100))
    status = db.Column(db.String(30), default="awaiting_name")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    contact = db.relationship('Contact', backref=db.backref('scholarship_application', uselist=False, cascade="all, delete-orphan"))