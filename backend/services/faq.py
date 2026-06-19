import re
from services.whatsapp import send_text, send_interactive_buttons
from models import Contact
from extensions import db

WELCOME_MSG = (
    "Welcome to *AMD* — an Adobe-accredited creative technology academy! 🎨\n\n"
    "We help students build careers in design, technology, and creativity.\n\n"
    "How can we help you today?"
)

COURSES_MSG = (
    "🔥 *Diploma in Creative Technologies with Gen AI*\n\n"
    "✅ Adobe Creative Cloud Access\n"
    "✅ Gen AI Training\n"
    "✅ Internship + Portfolio\n"
    "✅ Industry Certifications\n"
    "✅ 100% Placement Support\n\n"
    "📅 *Duration:* 1 Year\n"
    "🚀 Limited seats available!\n\n"
    "We also offer: UI/UX Design · Graphic Design · Motion Graphics · Web Development"
)

CONTACT_MSG = (
    "📞 *Contact AMD*\n\n"
    "📞 Ernakulam: +91 96560 99333\n"
    "📞 Palakkad: +91 96560 39944\n"
    "🌐 Website: amd.edu.in\n"
    "📸 Instagram: @amdcampus\n\n"
    "⏰ Mon – Sat: 9:00 AM – 6:00 PM"
)

BRANCHES_MSG = (
    "📍 *Our Branches*\n\n"
    "🏢 *Kochi:*\nhttps://maps.app.goo.gl/tcYSYki8kzZS9Deh8\n\n"
    "🏢 *Palakkad:*\nhttps://maps.app.goo.gl/iCRTUHeqRYWqjzj1A\n\n"
    "Mon – Sat: 9:00 AM – 6:00 PM"
)

ENROLL_MSG = (
    "Excellent choice! 🚀\n\n"
    "To enroll or get more details, contact our admissions team:\n\n"
    "📞 *+91 96560 99333*\n"
    "🌐 amd.edu.in\n\n"
    "We look forward to having you at AMD! 🎨"
)

NOT_INTERESTED_MSG = (
    "No worries! 😊\n\n"
    "Feel free to reach us anytime at *+91 96560 99333*.\n\n"
    "Wishing you all the best!"
)

MAIN_MENU_BUTTONS = [
    {"id": "courses", "title": "Our Courses"},
    {"id": "contact", "title": "Contact Us"},
    {"id": "branches", "title": "Our Branches"},
]

COURSE_BUTTONS = [
    {"id": "enroll", "title": "Enquire / Enroll"},
    {"id": "main_menu", "title": "Main Menu"},
]

BACK_BUTTONS = [
    {"id": "main_menu", "title": "Main Menu"},
    {"id": "courses", "title": "Our Courses"},
]

NOT_INTERESTED_KEYWORDS = [
    "not interested", "no thanks", "no thank you",
    "don't contact", "stop", "unsubscribe",
]


def _get_tags(contact):
    if not contact or not contact.tags:
        return []
    return [t.strip().lower() for t in contact.tags.split(",") if t.strip()]


def _set_tags(contact, tags_str):
    if contact:
        contact.tags = tags_str
        db.session.commit()


def _replace_tag(contact, match_tags, new_tag):
    """Swap any tag matching one of match_tags (case-insensitive) for new_tag,
    keeping every other label untouched. Adds new_tag if no match was found."""
    if not contact:
        return
    raw_tags = [t.strip() for t in (contact.tags or "").split(",") if t.strip()]
    match_set = {m.lower() for m in match_tags}
    new_tags = []
    replaced = False
    for t in raw_tags:
        if t.lower() in match_set:
            if not replaced:
                new_tags.append(new_tag)
                replaced = True
        else:
            new_tags.append(t)
    if not replaced:
        new_tags.append(new_tag)
    contact.tags = ", ".join(new_tags)
    db.session.commit()


def _check_engagement_upgrade(contact):
    tags = _get_tags(contact)
    if "lead" in tags and "course 1" in tags:
        _set_tags(contact, "interested, course")


def _is_not_interested(text):
    t = text.lower().strip()
    return any(k in t for k in NOT_INTERESTED_KEYWORDS)


def _is_interested(text):
    return bool(re.search(r"\binterested\b", text.lower()))


def handle_faq(msg, contact):
    phone = msg.get("from")
    msg_type = msg.get("type")

    btn_id = None
    user_text = ""

    if msg_type == "text":
        user_text = msg.get("text", {}).get("body", "").strip()
        if not user_text:
            return
    elif msg_type == "interactive":
        interactive = msg.get("interactive", {})
        if "button_reply" in interactive:
            btn_id = interactive["button_reply"]["id"]
        elif "list_reply" in interactive:
            btn_id = interactive["list_reply"]["id"]
        else:
            return
    elif msg_type == "button":
        # Quick-reply button tap on a template (campaign) message
        btn_text = msg.get("button", {}).get("text", "").strip().lower()
        if btn_text == "not interested":
            _replace_tag(contact, ["lead"], "Rejected Lead")
            contact.opted_in = False
            db.session.commit()
            send_text(phone, NOT_INTERESTED_MSG)
        elif btn_text == "interested":
            _replace_tag(contact, ["lead"], "Interested Lead")
            send_text(phone, ENROLL_MSG)
        return
    else:
        return

    # Upgrade tag if contact has "lead + course 1" (they engaged)
    _check_engagement_upgrade(contact)

    # Detect "not interested" from free text
    if btn_id is None and _is_not_interested(user_text):
        _set_tags(contact, "not_interested")
        contact.opted_in = False
        db.session.commit()
        send_text(phone, NOT_INTERESTED_MSG)
        return

    # Detect "interested" from free text
    if btn_id is None and _is_interested(user_text):
        send_text(phone, ENROLL_MSG)
        return

    # Button routing
    if btn_id == "courses":
        send_interactive_buttons(phone, COURSES_MSG, COURSE_BUTTONS)
    elif btn_id == "enroll":
        send_text(phone, ENROLL_MSG)
    elif btn_id == "contact":
        send_interactive_buttons(phone, CONTACT_MSG, BACK_BUTTONS)
    elif btn_id == "branches":
        send_interactive_buttons(phone, BRANCHES_MSG, BACK_BUTTONS)
    elif btn_id == "main_menu":
        send_interactive_buttons(phone, "Here's what we can help you with:", MAIN_MENU_BUTTONS)
    else:
        # First message or unrecognized text → show main menu
        send_interactive_buttons(phone, WELCOME_MSG, MAIN_MENU_BUTTONS)
