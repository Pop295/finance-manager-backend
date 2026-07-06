# Rute za kategorije - CRUD operacije
# Sve rute su zaštićene tokenom (@token_required)
# Svaki korisnik vidi i menja samo svoje kategorije

from flask import Blueprint, request, jsonify
from models import db, Category, Transaction
from services.auth import token_required

# Blueprint grupiše sve category rute pod /api/categories prefiks
categories_bp = Blueprint("categories", __name__, url_prefix="/api/categories")


@categories_bp.get("")
@token_required
def list_categories(current_user):
    """
    Vraća listu svih kategorija trenutnog korisnika.
    
    Vraća: [ { id, name, color, icon }, ... ]
    """
    cats = Category.query.filter_by(user_id=current_user.id).all()
    return jsonify([{
        "id":    c.id,
        "name":  c.name,
        "color": c.color,
        "icon":  c.icon
    } for c in cats])


@categories_bp.post("")
@token_required
def create_category(current_user):
    """
    Kreira novu kategoriju za trenutnog korisnika.
    
    Prima: { name, color, icon }
    Vraća: { id, name, color, icon }
    """
    data = request.get_json() or {}
    name = data.get("name", "").strip()

    # Naziv kategorije je obavezan
    if not name:
        return jsonify({"error": "Naziv kategorije je obavezan"}), 400

    cat = Category(
        user_id=current_user.id,
        name=name,
        color=data.get("color", "#6366f1"),  # default boja ako nije prosleđena
        icon=data.get("icon", "tag")          # default ikona ako nije prosleđena
    )
    db.session.add(cat)
    db.session.commit()

    return jsonify({
        "id":    cat.id,
        "name":  cat.name,
        "color": cat.color,
        "icon":  cat.icon
    }), 201


@categories_bp.put("/<int:cat_id>")
@token_required
def update_category(current_user, cat_id):
    """
    Ažurira postojeću kategoriju.
    filter_by sa user_id osigurava da korisnik može menjati samo svoje kategorije.
    first_or_404 automatski vraća 404 ako kategorija ne postoji.
    
    Prima: { name?, color?, icon? } - sva polja su opciona
    Vraća: { id, name, color, icon }
    """
    cat = Category.query.filter_by(id=cat_id, user_id=current_user.id).first_or_404()
    data = request.get_json() or {}

    # Ažuriramo samo polja koja su prosleđena
    if "name" in data:
        cat.name = data["name"].strip()
    if "color" in data:
        cat.color = data["color"]
    if "icon" in data:
        cat.icon = data["icon"]

    db.session.commit()
    return jsonify({
        "id":    cat.id,
        "name":  cat.name,
        "color": cat.color,
        "icon":  cat.icon
    })


@categories_bp.delete("/<int:cat_id>")
@token_required
def delete_category(current_user, cat_id):
    """
    Briše kategoriju i rešava Foreign Key probleme pre brisanja:
    1. Briše sve budžete vezane za tu kategoriju
    2. Transakcijama te kategorije postavlja category_id na NULL
       (transakcije ostaju, samo gube kategoriju)
    3. Briše samu kategoriju
    """
    cat = Category.query.filter_by(id=cat_id, user_id=current_user.id).first_or_404()

    # Brišemo vezane budžete da ne bi došlo do Foreign Key greške
    from models import Budget
    Budget.query.filter_by(category_id=cat_id).delete()

    # Transakcijama postavljamo category_id na NULL umesto da ih brišemo
    Transaction.query.filter_by(category_id=cat_id).update({"category_id": None})

    db.session.delete(cat)
    db.session.commit()
    return jsonify({"message": "Kategorija obrisana"})