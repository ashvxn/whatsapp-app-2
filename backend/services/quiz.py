from flask import current_app
from services.whatsapp import send_image, send_list_message, send_text, send_interactive_buttons
from extensions import db

QUESTIONS = [
    {
        "image_key": "1.png",
        "question": "🧩 *Question 1 of 3*\n\nLook at the image carefully...\n\n*How many triangles can you count?*",
        "options": [
            {"id": "quiz_q1_a", "title": "6 triangles"},
            {"id": "quiz_q1_b", "title": "8 triangles"},
            {"id": "quiz_q1_c", "title": "10 triangles"},
            {"id": "quiz_q1_d", "title": "12 triangles"},
        ],
        "correct": "quiz_q1_c",
        "correct_text": "10 triangles",
    },
    {
        "image_key": "2.png",
        "question": "🧩 *Question 2 of 3*\n\nLook at the image...\n\n*Which brand does this belong to?*",
        "options": [
            {"id": "quiz_q2_a", "title": "Burger King"},
            {"id": "quiz_q2_b", "title": "McDonald's"},
            {"id": "quiz_q2_c", "title": "Wendy's"},
            {"id": "quiz_q2_d", "title": "KFC"},
        ],
        "correct": "quiz_q2_b",
        "correct_text": "McDonald's",
    },
    {
        "image_key": "3.png",
        "question": "🧩 *Question 3 of 3*\n\nStudy the pattern in the image...\n\n*What is the answer?*",
        "options": [
            {"id": "quiz_q3_a", "title": "5"},
            {"id": "quiz_q3_b", "title": "6"},
            {"id": "quiz_q3_c", "title": "7"},
            {"id": "quiz_q3_d", "title": "9"},
        ],
        "correct": "quiz_q3_c",
        "correct_text": "7",
    },
]

_STATE_TAGS = ["quiz_q1", "quiz_q2", "quiz_q3"]

MAIN_MENU_BUTTONS = [
    {"id": "courses", "title": "Our Courses"},
    {"id": "contact", "title": "Contact Us"},
    {"id": "branches", "title": "Our Branches"},
]


def _tags_list(contact):
    if not contact or not contact.tags:
        return []
    return [t.strip() for t in contact.tags.split(",") if t.strip()]


def get_quiz_state(contact):
    for tag in _tags_list(contact):
        if tag in _STATE_TAGS:
            return tag
    return None


def _get_score(contact):
    for tag in _tags_list(contact):
        if tag.startswith("quiz_pts_"):
            try:
                return int(tag.split("_")[-1])
            except ValueError:
                return 0
    return 0


def _save_state(contact, state_tag, score):
    tags = [t for t in _tags_list(contact) if t not in _STATE_TAGS and not t.startswith("quiz_pts_")]
    if state_tag:
        tags.append(state_tag)
    tags.append(f"quiz_pts_{score}")
    contact.tags = ", ".join(tags)
    db.session.commit()


def _clear_state(contact):
    tags = [t for t in _tags_list(contact) if t not in _STATE_TAGS and not t.startswith("quiz_pts_")]
    contact.tags = ", ".join(tags)
    db.session.commit()


def _send_question(phone, q_index):
    q = QUESTIONS[q_index]
    public_url = current_app.config["PUBLIC_URL"]
    send_image(phone, f"{public_url}/quiz/{q['image_key']}")
    sections = [{"title": "Choose your answer", "rows": [{"id": o["id"], "title": o["title"]} for o in q["options"]]}]
    send_list_message(phone, q["question"], "Select Answer ✏️", sections)


def start_quiz(phone, contact):
    _save_state(contact, "quiz_q1", 0)
    send_text(
        phone,
        "🎯 *AMD Brain Quiz!*\n\n"
        "3 questions to test your observation skills.\n\n"
        "Take your time and choose wisely! Here comes Question 1 👇"
    )
    _send_question(phone, 0)


def handle_quiz_answer(phone, contact, btn_id):
    """Returns True if the btn_id was consumed by the quiz."""
    state = get_quiz_state(contact)
    if not state:
        return False

    state_map = {"quiz_q1": 0, "quiz_q2": 1, "quiz_q3": 2}
    q_index = state_map.get(state)
    if q_index is None:
        return False

    q = QUESTIONS[q_index]
    valid_ids = {o["id"] for o in q["options"]}
    if btn_id not in valid_ids:
        return False

    score = _get_score(contact)
    is_correct = btn_id == q["correct"]

    if is_correct:
        score += 1
        send_text(phone, f"✅ *Correct!* The answer is *{q['correct_text']}*. 🎉")
    else:
        send_text(phone, f"❌ *Not quite!* The correct answer was *{q['correct_text']}*. Keep going! 💪")

    next_index = q_index + 1
    if next_index < len(QUESTIONS):
        _save_state(contact, _STATE_TAGS[next_index], score)
        _send_question(phone, next_index)
    else:
        _clear_state(contact)
        _send_final_score(phone, score)

    return True


def _send_final_score(phone, score):
    total = len(QUESTIONS)
    if score == total:
        verdict = "🏆 *Perfect score! You're a genius!*"
    elif score == 2:
        verdict = "🥈 *Great job! Almost perfect!*"
    elif score == 1:
        verdict = "💡 *Good try! Keep sharpening those skills!*"
    else:
        verdict = "💪 *Better luck next time! Practice makes perfect!*"

    send_text(
        phone,
        f"🎊 *Quiz Complete!*\n\n"
        f"Your Final Score: *{score} / {total}*\n\n"
        f"{verdict}\n\n"
        f"━━━━━━━━━━━━━━\n"
        f"At AMD, we train students to think creatively and analytically — just like this! 🎨\n\n"
        f"Explore our Design & Technology courses:"
    )
    send_interactive_buttons(phone, "What would you like to know?", MAIN_MENU_BUTTONS)
