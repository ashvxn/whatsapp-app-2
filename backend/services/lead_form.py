import re

from extensions import db
from models import ScholarshipApplication
from services.whatsapp import send_text
from services.tags import replace_tag, add_tag

FORM_INTRO_RE = re.compile(r"filled out your form", re.IGNORECASE)
EMAIL_RE = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")
FULL_NAME_LINE_RE = re.compile(r"^\s*full\s*name\s*:\s*(.+)$", re.IGNORECASE | re.MULTILINE)

ACK_MSG = (
    "Thanks {name}! 🎉 We've received your details and one of our team members "
    "will reach out to you shortly."
)


def is_lead_form_submission(text):
    """True for the auto-fill message WhatsApp sends when someone submits a
    Meta (Facebook/Instagram) Click-to-WhatsApp lead form, e.g.:

        Hello! I filled out your form and would like to know more about
        your business.

        Full name: Jane Doe
        Phone number: +91...
        Email: jane@example.com
        Education level: High school / GED
        Are you willing to relocate...?: Yes
    """
    if not text or not FORM_INTRO_RE.search(text):
        return False
    return bool(EMAIL_RE.search(text))


def _extract_full_name(text):
    m = FULL_NAME_LINE_RE.search(text)
    return m.group(1).strip() if m else None


def _extract_email(text):
    # Search line-by-line first so the greedy regex can't swallow the next
    # field's label (e.g. "Email: x@y.com" followed immediately by
    # "Education level:" with no separating space once newlines are stripped).
    for line in text.splitlines():
        m = EMAIL_RE.search(line)
        if m:
            return m.group(0)
    # Fallback: mobile keyboards sometimes hard-wrap a long email address
    # across a line break, splitting it in two.
    flattened = text.replace("\r", "").replace("\n", "")
    m = EMAIL_RE.search(flattened)
    return m.group(0) if m else None


def capture_lead_form(contact, text, notify=True):
    """Parse a lead-form submission message, store it against the contact's
    ScholarshipApplication row (the same record/UI already used for "Details
    Captured"), and tag the contact as a verified lead.

    Skips contacts that already have captured details, so re-processing
    (e.g. a backfill) never clobbers existing records.
    Returns True if it captured something, False if skipped.
    """
    if not contact:
        return False

    app = ScholarshipApplication.query.filter_by(contact_id=contact.id).first()
    if app and (app.details_text or app.email):
        return False

    full_name = _extract_full_name(text) or contact.name
    email = _extract_email(text)

    if app:
        app.full_name = full_name
        app.email = email
        app.phone_number = contact.phone
        app.details_text = text
        app.status = "completed"
    else:
        app = ScholarshipApplication(
            contact_id=contact.id,
            full_name=full_name,
            email=email,
            phone_number=contact.phone,
            details_text=text,
            status="completed",
        )
        db.session.add(app)
    db.session.commit()

    replace_tag(contact, ["lead"], "Verified Lead")
    add_tag(contact, "Details Captured")

    if notify:
        send_text(contact.phone, ACK_MSG.format(name=full_name or "there"))

    return True
