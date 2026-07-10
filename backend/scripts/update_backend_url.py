"""
One-off maintenance script: rewrites the old backend/PUBLIC_URL prefix stored
in Campaign.payload["image_url"] (and any other string field inside the JSON
payload) to the new backend URL, so campaign image previews resolve again
after the server's public URL (e.g. the Cloudflare tunnel) changes.

Usage (run from the backend/ directory, on the server):
    python scripts/update_backend_url.py <old_url> <new_url> [--yes]

Example:
    python scripts/update_backend_url.py \
        https://laden-coastal-finder-videos.trycloudflare.com \
        https://new-tunnel-name.trycloudflare.com

Notes:
- Trailing slashes are ignored/normalized.
- Without --yes, the script only prints what it WOULD change (dry run).
- Also update PUBLIC_URL in backend/.env to the new URL so newly created
  campaigns use the correct base going forward — this script only fixes
  already-stored rows.
"""
import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from extensions import db
from models import Campaign


def rewrite(value, old_url, new_url):
    """Recursively replace old_url prefix with new_url inside strings/dicts/lists."""
    if isinstance(value, str):
        if value.startswith(old_url):
            return new_url + value[len(old_url):]
        return value
    if isinstance(value, dict):
        return {k: rewrite(v, old_url, new_url) for k, v in value.items()}
    if isinstance(value, list):
        return [rewrite(v, old_url, new_url) for v in value]
    return value


def main():
    args = [a for a in sys.argv[1:] if a != "--yes"]
    apply_changes = "--yes" in sys.argv

    if len(args) != 2:
        print(__doc__)
        sys.exit(1)

    old_url = args[0].rstrip("/")
    new_url = args[1].rstrip("/")

    app = create_app()
    with app.app_context():
        campaigns = Campaign.query.all()
        changed = 0

        for c in campaigns:
            if not c.payload:
                continue
            new_payload = rewrite(c.payload, old_url, new_url)
            if new_payload != c.payload:
                changed += 1
                print(f"Campaign {c.id} ({c.template_name}):")
                print(f"  old: {json.dumps(c.payload)}")
                print(f"  new: {json.dumps(new_payload)}")
                if apply_changes:
                    c.payload = new_payload

        if not changed:
            print("No campaigns reference the old URL. Nothing to do.")
            return

        if apply_changes:
            db.session.commit()
            print(f"\nUpdated {changed} campaign(s).")
        else:
            print(f"\nDry run: {changed} campaign(s) would be updated.")
            print("Re-run with --yes to apply the changes.")


if __name__ == "__main__":
    main()
