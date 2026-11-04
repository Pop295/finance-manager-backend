# Rute za autentifikaciju - jedine rute koje ne zahtevaju JWT token
# Korisnik ovde dobija token koji koristi za sve ostale zahteve

from flask import Blueprint, request, jsonify
from models import db, User
from services.auth import hash_password, check_password, create_token

# Blueprint grupiše sve auth rute pod /api/auth prefiks
auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@auth_bp.post("/register")
def register():
    """
    Registracija novog korisnika.
    
    Prima: { name, email, password }
    Vraća: { token, user }
    
    Proces:
    1. Proverava da li su sva polja popunjena
    2. Proverava da li email već postoji u bazi
    3. Hashira lozinku (nikad ne čuvamo plain text)
    4. Kreira korisnika u bazi
    5. Vraća JWT token i podatke o korisniku
    """
    data = request.get_json() or {}
    name     = data.get("name", "").strip()
    email    = data.get("email", "").strip().lower()
    password = data.get("password", "")

    # Validacija - sva polja moraju biti popunjena
    if not name or not email or not password:
        return jsonify({"error": "Sva polja su obavezna"}), 400

    # Provera da li email već postoji
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email već postoji"}), 409

    # Kreiranje korisnika sa hashiranom lozinkom
    user = User(name=name, email=email, password=hash_password(password))
    db.session.add(user)
    db.session.commit()

    # Vraćamo token i osnovne podatke o korisniku
    token = create_token(user.id)
    return jsonify({
        "token": token,
        "user": {"id": user.id, "name": user.name, "email": user.email, "avatar": user.avatar}
    }), 201


@auth_bp.post("/login")
def login():
    """
    Prijava postojećeg korisnika.
    
    Prima: { email, password }
    Vraća: { token, user }
    
    Proces:
    1. Traži korisnika po emailu u bazi
    2. Poredi unesenu lozinku sa hashom iz baze
    3. Ako se poklapaju - vraća JWT token
    4. Ako ne - vraća grešku 401
    
    Napomena: Namerno vraćamo istu grešku za pogrešan email i pogrešnu lozinku
    da ne otkrijemo da li email postoji u sistemu
    """
    data     = request.get_json() or {}
    email    = data.get("email", "").strip().lower()
    password = data.get("password", "")

    # Tražimo korisnika po emailu
    user = User.query.filter_by(email=email).first()

    # Ako korisnik ne postoji ili lozinka nije ispravna - vraćamo istu grešku
    if not user or not check_password(password, user.password):
        return jsonify({"error": "Pogrešan email ili lozinka"}), 401

    token = create_token(user.id)
    return jsonify({
        "token": token,
        "user": {"id": user.id, "name": user.name, "email": user.email, "avatar": user.avatar}
    }), 200