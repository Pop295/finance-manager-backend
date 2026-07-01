from flask import Blueprint, request, jsonify
from models import db
from services.auth import token_required, hash_password, check_password

profile_bp = Blueprint("profile", __name__, url_prefix="/api/profile")


@profile_bp.get("")
@token_required
def get_profile(current_user):
    # vraca podatke o trenutnom korisniku
    return jsonify({
        "id":       current_user.id,
        "name":     current_user.name,
        "email":    current_user.email,
        "avatar":   current_user.avatar,
        "currency": current_user.currency,
    })


@profile_bp.put("")
@token_required
def update_profile(current_user):
    data = request.get_json() or {}

    if "name" in data:
        current_user.name = data["name"].strip()
    if "avatar" in data:
        current_user.avatar = data["avatar"]
    if "currency" in data:
        current_user.currency = data["currency"]

    db.session.commit()
    return jsonify({
        "id":       current_user.id,
        "name":     current_user.name,
        "email":    current_user.email,
        "avatar":   current_user.avatar,
        "currency": current_user.currency,
    })


@profile_bp.put("/password")
@token_required
def change_password(current_user):
    data         = request.get_json() or {}
    old_password = data.get("old_password", "")
    new_password = data.get("new_password", "")

    # proveravamo da li je stara lozinka ispravna
    if not check_password(old_password, current_user.password):
        return jsonify({"error": "Stara lozinka nije ispravna"}), 400

    if len(new_password) < 6:
        return jsonify({"error": "Nova lozinka mora imati najmanje 6 karaktera"}), 400

    current_user.password = hash_password(new_password)
    db.session.commit()
    return jsonify({"message": "Lozinka uspesno promenjena"})