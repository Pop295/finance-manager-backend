# Pomoćne funkcije za autentifikaciju - hashiranje lozinki, JWT tokeni, zaštita ruta

import jwt
import bcrypt
from datetime import datetime, timedelta, timezone
from functools import wraps
from flask import request, jsonify, current_app
from models import User


def hash_password(plain: str) -> str:
    """
    Pretvara lozinku u nečitljiv hash koji se čuva u bazi.
    Bcrypt dodaje nasumični 'salt' pa čak i iste lozinke daju različite hasheve.
    Nikad ne čuvamo originalnu lozinku u bazi!
    """
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def check_password(plain: str, hashed: str) -> bool:
    """
    Poredi unesenu lozinku sa hashom iz baze.
    Bcrypt interno zna kako da ih uporedi i vraća True ili False.
    """
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def create_token(user_id: int) -> str:
    """
    Pravi JWT token koji važi 7 dana.
    Token u sebi nosi user_id i datum isteka.
    Potpisan je sa JWT_SECRET tako da backend može da proveri da li je validan.
    """
    payload = {
        "user_id": user_id,
        "exp":     datetime.now(timezone.utc) + timedelta(days=7),
    }
    return jwt.encode(payload, current_app.config["JWT_SECRET"], algorithm="HS256")


def token_required(f):
    """
    Dekorator koji štiti rute od neautorizovanog pristupa.
    Kada se stavi @token_required iznad neke rute, pre nego što se ta ruta
    izvrši, automatski se proverava da li je token validan.
    
    Tok provere:
    1. Čita Authorization header iz zahteva
    2. Proverava da li počinje sa "Bearer "
    3. Dekodira token i proverava da li je validan i nije istekao
    4. Traži korisnika u bazi
    5. Ako je sve OK - prosleđuje korisnika ruti kao prvi argument
    6. Ako nije OK - vraća 401 grešku
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        # Čitamo Authorization header (npr. "Bearer eyJhbG...")
        auth_header = request.headers.get("Authorization", "")
        
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Token nije prosleđen"}), 401
        
        # Uzimamo samo token deo (bez "Bearer ")
        token = auth_header.split(" ")[1]
        
        try:
            # Dekodiramo token i proveravamo potpis i datum isteka
            payload = jwt.decode(
                token,
                current_app.config["JWT_SECRET"],
                algorithms=["HS256"]
            )
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token je istekao"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Nevažeći token"}), 401
        
        # Tražimo korisnika u bazi na osnovu user_id iz tokena
        user = User.query.get(payload["user_id"])
        if not user:
            return jsonify({"error": "Korisnik ne postoji"}), 401
        
        # Prosleđujemo korisnika ruti kao prvi argument
        return f(user, *args, **kwargs)
    return decorated