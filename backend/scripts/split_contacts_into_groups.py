"""
One-off maintenance script: splits all contacts carrying a given tag into
sequential groups of N (group-1, group-2, ...), added as an extra tag
alongside the existing one. Contacts are grouped in id order (i.e. the order
they were originally created), so re-running is stable/idempotent.

Usage (run from the backend/ directory, on the server):
    python3 scripts/split_contacts_into_groups.py --tag "potential leads" --size 100
    python3 scripts/split_contacts_into_groups.py --tag "potential leads" --size 100 --yes

Without --yes, this only prints what it WOULD do (dry run). Passing --yes
first makes a timestamped copy of the sqlite file before tagging anything.
Contacts that already have a group-N tag from a previous run are left as-is
(not re-grouped, not duplicated).
"""
import sys
import os
import shutil
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from extensions import db
from models import Contact
from services.tags import get_tags, add_tag


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
    backup_path = f"{db_path}.bak_pre_group_split_{stamp}"
    shutil.copy2(db_path, backup_path)
    print(f"Backed up database to {backup_path}")


def main():
    apply_changes = "--yes" in sys.argv

    tag = None
    if "--tag" in sys.argv:
        tag = sys.argv[sys.argv.index("--tag") + 1]
    if not tag:
        print('Usage: python3 split_contacts_into_groups.py --tag "potential leads" --size 100 [--yes]')
        return

    size = 100
    if "--size" in sys.argv:
        size = int(sys.argv[sys.argv.index("--size") + 1])

    app = create_app()
    with app.app_context():
        contacts = Contact.query.order_by(Contact.id.asc()).all()
        matched = [c for c in contacts if tag.lower() in get_tags(c)]

        already_grouped = [c for c in matched if any(t.startswith("group-") for t in get_tags(c))]
        to_group = [c for c in matched if c not in already_grouped]

        num_groups = (len(to_group) + size - 1) // size if to_group else 0

        print(f"Tag: {tag!r}")
        print(f"  matching contacts: {len(matched)}")
        print(f"  already have a group-N tag (left untouched): {len(already_grouped)}")
        print(f"  to be grouped now: {len(to_group)}")
        print(f"  group size: {size} -> {num_groups} group(s)")

        assignments = []  # (contact, group_tag)
        for i, c in enumerate(to_group):
            group_num = (i // size) + 1
            assignments.append((c, f"group-{group_num}"))

        for group_num in range(1, num_groups + 1):
            count = sum(1 for _, g in assignments if g == f"group-{group_num}")
            print(f"    group-{group_num}: {count} contacts")

        if not apply_changes:
            print("\nDry run: no changes made. Re-run with --yes to apply.")
            return

        backup_sqlite_db(app)

        for c, group_tag in assignments:
            add_tag(c, group_tag)

        print(f"\nDone. Tagged {len(assignments)} contacts across {num_groups} group(s).")


if __name__ == "__main__":
    main()
