from flask import Blueprint, request, jsonify
from extensions import db
from models import Contact

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