"""
One-off maintenance script: scans historical incoming-message history for
messages that match the Meta (Facebook/Instagram) Click-to-WhatsApp lead-form
auto-fill format ("Hello! I filled out your form...") and, for any contact
who doesn't already have captured details, extracts the info and moves them
to the same "Verified Lead" / "Details Captured" state used by the live
webhook capture (services/lead_form.py) going forward.

Contacts that already have a ScholarshipApplication with details are left
untouched, so this never overwrites existing records. No WhatsApp message is
sent to these contacts (notify=False) since the "form filled" message may be
old.

Usage (run from the backend/ directory, on the server):
    python3 scripts/backfill_lead_form_leads.py [--yes]

Without --yes, this only prints what it WOULD do (dry run).
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from extensions import db
from models import Contact, IncomingMessage
from services.lead_form import is_lead_form_submission, capture_lead_form


def main():
    apply_changes = "--yes" in sys.argv

    app = create_app()
    with app.app_context():
        matches = (
            IncomingMessage.query
            .filter(IncomingMessage.msg_type == "text")
            .order_by(IncomingMessage.created_at.desc())
            .all()
        )

        seen_contacts = set()
        captured = 0
        skipped = 0

        for msg in matches:
            if not msg.body or not is_lead_form_submission(msg.body):
                continue
            if msg.contact_id in seen_contacts:
                continue  # only use each contact's most recent matching message
            seen_contacts.add(msg.contact_id)

            contact = Contact.query.get(msg.contact_id)
            if not contact:
                continue

            print(f"Contact {contact.id} ({contact.name}, {contact.phone}):")
            print(f"  message: {msg.body[:200]!r}")

            if apply_changes:
                did_capture = capture_lead_form(contact, msg.body, notify=False)
                if did_capture:
                    captured += 1
                    print("  -> captured, tagged Verified Lead / Details Captured")
                else:
                    skipped += 1
                    print("  -> skipped (already has captured details)")
            else:
                print("  -> would capture (dry run)")

        if apply_changes:
            print(f"\nDone. Captured {captured}, skipped {skipped} (already had details).")
        else:
            print(f"\nDry run: {len(seen_contacts)} contact(s) matched. Re-run with --yes to apply.")


if __name__ == "__main__":
    main()
