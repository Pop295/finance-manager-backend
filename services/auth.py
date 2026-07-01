import jwt
import bcrypt
from datetime import datetime, timedelta, timezone
from functools import wraps
from flask import request, jsonify, current_app
from models import User

def hash_password(plain):
    # pretvara lozinku u hash koji se cuva u bazi
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()

def check_password(plain, hashed):
    # poredi unesenu lozinku sa hashom iz baze
    return bcrypt.checkpw(plain.encode(), hashed.encode())

def create_token(user_id):
    # pravi JWT token koji vazi 7 dana
    payload = {
        "user_id": user_id,
        "exp": datetime.now(timezone.utc) + timedelta(days=7)
    }
    return jwt.encode(payload, current_app.config["JWT_SECRET"], algorithm="HS256")

def token_required(f):
    # dekorator koji stiti rute - proverava da li je token validan
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Token nije prosledjen"}), 401
        
        token = auth_header.split(" ")[1]
        
        try:
            payload = jwt.decode(token, current_app.config["JWT_SECRET"], algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token je istekao"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Nevazeci token"}), 401
        
        user = User.query.get(payload["user_id"])
        if not user:
            return jsonify({"error": "Korisnik ne postoji"}), 401
        
        return f(user, *args, **kwargs)
    return decorated