from flask import Blueprint, request, jsonify
from models import db, Transaction, Category, Budget
from services.auth import token_required
from sqlalchemy import func, text
from datetime import datetime

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/api")


@dashboard_bp.get("/dashboard")
@token_required
def dashboard(current_user):
    month = request.args.get("month", datetime.utcnow().strftime("%Y-%m"))

    income = db.session.query(func.sum(Transaction.amount)).filter(
        Transaction.user_id == current_user.id,
        Transaction.type == "income",
        func.date_format(Transaction.date, "%Y-%m") == month
    ).scalar() or 0

    expenses = db.session.query(func.sum(Transaction.amount)).filter(
        Transaction.user_id == current_user.id,
        Transaction.type == "expense",
        func.date_format(Transaction.date, "%Y-%m") == month
    ).scalar() or 0

    income   = float(income)
    expenses = float(expenses)

    by_category = db.session.query(
        Category.name,
        Category.color,
        func.sum(Transaction.amount).label("total")
    ).join(Transaction, Transaction.category_id == Category.id)\
    .filter(
        Transaction.user_id == current_user.id,
        Transaction.type == "expense",
        func.date_format(Transaction.date, "%Y-%m") == month
    ).group_by(Category.id, Category.name, Category.color)\
    .order_by(func.sum(Transaction.amount).desc()).all()

    monthly_rows = db.session.query(
        func.date_format(Transaction.date, "%Y-%m").label("month"),
        Transaction.type,
        func.sum(Transaction.amount).label("total")
    ).filter(
        Transaction.user_id == current_user.id,
        Transaction.date >= func.date_sub(func.curdate(), text("INTERVAL 6 MONTH"))
    ).group_by(
        func.date_format(Transaction.date, "%Y-%m"), Transaction.type
    ).order_by(
        func.date_format(Transaction.date, "%Y-%m")
    ).all()

    monthly_map = {}
    for row in monthly_rows:
        m = row.month
        if m not in monthly_map:
            monthly_map[m] = {"month": m, "income": 0, "expenses": 0}
        if row.type == "income":
            monthly_map[m]["income"] = float(row.total)
        else:
            monthly_map[m]["expenses"] = float(row.total)

    monthly_budget = Budget.query.filter_by(
        user_id=current_user.id, category_id=None, month=month
    ).first()
    remaining = float(monthly_budget.amount) - expenses if monthly_budget else None

    recent = Transaction.query.filter_by(user_id=current_user.id)\
        .order_by(Transaction.date.desc()).limit(10).all()

    return jsonify({
        "month":            month,
        "income":           income,
        "expenses":         expenses,
        "balance":          income - expenses,
        "remaining_budget": remaining,
        "by_category":      [{"name": r.name, "color": r.color, "total": float(r.total)} for r in by_category],
        "monthly_trend":    sorted(monthly_map.values(), key=lambda x: x["month"]),
        "recent":           [{
            "id":          t.id,
            "type":        t.type,
            "amount":      float(t.amount),
            "description": t.description,
            "date":        t.date.isoformat(),
            "category_id": t.category_id,
        } for t in recent],
    })


@dashboard_bp.get("/reports")
@token_required
def reports(current_user):
    rows = db.session.query(
        func.date_format(Transaction.date, "%Y-%m").label("month"),
        Transaction.type,
        func.sum(Transaction.amount).label("total")
    ).filter(
        Transaction.user_id == current_user.id,
        Transaction.date >= func.date_sub(func.curdate(), text("INTERVAL 12 MONTH"))
    ).group_by(
        func.date_format(Transaction.date, "%Y-%m"), Transaction.type
    ).order_by(
        func.date_format(Transaction.date, "%Y-%m")
    ).all()

    months       = sorted(set(r.month for r in rows))
    income_map   = {r.month: float(r.total) for r in rows if r.type == "income"}
    expenses_map = {r.month: float(r.total) for r in rows if r.type == "expense"}

    current_month = datetime.utcnow().strftime("%Y-%m")
    by_category = db.session.query(
        Category.name,
        Category.color,
        func.sum(Transaction.amount).label("total")
    ).join(Transaction, Transaction.category_id == Category.id)\
    .filter(
        Transaction.user_id == current_user.id,
        Transaction.type == "expense",
        func.date_format(Transaction.date, "%Y-%m") == current_month
    ).group_by(Category.id, Category.name, Category.color)\
    .order_by(func.sum(Transaction.amount).desc()).all()

    return jsonify({
        "months":     months,
        "income":     [income_map.get(m, 0) for m in months],
        "expenses":   [expenses_map.get(m, 0) for m in months],
        "byCategory": [{"name": r.name, "color": r.color, "total": float(r.total)} for r in by_category],
    })


@dashboard_bp.get("/dashboard/alerts")
@token_required
def alerts(current_user):
    month   = request.args.get("month", datetime.utcnow().strftime("%Y-%m"))
    budgets = Budget.query.filter_by(user_id=current_user.id, month=month).all()
    result  = []

    for b in budgets:
        if b.category_id is None:
            spent = db.session.query(func.sum(Transaction.amount)).filter(
                Transaction.user_id == current_user.id,
                Transaction.type == "expense",
                func.date_format(Transaction.date, "%Y-%m") == month
            ).scalar() or 0
            label = "Ukupni mesecni budzet"
        else:
            spent = db.session.query(func.sum(Transaction.amount)).filter(
                Transaction.user_id == current_user.id,
                Transaction.type == "expense",
                Transaction.category_id == b.category_id,
                func.date_format(Transaction.date, "%Y-%m") == month
            ).scalar() or 0
            label = b.category.name if b.category else f"Kategorija {b.category_id}"

        spent   = float(spent)
        limit   = float(b.amount)
        if limit == 0:
            continue
        percent = (spent / limit) * 100

        if percent >= 100:
            result.append({
                "category": label,
                "spent":    spent,
                "budget":   limit,
                "percent":  round(percent, 1),
                "severity": "danger",
                "message":  f"Prekoracen budzet za {label}!"
            })
        elif percent >= 80:
            result.append({
                "category": label,
                "spent":    spent,
                "budget":   limit,
                "percent":  round(percent, 1),
                "severity": "warning",
                "message":  f"Blizu limita za {label}: {percent:.0f}%"
            })

    return jsonify(result)