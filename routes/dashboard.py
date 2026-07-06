# Rute za dashboard, izveštaje i upozorenja
# Ovo je najbitniji deo backenda - agregacija podataka za grafikone i kartice
# Sve rute su zaštićene tokenom (@token_required)

from flask import Blueprint, request, jsonify
from models import db, Transaction, Category, Budget
from services.auth import token_required
from sqlalchemy import func, text
from datetime import datetime

# Blueprint grupiše dashboard rute pod /api prefiks
dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/api")


@dashboard_bp.get("/dashboard")
@token_required
def dashboard(current_user):
    """
    Glavna agregacija podataka za Dashboard stranicu.
    Sve se računa na serveru i šalje frontendu kao gotovi podaci.
    
    Query parametar: month (opciono, default je trenutni mesec)
    
    Vraća:
    - month          - trenutni mesec
    - income         - ukupni prihodi za mesec
    - expenses       - ukupni rashodi za mesec
    - balance        - bilans (prihodi - rashodi)
    - remaining_budget - preostali budžet (mesečni budžet - rashodi)
    - by_category    - rashodi grupisani po kategorijama (za pie chart)
    - monthly_trend  - prihodi i rashodi po mesecima za poslednjih 6 meseci (za line chart)
    - recent         - poslednjih 10 transakcija
    """
    month = request.args.get("month", datetime.utcnow().strftime("%Y-%m"))

    # Ukupni prihodi za trenutni mesec
    income = db.session.query(func.sum(Transaction.amount)).filter(
        Transaction.user_id == current_user.id,
        Transaction.type == "income",
        func.date_format(Transaction.date, "%Y-%m") == month
    ).scalar() or 0

    # Ukupni rashodi za trenutni mesec
    expenses = db.session.query(func.sum(Transaction.amount)).filter(
        Transaction.user_id == current_user.id,
        Transaction.type == "expense",
        func.date_format(Transaction.date, "%Y-%m") == month
    ).scalar() or 0

    income   = float(income)
    expenses = float(expenses)

    # Rashodi grupisani po kategorijama - koristi se za pie chart
    # JOIN sa Category tabelom da dobijemo naziv i boju kategorije
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

    # Mesečni trend za poslednjih 6 meseci - koristi se za line chart
    # Grupišemo po mesecu i tipu transakcije
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

    # Organizujemo mesečni trend u rečnik za lakše čitanje
    monthly_map = {}
    for row in monthly_rows:
        m = row.month
        if m not in monthly_map:
            monthly_map[m] = {"month": m, "income": 0, "expenses": 0}
        if row.type == "income":
            monthly_map[m]["income"] = float(row.total)
        else:
            monthly_map[m]["expenses"] = float(row.total)

    # Preostali budžet = mesečni budžet - ukupni rashodi
    monthly_budget = Budget.query.filter_by(
        user_id=current_user.id, category_id=None, month=month
    ).first()
    remaining = float(monthly_budget.amount) - expenses if monthly_budget else None

    # Poslednjih 10 transakcija za Recent Transactions listu
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
            "title":       t.title or t.description,
            "type":        t.type,
            "amount":      float(t.amount),
            "description": t.description,
            "date":        t.date.isoformat(),
            "category_id": t.category_id,
            "category":    t.category.name if t.category else None,
        } for t in recent],
    })


@dashboard_bp.get("/reports")
@token_required
def reports(current_user):
    """
    Podaci za Reports stranicu - pregled za poslednjih 12 meseci.
    
    Vraća:
    - months      - lista meseci (npr. ["2026-01", "2026-02", ...])
    - income      - lista prihoda po mesecima
    - expenses    - lista rashoda po mesecima
    - byCategory  - rashodi po kategorijama za trenutni mesec
    """
    # Prihodi i rashodi po mesecima za poslednjih 12 meseci
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

    # Organizujemo podatke u liste za grafikon
    months       = sorted(set(r.month for r in rows))
    income_map   = {r.month: float(r.total) for r in rows if r.type == "income"}
    expenses_map = {r.month: float(r.total) for r in rows if r.type == "expense"}

    # Rashodi po kategorijama za trenutni mesec
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
    """
    Upozorenja kada korisnik prekorači ili se približi budžetu.
    
    Query parametar: month (opciono, default je trenutni mesec)
    
    Vraća listu upozorenja sa:
    - severity "warning" - kada je potrošeno 80% ili više budžeta
    - severity "danger"  - kada je budžet prekoračen (100% ili više)
    """
    month   = request.args.get("month", datetime.utcnow().strftime("%Y-%m"))
    budgets = Budget.query.filter_by(user_id=current_user.id, month=month).all()
    result  = []

    for b in budgets:
        # Računamo koliko je potrošeno za ovaj budžet
        if b.category_id is None:
            # Ukupni mesečni budžet - sabiramo sve rashode
            spent = db.session.query(func.sum(Transaction.amount)).filter(
                Transaction.user_id == current_user.id,
                Transaction.type == "expense",
                func.date_format(Transaction.date, "%Y-%m") == month
            ).scalar() or 0
            label = "Ukupni mesečni budžet"
        else:
            # Budžet po kategoriji - sabiramo rashode samo te kategorije
            spent = db.session.query(func.sum(Transaction.amount)).filter(
                Transaction.user_id == current_user.id,
                Transaction.type == "expense",
                Transaction.category_id == b.category_id,
                func.date_format(Transaction.date, "%Y-%m") == month
            ).scalar() or 0
            label = b.category.name if b.category else f"Kategorija {b.category_id}"

        spent   = float(spent)
        limit   = float(b.amount)
        
        # Preskačemo budžete sa limitom 0
        if limit == 0:
            continue
        
        # Računamo procenat potrošenog budžeta
        percent = (spent / limit) * 100

        if percent >= 100:
            # Budžet je prekoračen
            result.append({
                "category": label,
                "spent":    spent,
                "budget":   limit,
                "percent":  round(percent, 1),
                "severity": "danger",
                "message":  f"Prekoračen budžet za {label}!"
            })
        elif percent >= 80:
            # Blizu limita - upozorenje
            result.append({
                "category": label,
                "spent":    spent,
                "budget":   limit,
                "percent":  round(percent, 1),
                "severity": "warning",
                "message":  f"Blizu limita za {label}: {percent:.0f}%"
            })

    return jsonify(result)