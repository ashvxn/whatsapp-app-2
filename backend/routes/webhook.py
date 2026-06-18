from flask import Blueprint, request, current_app, g
from services.faq import handle_faq
from services.whatsapp import mark_as_read
from extensions import db
from models import CampaignRecipient, Contact

webhook = Blueprint("webhook", __name__)

@webhook.route("/webhook/whatsapp", methods=["GET"])
def verify():
    mode = request.args.get("hub.mode") or request.args.get("hub_mode")
    token = request.args.get("hub.verify_token") or request.args.get("hub_verify_token")
    challenge = request.args.get("hub.challenge") or request.args.get("hub_challenge")
    verify_token = current_app.config.get("VERIFY_TOKEN", "ashvins-bot-2026")

    if mode == "subscribe" and token == verify_token:
        return str(challenge)
    return "Verification failed", 403

@webhook.route("/webhook/whatsapp", methods=["POST"])
def receive():
    data = request.json
    try:
        entries = data.get("entry", [])
        for entry in entries:
            for change in entry.get("changes", []):
                value = change.get("value", {})
                
                # 1. CONTEXTUAL REPLIES
                metadata = value.get("metadata", {})
                receiver_phone_id = metadata.get("phone_number_id")
                g.current_phone_id = receiver_phone_id

                # 2. CAPTURE MESSAGES & CONTACTS
                messages = value.get("messages", [])
                for msg in messages:
                    sender_phone = msg.get("from")
                    profile_name = value.get("contacts", [{}])[0].get("profile", {}).get("name", "New Lead")

                    # Mark incoming message as read (blue ticks)
                    if msg.get("id"):
                        mark_as_read(msg["id"])

                    # Auto-Lead Capture
                    existing = Contact.query.filter_by(phone=sender_phone).first()
                    if not existing:
                        existing = Contact(name=profile_name, phone=sender_phone, tags="LEAD", opted_in=True)
                        db.session.add(existing)
                        db.session.commit()


                # 3. HANDLE STATUS UPDATES
                statuses = value.get("statuses", [])
                for status in statuses:
                    msg_id = status.get("id")
                    status_name = status.get("status")
                    recipient = CampaignRecipient.query.filter_by(whatsapp_msg_id=msg_id).first()
                    if recipient:
                        status_priority = {"sent": 1, "delivered": 2, "read": 3, "failed": 0}
                        if status_priority.get(status_name, 0) > status_priority.get(recipient.status, 0):
                            recipient.status = status_name
                            db.session.commit()

                # 4. TRIGGER FAQ REPLIES
                for msg in messages:
                    sender_phone = msg.get("from")
                    contact = Contact.query.filter_by(phone=sender_phone).first()
                    handle_faq(msg, contact)
                    
    except Exception as e:
        print(f"Error handling webhook: {e}")
        
    return "OK", 200