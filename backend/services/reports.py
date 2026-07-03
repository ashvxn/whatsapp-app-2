import io
import os

from sqlalchemy import or_
from fpdf import FPDF

from models import Contact, ScholarshipApplication


def _safe_text(value):
    if value is None or value == "":
        return "-"
    text = str(value)
    return text.encode("latin-1", "replace").decode("latin-1")


def _line(pdf, text, **kwargs):
    # multi_cell defaults to new_x=RIGHT in this fpdf2 version, which never resets
    # the cursor to the left margin - explicitly reset on every call to avoid it
    # drifting off the page after a few lines.
    pdf.multi_cell(0, 8, text, new_x="LMARGIN", new_y="NEXT", **kwargs)


def _add_contact_page(pdf, contact, app):
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 16)
    _line(pdf, _safe_text(app.full_name or contact.name or "Unknown"))
    pdf.ln(2)

    fields = [
        ("WhatsApp Number", contact.phone),
        ("Full Name", app.full_name),
        ("Contact Phone Number", app.phone_number),
        ("Email", app.email),
        ("Location", app.location),
        ("Age", app.age),
        ("Tags", contact.tags),
        ("Application Status", app.status),
        ("Last Updated", app.updated_at.strftime("%d %b %Y, %I:%M %p") if app.updated_at else "-"),
    ]
    pdf.set_font("Helvetica", "", 11)
    for label, value in fields:
        _line(pdf, f"**{label}:** {_safe_text(value)}", markdown=True)

    pdf.ln(4)
    _line(pdf, "**ID Proof:**", markdown=True)

    if app.id_proof_path and os.path.exists(app.id_proof_path):
        try:
            pdf.image(app.id_proof_path, w=120)
        except Exception:
            pdf.set_font("Helvetica", "I", 10)
            _line(pdf, "(Could not render the ID proof image)")
    else:
        pdf.set_font("Helvetica", "I", 10)
        _line(pdf, "No ID proof uploaded yet.")


def generate_verified_leads_report():
    contacts = (
        Contact.query.filter(
            or_(
                Contact.tags.ilike("%verified lead%"),
                Contact.tags.ilike("%id available%"),
            )
        )
        .order_by(Contact.name)
        .all()
    )

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)

    if not contacts:
        pdf.add_page()
        pdf.set_font("Helvetica", "", 12)
        pdf.cell(0, 10, "No verified leads found.")
    else:
        for contact in contacts:
            app = ScholarshipApplication.query.filter_by(contact_id=contact.id).first()
            if not app:
                continue
            _add_contact_page(pdf, contact, app)

    buf = io.BytesIO(bytes(pdf.output()))
    buf.seek(0)
    return buf
