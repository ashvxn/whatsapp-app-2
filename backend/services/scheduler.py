from email.mime import message
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from extensions import db
from models import Campaign, Contact, CampaignRecipient
from services.whatsapp import send_template, send_text, send_image
from services.pricing import get_conversation_cost

def _contact_has_all_tags(contact, required_tags_normalized):
    contact_tags = {t.strip().lower() for t in (contact.tags or "").split(",") if t.strip()}
    return all(rt in contact_tags for rt in required_tags_normalized)


def extract_message_id(response):
    try:
        data = response.json()
        if "messages" in data and len(data["messages"]) > 0:
            return data["messages"][0]["id"]
    except Exception:
        pass
    return None

def process_campaigns(app):
    with app.app_context():
        while True:
            try:
                now = datetime.utcnow()
                campaigns = Campaign.query.filter(
                    Campaign.status == "scheduled",
                    (Campaign.scheduled_at.is_(None)) | (Campaign.scheduled_at <= now)
                ).all()

                for campaign in campaigns:
                    campaign.status = "processing"
                    db.session.commit()
                    
                    try:
                        tags = campaign.payload.get("tags") or (
                            [campaign.payload.get("tag")] if campaign.payload.get("tag") else []
                        )
                        message = campaign.payload.get("message")
                        image_url = campaign.payload.get("image_url")

                        required_tags_normalized = [t.strip().lower() for t in tags if t and t.strip()]

                        contacts = Contact.query.filter_by(opted_in=True).all()
                        if required_tags_normalized:
                            contacts = [c for c in contacts if _contact_has_all_tags(c, required_tags_normalized)]
                        total_campaign_cost = 0.0
                        sent_count = 0
                        failed_count = 0
                        is_custom = campaign.template_name.startswith("CUSTOM_")
                        category = "service" if is_custom else "marketing"
                        template_name = campaign.template_name

                        def send_to_contact(contact):
                            with app.app_context():
                                cost = get_conversation_cost(contact.phone, category)
                                if template_name == "CUSTOM_TEXT":
                                    response = send_text(contact.phone, message)
                                elif template_name == "CUSTOM_IMAGE":
                                    response = send_image(contact.phone, image_url, caption=message)
                                else:
                                    response = send_template(contact.phone, template_name, image_url, message)
                                msg_id = extract_message_id(response)
                                return contact.id, msg_id, cost

                        with ThreadPoolExecutor(max_workers=10) as executor:
                            futures = {executor.submit(send_to_contact, c): c for c in contacts}
                            for future in as_completed(futures):
                                try:
                                    contact_id, msg_id, cost = future.result()
                                    total_campaign_cost += cost
                                    if msg_id:
                                        sent_count += 1
                                        recipient = CampaignRecipient(
                                            campaign_id=campaign.id,
                                            contact_id=contact_id,
                                            whatsapp_msg_id=msg_id,
                                            status="sent",
                                            estimated_cost=cost
                                        )
                                        db.session.add(recipient)
                                    else:
                                        failed_count += 1
                                except Exception as e:
                                    failed_count += 1
                                    print(f"Failed to send to contact: {e}")

                        campaign.total_estimated_cost = total_campaign_cost
                        if sent_count == 0 and failed_count > 0:
                            campaign.status = "failed"
                        elif failed_count > 0:
                            campaign.status = "partial"
                        else:
                            campaign.status = "completed"
                    except Exception as e:
                        print(f"Error processing campaign {campaign.id}: {e}")
                        campaign.status = "failed"
                    
                    db.session.commit()
            except Exception as e:
                print(f"Scheduler error: {e}")
            time.sleep(10)

def start_scheduler(app):
    thread = threading.Thread(target=process_campaigns, args=(app,), daemon=True)
    thread.start()