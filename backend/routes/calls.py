from flask import Blueprint, jsonify, request
from extensions import db
from models import CallRequest

calls_bp = Blueprint("calls", __name__, url_prefix="/api/calls")


@calls_bp.route("", methods=["GET"])
def get_calls():
    status_filter = request.args.get("status")
    query = CallRequest.query.order_by(CallRequest.created_at.desc())
    if status_filter:
        query = query.filter_by(status=status_filter)
    calls = query.all()
    return jsonify([
        {
            "id": c.id,
            "phone": c.phone,
            "caller_name": c.caller_name,
            "preferred_time": c.preferred_time,
            "notes": c.notes,
            "status": c.status,
            "created_at": c.created_at.isoformat() if c.created_at else None
        }
        for c in calls
    ])


@calls_bp.route("/<int:id>", methods=["PUT"])
def update_call(id):
    call = CallRequest.query.get_or_404(id)
    data = request.json
    if "status" in data:
        call.status = data["status"]
    if "notes" in data:
        call.notes = data["notes"]
    db.session.commit()
    return jsonify({"message": "Updated"})


@calls_bp.route("/<int:id>", methods=["DELETE"])
def delete_call(id):
    call = CallRequest.query.get_or_404(id)
    db.session.delete(call)
    db.session.commit()
    return jsonify({"message": "Deleted"})
