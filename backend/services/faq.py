import re
from services.whatsapp import send_text, send_interactive_buttons
from models import Contact
from extensions import db
from services.quiz import start_quiz, handle_quiz_answer, get_quiz_state

WELCOME_MSG = (
    "Welcome to *AMD* — an Adobe-accredited creative technology academy! 🎨\n\n"
    "We help students build careers in design, technology, and creativity.\n\n"
    "💡 Tip: Type *quiz* to play a fun brain challenge!\n\n"
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

ENQUIRY_MSG = (
    "Excellent choice! 🚀\n\n"
    "To enroll or get more details, contact our admissions team:\n\n"
    "📞 Ernakulam: +91 96560 99333\n"
    "📞 Palakkad: +91 96560 39944\n"
    "🌐 amd.edu.in\n\n"
    "We look forward to having you at AMD! 🎨"
)

FAQ_MSG = (
    "📚 *Frequently Asked Questions*\n\n"
    "*1. What is AMD?*\n"
    "AMD is an Adobe-accredited academy specializing in creative technology education, helping students develop industry-relevant skills through practical training and real-world projects.\n\n"
    "*2. What courses does AMD offer?*\n"
    "• UI/UX Design\n"
    "• Graphic Design\n"
    "• Motion Graphics\n"
    "• Video Editing\n"
    "• Web Design & Development\n"
    "• Product Design\n"
    "• Creative Technology Programs\n\n"
    "*3. Is AMD Adobe Accredited?*\n"
    "Yes. AMD is an Adobe-accredited academy providing training aligned with industry standards.\n\n"
    "*4. Who can join AMD courses?*\n"
    "Plus Two graduates, degree holders, working professionals, freelancers, and anyone interested in creative technologies.\n\n"
    "*5. Do I need previous experience?*\n"
    "No. Our programs are designed for both beginners and learners with prior knowledge.\n\n"
    "*6. Will I get hands-on project experience?*\n"
    "Yes. Students work on practical assignments and real-world projects to build a strong portfolio.\n\n"
    "*7. Does AMD provide placement assistance?*\n"
    "Yes. We provide placement assistance, portfolio development, interview preparation, and career guidance.\n\n"
    "*8. Why is a portfolio important?*\n"
    "A portfolio showcases your skills to employers and is often more important than a resume in creative industries.\n\n"
    "*9. Are the courses job-oriented?*\n"
    "Yes. Our curriculum equips students with skills currently demanded by the industry.\n\n"
    "*10. Will I receive a certificate?*\n"
    "Yes. Students receive a course completion certificate upon successfully completing their training.\n\n"
    "*11. Why choose AMD?*\n"
    "✅ Adobe Accredited Academy\n"
    "✅ Industry-Focused Curriculum\n"
    "✅ Expert Faculty\n"
    "✅ Real-Time Projects\n"
    "✅ Portfolio Development\n"
    "✅ Placement Assistance\n"
    "✅ Career Guidance\n\n"
    "*12. How can I enroll?*\n"
    "Contact our admissions team through phone, WhatsApp, or visit our campus for a free career consultation."
)

TERMS_MSG = (
    "📋 *AMD Student Policy*\n\n"
    "*Admission Policy*\n"
    "• Students must provide accurate information during admission.\n"
    "• Admission is confirmed only after successful fee payment and document verification.\n"
    "• AMD reserves the right to accept or reject applications based on eligibility criteria.\n\n"
    "*Attendance Policy*\n"
    "• Students are expected to attend all scheduled classes regularly.\n"
    "• Excessive absenteeism may affect certification eligibility and placement assistance.\n\n"
    "*Code of Conduct*\n"
    "• Students must maintain respectful behavior toward faculty, staff, and fellow students.\n"
    "• Any form of harassment, discrimination, or misconduct will not be tolerated.\n\n"
    "*Academic Integrity*\n"
    "• All assignments and projects must be the student's original work.\n"
    "• Plagiarism may result in disciplinary action.\n\n"
    "*Placement Assistance Policy*\n"
    "• AMD provides placement assistance, career guidance, portfolio reviews, and interview preparation.\n"
    "• Placement assistance does not guarantee employment.\n\n"
    "*Fee Policy*\n"
    "• Course fees must be paid according to the agreed payment schedule.\n"
    "• Fees paid are non-transferable.\n\n"
    "*Certification Policy*\n"
    "• Certificates will be issued upon successful completion of all course requirements.\n\n"
    "*Privacy Policy*\n"
    "• Student information will be kept confidential and used only for academic and placement purposes.\n"
    "• AMD will not share personal information with third parties without consent.\n\n"
    "By enrolling at AMD, students acknowledge and agree to comply with all academy policies."
)

NOT_INTERESTED_MSG = (
    "No worries! 😊\n\n"
    "Feel free to reach us anytime at *+91 96560 99333*.\n\n"
    "Wishing you all the best!"
)

# Kept for template campaign button reply backwards-compatibility
ENROLL_MSG = ENQUIRY_MSG

MAIN_MENU_BUTTONS = [
    {"id": "courses", "title": "Courses"},
    {"id": "contact", "title": "Contact Us"},
]

COURSES_BUTTONS = [
    {"id": "enquiry", "title": "Enquiry"},
    {"id": "faq", "title": "FAQ"},
    {"id": "main_menu", "title": "Main Menu"},
]

ENQUIRY_BUTTONS = [
    {"id": "faq", "title": "FAQ"},
    {"id": "terms", "title": "Terms & Conditions"},
]

BACK_TO_MAIN = [
    {"id": "main_menu", "title": "Main Menu"},
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
        btn_text = msg.get("button", {}).get("text", "").strip().lower()
        if btn_text == "not interested":
            _replace_tag(contact, ["lead"], "Rejected Lead")
            contact.opted_in = False
            db.session.commit()
            send_text(phone, NOT_INTERESTED_MSG)
        elif btn_text == "interested":
            _replace_tag(contact, ["lead"], "Interested Lead")
            send_interactive_buttons(phone, ENQUIRY_MSG, ENQUIRY_BUTTONS)
        return
    else:
        return

    # --- QUIZ: handle answer if contact is mid-quiz ---
    if contact and get_quiz_state(contact):
        if btn_id:
            consumed = handle_quiz_answer(phone, contact, btn_id)
            if consumed:
                return
        else:
            send_text(phone, "👆 Please tap *Select Answer* above to choose your answer and continue the quiz!")
            return

    # --- QUIZ: keyword trigger ---
    if btn_id is None and "quiz" in user_text.lower():
        start_quiz(phone, contact)
        return

    # --- QUIZ: list reply with quiz option IDs (safety catch) ---
    if btn_id and btn_id.startswith("quiz_"):
        handle_quiz_answer(phone, contact, btn_id)
        return

    _check_engagement_upgrade(contact)

    if btn_id is None and _is_not_interested(user_text):
        _set_tags(contact, "not_interested")
        contact.opted_in = False
        db.session.commit()
        send_text(phone, NOT_INTERESTED_MSG)
        return

    if btn_id is None and _is_interested(user_text):
        send_interactive_buttons(phone, ENQUIRY_MSG, ENQUIRY_BUTTONS)
        return

    # Button routing
    if btn_id == "courses":
        send_interactive_buttons(phone, COURSES_MSG, COURSES_BUTTONS)
    elif btn_id in ("enquiry", "enroll"):
        send_interactive_buttons(phone, ENQUIRY_MSG, ENQUIRY_BUTTONS)
    elif btn_id == "faq":
        send_text(phone, FAQ_MSG)
        send_interactive_buttons(phone, "Need more help?", BACK_TO_MAIN)
    elif btn_id == "terms":
        send_text(phone, TERMS_MSG)
        send_interactive_buttons(phone, "Need more help?", BACK_TO_MAIN)
    elif btn_id == "contact":
        send_interactive_buttons(phone, CONTACT_MSG, BACK_TO_MAIN)
    elif btn_id == "main_menu":
        send_interactive_buttons(phone, "Here's what we can help you with:", MAIN_MENU_BUTTONS)
    else:
        send_interactive_buttons(phone, WELCOME_MSG, MAIN_MENU_BUTTONS)
