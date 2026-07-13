"""
One-off maintenance script: bulk-adds contacts from a plain text file (one
10-digit Indian number per line, no country code) with a generated name
(Candidate1, Candidate2, ...) and a shared tag.

Numbers already belonging to an existing contact are left untouched (not
retagged, not renamed) and are just reported as skipped.

Usage (run from the backend/ directory, on the server):
    python3 scripts/bulk_add_contacts.py --file numbers.txt --tag "potential leads"
    python3 scripts/bulk_add_contacts.py --file numbers.txt --tag "potential leads" --yes

Without --yes, this only prints what it WOULD do (dry run). Passing --yes
first makes a timestamped copy of the sqlite file before inserting anything.
"""
import sys
import os
import re
import shutil
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from extensions import db
from models import Contact

COUNTRY_CODE = "91"


def backup_sqlite_db(app):
    uri = app.config["SQLALCHEMY_DATABASE_URI"]
    if not uri.startswith("sqlite:///"):
        print("Non-sqlite database in use — back it up yourself before continuing.")
        return
    db_path = uri.replace("sqlite:///", "", 1)
    if not os.path.isabs(db_path):
        db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), db_path)
    if not os.path.exists(db_path):
        print(f"Warning: expected sqlite file not found at {db_path}, skipping backup.")
        return
    stamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{db_path}.bak_pre_bulk_add_{stamp}"
    shutil.copy2(db_path, backup_path)
    print(f"Backed up database to {backup_path}")


def normalize(raw_line):
    digits = re.sub(r"\D", "", raw_line)
    if len(digits) == 10:
        return COUNTRY_CODE + digits
    if len(digits) == 12 and digits.startswith(COUNTRY_CODE):
        return digits
    return None  # malformed


def main():
    apply_changes = "--yes" in sys.argv

    file_path = "numbers.txt"
    if "--file" in sys.argv:
        file_path = sys.argv[sys.argv.index("--file") + 1]

    tag = None
    if "--tag" in sys.argv:
        tag = sys.argv[sys.argv.index("--tag") + 1]
    if not tag:
        print("Usage: python3 bulk_add_contacts.py --file numbers.txt --tag \"potential leads\" [--yes]")
        return

    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return

    with open(file_path, "r", encoding="utf-8") as f:
        raw_lines = [line.strip() for line in f]

    blank = 0
    malformed = []
    seen_in_file = set()
    duplicates_in_file = 0
    to_create = []  # (phone, name)

    app = create_app()
    with app.app_context():
        for raw in raw_lines:
            if not raw:
                blank += 1
                continue
            phone = normalize(raw)
            if not phone:
                malformed.append(raw)
                continue
            if phone in seen_in_file:
                duplicates_in_file += 1
                continue
            seen_in_file.add(phone)
            to_create.append(phone)

        existing_phones = {
            p for (p,) in db.session.query(Contact.phone).filter(Contact.phone.in_(to_create)).all()
        }
        already_exists = [p for p in to_create if p in existing_phones]
        new_phones = [p for p in to_create if p not in existing_phones]

        print(f"File: {file_path}")
        print(f"  total lines: {len(raw_lines)}")
        print(f"  blank lines skipped: {blank}")
        print(f"  malformed lines skipped: {len(malformed)}")
        if malformed:
            print(f"    e.g. {malformed[:5]}")
        print(f"  duplicate lines within file skipped: {duplicates_in_file}")
        print(f"  already existing contacts skipped: {len(already_exists)}")
        print(f"  new contacts to create: {len(new_phones)}")
        print(f"  tag to apply: {tag!r}")
        print(f"  name pattern: Candidate1..Candidate{len(new_phones)}")

        if not apply_changes:
            print("\nDry run: no changes made. Re-run with --yes to apply.")
            return

        backup_sqlite_db(app)

        for i, phone in enumerate(new_phones, start=1):
            db.session.add(Contact(
                name=f"Candidate{i}",
                phone=phone,
                opted_in=True,
                tags=tag
            ))
        db.session.commit()

        print(f"\nDone. Created {len(new_phones)} contacts tagged {tag!r}.")


if __name__ == "__main__":
    main()
