# Rute za budžete - upravljanje mesečnim budžetom i budžetima po kategorijama
# Sve rute su zaštićene tokenom (@token_required)

from flask import Blueprint, request, jsonify
from models import db, Budget, Transaction
from services.auth import token_required
from sqlalchemy import func
from datetime import datetime

# Blueprint grupiše sve budget rute pod /api/budgets prefiks
budgets_bp = Blueprint("budgets", __name__, url_prefix="/api/budgets")


def current_month():
    """Pomoćna funkcija koja vraća trenutni mesec u formatu '2026-07'"""
    return datetime.utcnow().strftime("%Y-%m")


@budgets_bp.get("")
@token_required
def list_budgets(current_user):
    """
    Vraća sve budžete korisnika za određeni mesec.
    Za svaki budžet po kategoriji računa koliko je već potrošeno.
    
    Query parametar: month (opciono, default je trenutni mesec)
    Vraća: { monthly: broj, items: [ { id, category, amount, spent, month }, ... ] }
    
    monthly - ukupni mesečni budžet (category_id = NULL)
    items   - budžeti po kategorijama sa izračunatom potrošnjom
    """
    month = request.args.get("month", current_month())
    budgets = Budget.query.filter_by(user_id=current_user.id, month=month).all()

    monthly = None
    items = []

    for b in budgets:
        if b.category_id is None:
            # Ukupni mesečni budžet - category_id je NULL
            monthly = float(b.amount)
        else:
            # Budžet po kategoriji - računamo koliko je potrošeno u toj kategoriji
            spent = db.session.query(func.sum(Transaction.amount)).filter(
                Transaction.user_id == current_user.id,
                Transaction.type == "expense",
                Transaction.category_id == b.category_id,
                func.date_format(Transaction.date, "%Y-%m") == month
            ).scalar() or 0

            items.append({
                "id":       b.id,
                "category": b.category.name if b.category else None,
                "category_id": b.category_id,
                "amount":   float(b.amount),
                "spent":    float(spent),  # koliko je već potrošeno
                "month":    b.month,
            })

    return jsonify({"monthly": monthly, "items": items})


@budgets_bp.post("")
@token_required
def create_budget(current_user):
    """
    Kreira novi budžet ili ažurira postojeći ako već postoji za isti mesec i kategoriju.
    
    Prima: { amount, month?, category_id? }
    - category_id = NULL → ukupni mesečni budžet
    - category_id = broj → budžet za određenu kategoriju
    Vraća: { id, amount, month }
    """
    data        = request.get_json() or {}
    amount      = data.get("amount")
    month       = data.get("month", current_month())
    category_id = data.get("category_id")  # None = ukupni mesečni budžet

    # Validacija iznosa
    if not amount or float(amount) <= 0:
        return jsonify({"error": "Iznos mora biti pozitivan"}), 400

    # Ako već postoji budžet za ovu kategoriju i mesec, samo ga ažuriramo
    existing = Budget.query.filter_by(
        user_id=current_user.id,
        category_id=category_id,
        month=month
    ).first()

    if existing:
        existing.amount = float(amount)
        db.session.commit()
        return jsonify({"id": existing.id, "amount": float(existing.amount), "month": existing.month})

    # Kreiranje novog budžeta
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
    """
    Ažurira ukupni mesečni budžet (onaj bez kategorije).
    Ako ne postoji, kreira ga.
    
    Prima: { amount, month? }
    Vraća: { id, amount, month }
    """
    data   = request.get_json() or {}
    month  = data.get("month", current_month())
    amount = data.get("amount")

    # Validacija
    if amount is None:
        return jsonify({"error": "Iznos je obavezan"}), 400

    # Tražimo postojeći mesečni budžet (category_id = NULL)
    budget = Budget.query.filter_by(
        user_id=current_user.id, category_id=None, month=month
    ).first()

    if budget:
        # Ažuriramo postojeći
        budget.amount = float(amount)
    else:
        # Kreiramo novi mesečni budžet
        budget = Budget(user_id=current_user.id, category_id=None, amount=float(amount), month=month)
        db.session.add(budget)

    db.session.commit()
    return jsonify({"id": budget.id, "amount": float(budget.amount), "month": budget.month})


@budgets_bp.put("/<int:budget_id>")
@token_required
def update_budget(current_user, budget_id):
    """
    Ažurira budžet po ID-u.
    
    Prima: { amount?, month? }
    Vraća: { id, amount, month }
    """
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
    """
    Briše budžet.
    filter_by sa user_id osigurava da korisnik može brisati samo svoje budžete.
    """
    budget = Budget.query.filter_by(id=budget_id, user_id=current_user.id).first_or_404()
    db.session.delete(budget)
    db.session.commit()
    return jsonify({"message": "Budžet obrisan"})