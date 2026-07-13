"""
One-off maintenance script: corrects an inflated "sent" count on a campaign.

Background: CampaignRecipient rows are created as soon as WhatsApp accepts a
message and returns a message id (status="sent"), before delivery is known.
Delivery/read confirmations arrive later via the status webhook
(routes/webhook.py) and upgrade the row to "delivered" or "read". A priority
bug in that webhook handler means "failed" status updates are silently
dropped (failed has priority 0, which can never beat "sent"'s priority 1), so
rows for messages that actually failed stay stuck at status="sent" forever
and inflate every "sent" count in the app (per-campaign and the analytics
overview), since those counts are a plain row count with no status filter.

This script trims a single campaign's CampaignRecipient rows down to only
the ones with confirmed status ("delivered" or "read"), deleting the rest.
Use it once you've confirmed the real delivered/read number (e.g. 212) is
what you want "sent" to reflect for that campaign going forward.

Usage (run from the backend/ directory, on the server):
    python3 scripts/fix_campaign_sent_count.py --list
    python3 scripts/fix_campaign_sent_count.py --campaign-id 12
    python3 scripts/fix_campaign_sent_count.py --campaign-id 12 --yes

Without --yes, this only prints what it WOULD do (dry run). Passing --yes
first makes a timestamped copy of the sqlite file (matches the
db.sqlite3.bak_* convention already used in instance/) before deleting
anything.
"""
import sys
import os
import shutil
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from extensions import db
from models import Campaign, CampaignRecipient

CONFIRMED_STATUSES = ("delivered", "read")


def backup_sqlite_db(app):
    uri = app.config["SQLALCHEMY_DATABASE_URI"]
    if not uri.startswith("sqlite:///"):
        print("Non-sqlite database in use — back it up yourself before continuing, "
              "this script only auto-backs-up sqlite files.")
        return
    db_path = uri.replace("sqlite:///", "", 1)
    if not os.path.isabs(db_path):
        db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), db_path)
    if not os.path.exists(db_path):
        print(f"Warning: expected sqlite file not found at {db_path}, skipping backup.")
        return
    stamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{db_path}.bak_pre_sent_fix_{stamp}"
    shutil.copy2(db_path, backup_path)
    print(f"Backed up database to {backup_path}")


def list_campaigns():
    campaigns = Campaign.query.order_by(Campaign.id.desc()).all()
    print(f"{'id':>4}  {'status':<12} {'created_at':<20} {'total':>6} {'confirmed':>9}  template_name")
    for c in campaigns:
        total = CampaignRecipient.query.filter_by(campaign_id=c.id).count()
        confirmed = CampaignRecipient.query.filter(
            CampaignRecipient.campaign_id == c.id,
            CampaignRecipient.status.in_(CONFIRMED_STATUSES)
        ).count()
        created = c.created_at.isoformat() if c.created_at else "?"
        print(f"{c.id:>4}  {c.status:<12} {created:<20} {total:>6} {confirmed:>9}  {c.template_name}")


def fix_campaign(campaign_id, apply_changes, app):
    campaign = Campaign.query.get(campaign_id)
    if not campaign:
        print(f"No campaign with id {campaign_id}")
        return

    recipients = CampaignRecipient.query.filter_by(campaign_id=campaign_id).all()
    by_status = {}
    for r in recipients:
        by_status[r.status] = by_status.get(r.status, 0) + 1

    to_delete = [r for r in recipients if r.status not in CONFIRMED_STATUSES]
    to_keep = [r for r in recipients if r.status in CONFIRMED_STATUSES]
    new_cost = round(sum(r.estimated_cost or 0.0 for r in to_keep), 3)

    print(f"Campaign {campaign_id} ({campaign.template_name}):")
    print(f"  current total recipient rows: {len(recipients)}")
    print(f"  breakdown by status: {by_status}")
    print(f"  confirmed (delivered/read): {len(to_keep)}")
    print(f"  rows that would be deleted (never confirmed): {len(to_delete)}")
    print(f"  total_estimated_cost: {campaign.total_estimated_cost} -> {new_cost}")

    if not apply_changes:
        print("\nDry run: no changes made. Re-run with --yes to apply.")
        return

    backup_sqlite_db(app)

    for r in to_delete:
        db.session.delete(r)
    campaign.total_estimated_cost = new_cost
    db.session.commit()

    remaining = CampaignRecipient.query.filter_by(campaign_id=campaign_id).count()
    print(f"\nDone. Deleted {len(to_delete)} unconfirmed rows. "
          f"Campaign {campaign_id} now shows {remaining} sent, cost {new_cost}.")


def main():
    apply_changes = "--yes" in sys.argv
    campaign_id = None
    if "--campaign-id" in sys.argv:
        idx = sys.argv.index("--campaign-id")
        campaign_id = int(sys.argv[idx + 1])

    app = create_app()
    with app.app_context():
        if campaign_id is None:
            list_campaigns()
            print("\nPass --campaign-id <id> to inspect/fix a specific campaign.")
            return
        fix_campaign(campaign_id, apply_changes, app)


if __name__ == "__main__":
    main()
