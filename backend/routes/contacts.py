import os
from flask import Blueprint, request, jsonify, send_file
from extensions import db
from models import Contact, ScholarshipApplication

contacts_bp = Blueprint("contacts", __name__, url_prefix="/api/contacts")

# Get all contacts
@contacts_bp.route("", methods=["GET"])
def get_contacts():
    contacts = Contact.query.all()
    return jsonify([
        {
            "id": c.id,
            "name": c.name,
            "phone": c.phone,
            "opted_in": c.opted_in,
            "tags": c.tags
        } for c in contacts
    ])

# Add a new contact
@contacts_bp.route("", methods=["POST"])
def add_contact():
    data = request.json

    if not data.get("phone"):
        return jsonify({"error": "Phone number required"}), 400

    # Ensure no duplicate phone numbers
    existing = Contact.query.filter_by(phone=data["phone"]).first()
    if existing:
        return jsonify({"error": "Phone number already exists"}), 400

    contact = Contact(
        name=data.get("name"),
        phone=data["phone"],
        opted_in=data.get("opted_in", True),
        tags=data.get("tags", "")
    )

    db.session.add(contact)
    db.session.commit()

    return jsonify({"message": "Contact added"}), 201

# Update a contact
@contacts_bp.route("/<int:id>", methods=["PUT"])
def update_contact(id):
    contact = Contact.query.get_or_404(id)
    data = request.json
    
    contact.name = data.get("name", contact.name)
    contact.phone = data.get("phone", contact.phone)
    contact.tags = data.get("tags", contact.tags)
    
    db.session.commit()
    return jsonify({"message": "Contact updated"})

# Delete a contact
@contacts_bp.route("/<int:id>", methods=["DELETE"])
def delete_contact(id):
    contact = Contact.query.get_or_404(id)
    db.session.delete(contact)
    db.session.commit()
    return jsonify({"message": "Contact deleted"})

# Get a contact's captured scholarship details
@contacts_bp.route("/<int:id>/scholarship", methods=["GET"])
def get_scholarship_details(id):
    Contact.query.get_or_404(id)
    app = ScholarshipApplication.query.filter_by(contact_id=id).first()
    if not app:
        return jsonify({"error": "No scholarship application found"}), 404
    return jsonify({
        "name": app.full_name,
        "phone_number": app.phone_number,
        "email": app.email,
        "location": app.location,
        "age": app.age,
        "details_text": app.details_text,
        "status": app.status,
        "has_id_proof": bool(app.id_proof_path)
    })

# Get a contact's uploaded ID proof photo
@contacts_bp.route("/<int:id>/id-proof", methods=["GET"])
def get_id_proof(id):
    Contact.query.get_or_404(id)
    app = ScholarshipApplication.query.filter_by(contact_id=id).first()
    if not app or not app.id_proof_path or not os.path.exists(app.id_proof_path):
        return jsonify({"error": "No ID proof found"}), 404
    return send_file(app.id_proof_path)