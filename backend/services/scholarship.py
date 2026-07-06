import os
import re
import uuid
import mimetypes

from extensions import db
from models import ScholarshipApplication
from services.whatsapp import send_text, send_interactive_buttons, download_media
from services.tags import replace_tag, add_tag

AGE_MIN = 1
AGE_MAX = 100

TERMS_MSG = (
    "📋 *Terms & Conditions – AMD Free Hostel Campaign*\n\n"
    "Thank you for your interest in the AMD Free Hostel Campaign! Please read the following terms carefully:\n\n"
    "1. This offer is valid only for students aged 17–24 years.\n"
    "2. Applicants must reside more than 30 km from our AMD campus Kochi (Kaloor).\n"
    "3. The FREE hostel facility is available only to the first 50 eligible students who complete registration and fulfill all admission requirements.\n"
    "4. Eligibility will be verified based on the address and documents submitted during the admission process.\n"
    "5. Registration alone does not guarantee the offer. Admission confirmation and document verification are mandatory.\n"
    "6. The eligibility cannot be transferred to another person.\n"
    "7. This offer is applicable only for selected courses and intakes announced by AMD.\n"
    "8. Students must complete the admission process within the timeline provided by the admissions team. Failure to do so may result in forfeiture of the offer.\n"
    "9. AMD reserves the right to modify, withdraw, or discontinue the campaign at any time without prior notice.\n"
    "10. The decision of AMD regarding eligibility and allotment of the free hostel facility will be final."
)

TERMS_BUTTONS = [
    {"id": "scholarship_accept", "title": "Accept"},
]

DETAILS_PROMPT = (
    "Thank you for your interest! 😊\n\n"
    "Please send us the following details to continue:\n\n"
    "• Full Name\n"
    "• Age\n"
    "• Email ID\n"
    "• Location\n\n"
    "(Please send each detail on a separate line, in the order listed above.)\n\n"
    "Once we receive your details, we'll guide you to the next step. Thank you!"
)

PROMPTS = {
    "awaiting_id_proof": (
        "✅ Thanks, your details have been recorded!\n\n"
        "Now please upload a *Government-Issued ID Proof* that clearly displays:\n"
        "• Full Name\n"
        "• Date of Birth (DOB)\n"
        "• Residential Address\n\n"
        "(e.g. Aadhaar Card, Passport, Voter ID)"
    ),
}

CANCEL_MSG = "Application cancelled. Type *hostel scholarship* anytime to start again."
ALREADY_APPLIED_MSG = (
    "🎓 You've already completed your *Free Hostel Campaign* application.\n\n"
    "If you need to update anything, please contact our admissions team: "
    "+91 96560 99333"
)
COMPLETE_MSG = (
    "🎉 Thank you for submitting your ID proof!\n\n"
    "Your document has been received successfully and is now under verification by our admissions team.\n\n"
    "📧 Please keep an eye on your email inbox (and Spam/Junk folder), as all further communication regarding your verification status, eligibility, and the AMD Free Hostel campaign will be sent via email\n\n"
    "If your application is approved, we'll contact you with the next steps as soon as possible.\n\n"
    "Thank you for choosing AMD. We wish you the very best, and we look forward to welcoming you!"
)

EMAIL_RE = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")

DETAILS_ERROR_MSG = (
    "Hmm, I couldn't find a valid *Email ID* in your message 🤔\n\n"
    "Please resend all your details (Full Name, Age, Email ID, Location), "
    "making sure to include a valid email address."
)


def _extract_email(text):
    # Mobile keyboards sometimes hard-wrap a long email address across a line
    # break; collapse newlines before searching so the address still matches.
    flattened = text.replace("\r", "").replace("\n", "")
    m = EMAIL_RE.search(flattened)
    return m.group(0) if m else None


