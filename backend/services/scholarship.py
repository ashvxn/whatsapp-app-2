import os
import re
import uuid
import mimetypes

from extensions import db
from models import ScholarshipApplication
from services.whatsapp import send_text, download_media
from services.tags import replace_tag, add_tag

STEP_ORDER = [
    "awaiting_name",
    "awaiting_phone",
    "awaiting_email",
    "awaiting_location",
    "awaiting_qualification",
    "awaiting_id_proof",
]

FIELD_FOR_STEP = {
    "awaiting_name": "full_name",
    "awaiting_phone": "phone_number",
    "awaiting_email": "email",
    "awaiting_location": "location",
    "awaiting_qualification": "qualification",
}

CANCEL_HINT = "\n\n_Type *cancel* anytime to stop this application._"

PROMPTS = {
    "awaiting_name": (
        "🎓 *Hostel Scholarship Application*\n\n"
        "Let's get started! What's your *Full Name* (as per your government-issued ID)?"
        + CANCEL_HINT
    ),
    "awaiting_phone": "Thanks! What's your *contact phone number*?" + CANCEL_HINT,
    "awaiting_email": (
        "Great. What's your *Email Address*?\n"
        "Please provide an active email address, as all further communication will be sent via email."
        + CANCEL_HINT
    ),
    "awaiting_location": (
        "Got it. What's your *current location* (city/town)?" + CANCEL_HINT
    ),
    "awaiting_qualification": (
        "Almost done — what's your *highest qualification*? "
        "(e.g. Class 12, Diploma, Degree)"
        + CANCEL_HINT
    ),
    "awaiting_id_proof": (
        "✅ Thanks, your details have been recorded!\n\n"
        "Now please upload a *Government-Issued ID Proof* that clearly displays:\n"
        "• Full Name\n"
        "• Date of Birth (DOB)\n"
        "• Residential Address\n\n"
        "(e.g. Aadhaar Card, Passport, Voter ID)"
        + CANCEL_HINT
    ),
}

INVALID_MSGS = {
    "awaiting_phone": (
        "That doesn't look like a valid phone number 🤔 "
        "Please enter a valid phone number (7-15 digits)."
        + CANCEL_HINT
    ),
    "awaiting_email": (
        "That doesn't look like a valid email address 🤔 "
        "Please enter a valid email (e.g. name@example.com)."
        + CANCEL_HINT
    ),
}

CANCEL_MSG = "Application cancelled. Type *hostel scholarship* anytime to start again."
ALREADY_APPLIED_MSG = (
    "🎓 You've already completed your *Free Hostel Campaign* application.\n\n"
    "If you need to update anything, please contact our admissions team: "
    "+91 96560 99333"
)
COMPLETE_MSG = (
    "🎉 Your ID proof has been received. Your Hostel Scholarship application is now complete. "
    "Our team will get back to you soon!"
)

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PHONE_RE = re.compile(r"^\+?\d{7,15}$")


def _validate(step, text):
    if step == "awaiting_phone":
        return bool(PHONE_RE.match(text.strip()))
    if step == "awaiting_email":
        return bool(EMAIL_RE.match(text.strip()))
    return bool(text.strip())


def _next_step(step):
    idx = STEP_ORDER.index(step)
    if idx + 1 < len(STEP_ORDER):
        return STEP_ORDER[idx + 1]
    return "completed"


def get_scholarship_state(contact):
    if not contact:
        return None
    app = ScholarshipApplication.query.filter_by(contact_id=contact.id).first()
    if app and app.status != "completed":
        return app.status
    return None


def start_scholarship(phone, contact):
    if not contact:
        return
    app = ScholarshipApplication.query.filter_by(contact_id=contact.id).first()
    if app and app.status == "completed":
        send_text(phone, ALREADY_APPLIED_MSG)
        return
    if app:
        app.status = "awaiting_name"
        app.full_name = None
        app.phone_number = None
        app.email = None
        app.location = None
        app.qualification = None
    else:
        app = ScholarshipApplication(contact_id=contact.id, status="awaiting_name")
        db.session.add(app)
    db.session.commit()
    send_text(phone, PROMPTS["awaiting_name"])


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


def handle_scholarship_message(phone, contact, msg_type, user_text, image_id):
    app = ScholarshipApplication.query.filter_by(contact_id=contact.id).first()
    if not app or app.status == "completed":
        return

    step = app.status

    if step == "awaiting_id_proof":
        _handle_id_proof_step(phone, contact, app, user_text, image_id)
        return

    text = (user_text or "").strip()
    if text.lower() == "cancel":
        _cancel(phone, app)
        return
    if not text:
        send_text(phone, "Please reply with text to continue, or type *cancel* to stop.")
        return
    if not _validate(step, text):
        send_text(phone, INVALID_MSGS.get(step, "That doesn't look right, please try again."))
        return

    setattr(app, FIELD_FOR_STEP[step], text)
    next_step = _next_step(step)
    app.status = next_step
    db.session.commit()

    if next_step == "awaiting_id_proof":
        replace_tag(contact, ["lead"], "Verified Lead")
        add_tag(contact, "Details Captured")

    send_text(phone, PROMPTS[next_step])
