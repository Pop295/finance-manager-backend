from flask import Blueprint, request, jsonify
from models import db, User
from services.auth import hash_password, check_password, create_token

# Blueprint je grupa povezanih ruta, registrujemo ga kasnije u app.py
auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@auth_bp.post("/register")
def register():
    data = request.get_json() or {}
    name     = data.get("name", "").strip()
    email    = data.get("email", "").strip().lower()
    password = data.get("password", "")

    # provera da li su sva polja popunjena
    if not name or not email or not password:
        return jsonify({"error": "Sva polja su obavezna"}), 400

    # provera da li email vec postoji u bazi
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email vec postoji"}), 409

    # kreiranje novog korisnika
    user = User(name=name, email=email, password=hash_password(password))
    db.session.add(user)
    db.session.commit()

    token = create_token(user.id)
    return jsonify({"token": token, "user": {"id": user.id, "name": user.name, "email": user.email}}), 201


@auth_bp.post("/login")
def login():
    data     = request.get_json() or {}
    email    = data.get("email", "").strip().lower()
    password = data.get("password", "")

    # trazimo korisnika po emailu
    user = User.query.filter_by(email=email).first()

    # ako korisnik ne postoji ili lozinka nije ispravna
    if not user or not check_password(password, user.password):
        return jsonify({"error": "Pogresan email ili lozinka"}), 401

    token = create_token(user.id)
    return jsonify({"token": token, "user": {"id": user.id, "name": user.name, "email": user.email}}), 200