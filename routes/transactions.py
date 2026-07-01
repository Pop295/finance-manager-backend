from flask import Blueprint, request, jsonify
from models import db, Transaction
from services.auth import token_required
from datetime import datetime

transactions_bp = Blueprint("transactions", __name__, url_prefix="/api/transactions")


@transactions_bp.get("")
@token_required
def list_transactions(current_user):
    # uzimamo sve transakcije trenutnog korisnika, sortirane po datumu
    transactions = Transaction.query.filter_by(user_id=current_user.id)\
        .order_by(Transaction.date.desc()).all()
    
    return jsonify([{
    "id":          t.id,
    "type":        t.type,
    "amount":      float(t.amount),
    "description": t.description,
    "title":       t.description,
    "date":        t.date.isoformat() if t.date else None,
    "category_id": t.category_id,
    "category":    t.category.name if t.category else None,
} for t in transactions])


@transactions_bp.post("")
@token_required
def create_transaction(current_user):
    data    = request.get_json() or {}
    tx_type = data.get("type")
    amount  = data.get("amount")
    date_str = data.get("date")

    # validacija
    if tx_type not in ("income", "expense"):
        return jsonify({"error": "Tip mora biti 'income' ili 'expense'"}), 400
    if not amount or float(amount) <= 0:
        return jsonify({"error": "Iznos mora biti pozitivan"}), 400

    # konvertujemo string datum u Python date objekat
    try:
        date = datetime.strptime(date_str, "%Y-%m-%d").date() if date_str else datetime.utcnow().date()
    except ValueError:
        return jsonify({"error": "Format datuma mora biti YYYY-MM-DD"}), 400

    transaction = Transaction(
        user_id=current_user.id,
        type=tx_type,
        amount=float(amount),
        description=data.get("description", ""),
        category_id=data.get("category_id"),
        date=date,
    )
    db.session.add(transaction)
    db.session.commit()

    return jsonify({
        "id":          transaction.id,
        "type":        transaction.type,
        "amount":      float(transaction.amount),
        "description": transaction.description,
        "date":        transaction.date.isoformat(),
        "category_id": transaction.category_id,
    }), 201


@transactions_bp.put("/<int:tx_id>")
@token_required
def update_transaction(current_user, tx_id):
    transaction = Transaction.query.filter_by(id=tx_id, user_id=current_user.id).first_or_404()
    data = request.get_json() or {}

    if "type" in data and data["type"] in ("income", "expense"):
        transaction.type = data["type"]
    if "amount" in data:
        transaction.amount = float(data["amount"])
    if "description" in data:
        transaction.description = data["description"]
    if "category_id" in data:
        transaction.category_id = data["category_id"]
    if "date" in data:
        try:
            transaction.date = datetime.strptime(data["date"], "%Y-%m-%d").date()
        except ValueError:
            return jsonify({"error": "Format datuma mora biti YYYY-MM-DD"}), 400

    db.session.commit()
    return jsonify({
        "id":          transaction.id,
        "type":        transaction.type,
        "amount":      float(transaction.amount),
        "description": transaction.description,
        "date":        transaction.date.isoformat(),
        "category_id": transaction.category_id,
    })


@transactions_bp.delete("/<int:tx_id>")
@token_required
def delete_transaction(current_user, tx_id):
    transaction = Transaction.query.filter_by(id=tx_id, user_id=current_user.id).first_or_404()
    db.session.delete(transaction)
    db.session.commit()
    return jsonify({"message": "Transakcija obrisana"})