# Rute za transakcije - CRUD operacije
# Sve rute su zaštićene tokenom (@token_required)
# Svaki korisnik vidi i menja samo svoje transakcije

from flask import Blueprint, request, jsonify
from models import db, Transaction
from services.auth import token_required
from datetime import datetime

# Blueprint grupiše sve transaction rute pod /api/transactions prefiks
transactions_bp = Blueprint("transactions", __name__, url_prefix="/api/transactions")


@transactions_bp.get("")
@token_required
def list_transactions(current_user):
    """
    Vraća listu svih transakcija trenutnog korisnika, sortirano po datumu (najnovije prvo).
    
    Vraća: [ { id, title, type, amount, description, date, category_id, category }, ... ]
    """
    transactions = Transaction.query.filter_by(user_id=current_user.id)\
        .order_by(Transaction.date.desc()).all()
    
    return jsonify([{
        "id":          t.id,
        "title":       t.title or t.description,  # ako nema title, koristi description
        "type":        t.type,
        "amount":      float(t.amount),
        "description": t.description,
        "date":        t.date.isoformat() if t.date else None,
        "category_id": t.category_id,
        "category":    t.category.name if t.category else None,  # naziv kategorije za prikaz
    } for t in transactions])


@transactions_bp.post("")
@token_required
def create_transaction(current_user):
    """
    Kreira novu transakciju.
    
    Prima: { title, type, amount, date, category_id, description }
    Vraća: { id, title, type, amount, description, date, category_id, category }
    
    Validacija:
    - type mora biti "income" ili "expense"
    - amount mora biti pozitivan broj
    - date mora biti u formatu YYYY-MM-DD
    """
    data     = request.get_json() or {}
    tx_type  = data.get("type")
    amount   = data.get("amount")
    date_str = data.get("date")

    # Validacija tipa transakcije
    if tx_type not in ("income", "expense"):
        return jsonify({"error": "Tip mora biti 'income' ili 'expense'"}), 400
    
    # Validacija iznosa
    if not amount or float(amount) <= 0:
        return jsonify({"error": "Iznos mora biti pozitivan"}), 400

    # Konvertovanje string datuma u Python date objekat
    try:
        date = datetime.strptime(date_str, "%Y-%m-%d").date() if date_str else datetime.utcnow().date()
    except ValueError:
        return jsonify({"error": "Format datuma mora biti YYYY-MM-DD"}), 400

    transaction = Transaction(
        user_id=current_user.id,
        title=data.get("title", ""),
        type=tx_type,
        amount=float(amount),
        description=data.get("description", ""),
        # Prihvatamo i category_id i categoryId (zbog razlike između backenda i frontenda)
        category_id=data.get("category_id") or (data.get("categoryId") if data.get("categoryId") else None),
        date=date,
    )
    db.session.add(transaction)
    db.session.commit()

    return jsonify({
        "id":          transaction.id,
        "title":       transaction.title,
        "type":        transaction.type,
        "amount":      float(transaction.amount),
        "description": transaction.description,
        "date":        transaction.date.isoformat(),
        "category_id": transaction.category_id,
        "category":    transaction.category.name if transaction.category else None,
    }), 201


@transactions_bp.put("/<int:tx_id>")
@token_required
def update_transaction(current_user, tx_id):
    """
    Ažurira postojeću transakciju.
    Sva polja su opciona - ažuriraju se samo ona koja su prosleđena.
    
    Prima: { title?, type?, amount?, date?, category_id?, description? }
    Vraća: { id, title, type, amount, description, date, category_id, category }
    """
    transaction = Transaction.query.filter_by(id=tx_id, user_id=current_user.id).first_or_404()
    data = request.get_json() or {}

    # Ažuriramo samo polja koja su prosleđena
    if "title" in data:
        transaction.title = data["title"]
    if "type" in data and data["type"] in ("income", "expense"):
        transaction.type = data["type"]
    if "amount" in data:
        transaction.amount = float(data["amount"])
    if "description" in data:
        transaction.description = data["description"]
    # Prihvatamo i category_id i categoryId
    if "category_id" in data or "categoryId" in data:
        transaction.category_id = data.get("category_id") or data.get("categoryId")
    if "date" in data:
        try:
            transaction.date = datetime.strptime(data["date"], "%Y-%m-%d").date()
        except ValueError:
            return jsonify({"error": "Format datuma mora biti YYYY-MM-DD"}), 400

    db.session.commit()
    return jsonify({
        "id":          transaction.id,
        "title":       transaction.title,
        "type":        transaction.type,
        "amount":      float(transaction.amount),
        "description": transaction.description,
        "date":        transaction.date.isoformat(),
        "category_id": transaction.category_id,
        "category":    transaction.category.name if transaction.category else None,
    })


@transactions_bp.delete("/<int:tx_id>")
@token_required
def delete_transaction(current_user, tx_id):
    """
    Briše transakciju.
    filter_by sa user_id osigurava da korisnik može brisati samo svoje transakcije.
    """
    transaction = Transaction.query.filter_by(id=tx_id, user_id=current_user.id).first_or_404()
    db.session.delete(transaction)
    db.session.commit()
    return jsonify({"message": "Transakcija obrisana"})