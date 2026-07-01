from flask import Blueprint, request, jsonify
from models import db, Category
from services.auth import token_required

categories_bp = Blueprint("categories", __name__, url_prefix="/api/categories")


@categories_bp.get("")
@token_required
def list_categories(current_user):
    # uzimamo sve kategorije trenutnog korisnika
    categories = Category.query.filter_by(user_id=current_user.id).all()
    return jsonify([{
        "id":    c.id,
        "name":  c.name,
        "color": c.color,
        "icon":  c.icon
    } for c in categories])


@categories_bp.post("")
@token_required
def create_category(current_user):
    data = request.get_json() or {}
    name = data.get("name", "").strip()

    if not name:
        return jsonify({"error": "Naziv kategorije je obavezan"}), 400

    category = Category(
        user_id=current_user.id,
        name=name,
        color=data.get("color", "#6366f1"),
        icon=data.get("icon", "tag")
    )
    db.session.add(category)
    db.session.commit()

    return jsonify({"id": category.id, "name": category.name, "color": category.color, "icon": category.icon}), 201


@categories_bp.put("/<int:cat_id>")
@token_required
def update_category(current_user, cat_id):
    # trazimo kategoriju koja pripada trenutnom korisniku
    category = Category.query.filter_by(id=cat_id, user_id=current_user.id).first_or_404()
    data = request.get_json() or {}

    if "name" in data:
        category.name = data["name"].strip()
    if "color" in data:
        category.color = data["color"]
    if "icon" in data:
        category.icon = data["icon"]

    db.session.commit()
    return jsonify({"id": category.id, "name": category.name, "color": category.color, "icon": category.icon})


@categories_bp.delete("/<int:cat_id>")
@token_required
def delete_category(current_user, cat_id):
    category = Category.query.filter_by(id=cat_id, user_id=current_user.id).first_or_404()
    db.session.delete(category)
    db.session.commit()
    return jsonify({"message": "Kategorija obrisana"})