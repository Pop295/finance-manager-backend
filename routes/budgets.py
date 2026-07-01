from flask import Blueprint, request, jsonify
from models import db, Budget, Transaction
from services.auth import token_required
from sqlalchemy import func
from datetime import datetime

budgets_bp = Blueprint("budgets", __name__, url_prefix="/api/budgets")


def current_month():
    # pomocna funkcija koja vraca trenutni mesec u formatu "2026-07"
    return datetime.utcnow().strftime("%Y-%m")


@budgets_bp.get("")
@token_required
def list_budgets(current_user):
    month = request.args.get("month", current_month())
    budgets = Budget.query.filter_by(user_id=current_user.id, month=month).all()

    monthly = None
    items = []

    for b in budgets:
        if b.category_id is None:
            # ukupni mesecni budzet
            monthly = {"id": b.id, "amount": float(b.amount), "month": b.month}
        else:
            # budzet po kategoriji - dodajemo i koliko je potroseno
            spent = db.session.query(func.sum(Transaction.amount)).filter(
                Transaction.user_id == current_user.id,
                Transaction.type == "expense",
                Transaction.category_id == b.category_id,
                func.date_format(Transaction.date, "%Y-%m") == month
            ).scalar() or 0

            items.append({
                "id":          b.id,
                "category_id": b.category_id,
                "amount":      float(b.amount),
                "spent":       float(spent),
                "month":       b.month,
            })

    return jsonify({"monthly": monthly, "items": items})


@budgets_bp.post("")
@token_required
def create_budget(current_user):
    data        = request.get_json() or {}
    amount      = data.get("amount")
    month       = data.get("month", current_month())
    category_id = data.get("category_id")  # None = ukupni mesecni budzet

    if not amount or float(amount) <= 0:
        return jsonify({"error": "Iznos mora biti pozitivan"}), 400

    # ako vec postoji budzet za ovu kategoriju i mesec, azuriramo ga
    existing = Budget.query.filter_by(
        user_id=current_user.id,
        category_id=category_id,
        month=month
    ).first()

    if existing:
        existing.amount = float(amount)
        db.session.commit()
        return jsonify({"id": existing.id, "amount": float(existing.amount), "month": existing.month})

    budget = Budget(
        user_id=current_user.id,
        category_id=category_id,
        amount=float(amount),
        month=month,
    )
    db.session.add(budget)
    db.session.commit()
    return jsonify({"id": budget.id, "amount": float(budget.amount), "month": budget.month}), 201


@budgets_bp.put("/monthly")
@token_required
def update_monthly(current_user):
    data   = request.get_json() or {}
    month  = data.get("month", current_month())
    amount = data.get("amount")

    if not amount:
        return jsonify({"error": "Iznos je obavezan"}), 400

    budget = Budget.query.filter_by(
        user_id=current_user.id, category_id=None, month=month
    ).first()

    if budget:
        budget.amount = float(amount)
    else:
        budget = Budget(user_id=current_user.id, category_id=None, amount=float(amount), month=month)
        db.session.add(budget)

    db.session.commit()
    return jsonify({"id": budget.id, "amount": float(budget.amount), "month": budget.month})


@budgets_bp.put("/<int:budget_id>")
@token_required
def update_budget(current_user, budget_id):
    budget = Budget.query.filter_by(id=budget_id, user_id=current_user.id).first_or_404()
    data   = request.get_json() or {}

    if "amount" in data:
        budget.amount = float(data["amount"])
    if "month" in data:
        budget.month = data["month"]

    db.session.commit()
    return jsonify({"id": budget.id, "amount": float(budget.amount), "month": budget.month})


@budgets_bp.delete("/<int:budget_id>")
@token_required
def delete_budget(current_user, budget_id):
    budget = Budget.query.filter_by(id=budget_id, user_id=current_user.id).first_or_404()
    db.session.delete(budget)
    db.session.commit()
    return jsonify({"message": "Budzet obrisan"})