def _parse_lines(text):
    """Best-effort split into individual fields when the reply follows the
    requested one-per-line order. Falls back to leaving fields blank."""
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    if len(lines) != 4:
        return {}
    full_name, age_raw, _email, location = lines
    parsed = {"full_name": full_name, "location": location}
    if age_raw.isdigit() and AGE_MIN <= int(age_raw) <= AGE_MAX:
        parsed["age"] = int(age_raw)
    return parsed


def get_scholarship_state(contact):
    if not contact:
        return None
    app = ScholarshipApplication.query.filter_by(contact_id=contact.id).first()
    if app and app.status != "completed":
        return app.status
    return None


def send_scholarship_terms(phone, contact):
    if not contact:
        return
    app = ScholarshipApplication.query.filter_by(contact_id=contact.id).first()
    if app and app.status == "completed":
        send_text(phone, ALREADY_APPLIED_MSG)
        return
    send_text(phone, TERMS_MSG)
    send_interactive_buttons(phone, "Do you accept these terms and conditions?", TERMS_BUTTONS)


def start_scholarship(phone, contact):
    if not contact:
        return
    app = ScholarshipApplication.query.filter_by(contact_id=contact.id).first()
    if app and app.status == "completed":
        send_text(phone, ALREADY_APPLIED_MSG)
        return
    if app:
        app.status = "awaiting_details"
        app.full_name = None
        app.phone_number = None
        app.email = None
        app.location = None
        app.age = None
        app.details_text = None
    else:
        app = ScholarshipApplication(contact_id=contact.id, status="awaiting_details")
        db.session.add(app)
    db.session.commit()
    send_text(phone, DETAILS_PROMPT)


def _cancel(phone, app):
    db.session.delete(app)
    db.session.commit()
    send_text(phone, CANCEL_MSG)


def _handle_id_proof_step(phone, contact, app, user_text, image_id):
    if image_id is None:
        if user_text.strip().lower() == "cancel":
            _cancel(phone, app)
            return
        send_text(phone, "Please send a *photo* of your ID proof (or type *cancel* to stop).")
        return

    try:
        content, mime_type = download_media(image_id)
    except Exception:
        send_text(phone, "Sorry, we couldn't process that photo. Please try sending it again.")
        return

    ext = mimetypes.guess_extension(mime_type or "") or ".jpg"
    folder = os.path.join("static", "id_proofs", str(contact.id))
    os.makedirs(folder, exist_ok=True)
    filepath = os.path.join(folder, f"{uuid.uuid4().hex}{ext}")
    with open(filepath, "wb") as f:
        f.write(content)

    app.id_proof_path = filepath.replace("\\", "/")
    app.id_proof_media_id = image_id
    app.status = "completed"
    db.session.commit()

    add_tag(contact, "Id Available")
    send_text(phone, COMPLETE_MSG)


def _handle_details_step(phone, contact, app, user_text):
    text = (user_text or "").strip()
    if text.lower() == "cancel":
        _cancel(phone, app)
        return
    if not text:
        send_text(phone, "Please reply with your details to continue, or type *cancel* to stop.")
        return

    email = _extract_email(text)
    if not email:
        send_text(phone, DETAILS_ERROR_MSG)
        return

    app.details_text = text
    app.email = email
    app.phone_number = contact.phone
    for field, value in _parse_lines(text).items():
        setattr(app, field, value)

    app.status = "awaiting_id_proof"
    db.session.commit()

    replace_tag(contact, ["lead"], "Verified Lead")
    add_tag(contact, "Details Captured")

    send_text(phone, PROMPTS["awaiting_id_proof"])


def handle_scholarship_message(phone, contact, msg_type, user_text, image_id):
    app = ScholarshipApplication.query.filter_by(contact_id=contact.id).first()
    if not app or app.status == "completed":
        return

    step = app.status

    if step == "awaiting_id_proof":
        _handle_id_proof_step(phone, contact, app, user_text, image_id)
        return

    if step == "awaiting_details":
        _handle_details_step(phone, contact, app, user_text)
        return
