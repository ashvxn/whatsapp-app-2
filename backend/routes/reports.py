from datetime import datetime

from flask import Blueprint, send_file

from services.reports import generate_verified_leads_report

reports_bp = Blueprint("reports", __name__, url_prefix="/api/reports")


@reports_bp.route("/verified-leads", methods=["GET"])
def verified_leads_report():
    buf = generate_verified_leads_report()
    filename = f"verified_leads_report_{datetime.utcnow().strftime('%Y-%m-%d')}.pdf"
    return send_file(buf, mimetype="application/pdf", as_attachment=True, download_name=filename)
