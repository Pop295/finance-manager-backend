# Glavni fajl Flask aplikacije - ovde se sve spaja zajedno
import os
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from config import Config
from models import db

# Uvoz svih Blueprint-ova (grupa ruta)
from routes.auth import auth_bp
from routes.categories import categories_bp
from routes.transactions import transactions_bp
from routes.budgets import budgets_bp
from routes.dashboard import dashboard_bp
from routes.profile import profile_bp


def create_app():
    # Kreiranje Flask aplikacije
    app = Flask(__name__)
    
    # Učitavanje konfiguracije iz config.py (baza, JWT ključ...)
    app.config.from_object(Config)
    # Maksimalna velicina zahteva (upload avatara) - 2 MB
    app.config["MAX_CONTENT_LENGTH"] = 2 * 1024 * 1024
    
    # CORS - dozvoljava frontendu da šalje zahteve backendu
    # Bez ovoga browser bi blokirao sve zahteve sa localhost:5173 ka localhost:5000
    CORS(app, resources={r"/api/*": {"origins": [
        Config.FRONTEND_URL,
        "http://localhost:5173"
    ], "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
       "allow_headers": ["Content-Type", "Authorization"]}})
    
    # Povezivanje SQLAlchemy sa Flask aplikacijom
    db.init_app(app)
    
    with app.app_context():
        # Kreira tabele u bazi ako ne postoje (na osnovu modela iz models/)
        db.create_all()
    
    # Registracija svih Blueprint-ova - svaki Blueprint je grupa povezanih ruta
    app.register_blueprint(auth_bp)           # /api/auth/*
    app.register_blueprint(categories_bp)     # /api/categories/*
    app.register_blueprint(transactions_bp)   # /api/transactions/*
    app.register_blueprint(budgets_bp)        # /api/budgets/*
    app.register_blueprint(dashboard_bp)      # /api/dashboard, /api/reports, /api/dashboard/alerts
    app.register_blueprint(profile_bp)        # /api/profile/*

    # Posluzuje otpremljene slike (avatare) iz foldera uploads/
    @app.get("/uploads/<path:filename>")
    def uploaded_file(filename):
        return send_from_directory(os.path.join(app.root_path, "uploads"), filename)

    # Prevelik fajl -> jasna poruka umesto HTML greske
    @app.errorhandler(413)
    def too_large(_e):
        return jsonify({"error": "Slika je prevelika (maksimum 2 MB)"}), 413

    # Health check ruta - za proveru da li server radi
    @app.get("/api/health")
    def health():
        return {"status": "ok", "message": "FinFlow backend radi!"}

    return app


if __name__ == "__main__":
    # Pokretanje servera u debug modu na portu 5000
    # Debug mod automatski restartuje server kad se promeni kod
    app = create_app()
    app.run(debug=True, port=5000)