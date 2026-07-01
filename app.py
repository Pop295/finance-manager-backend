from flask import Flask
from flask_cors import CORS
from config import Config
from models import db
from routes.auth import auth_bp
from routes.categories import categories_bp
from routes.transactions import transactions_bp
from routes.budgets import budgets_bp
from routes.dashboard import dashboard_bp

def create_app():
    app = Flask(__name__)
    
    # učitaj konfiguraciju iz config.py
    app.config.from_object(Config)
    
    # dozvoli zahteve sa frontenda
    CORS(app, resources={r"/api/*": {"origins": [
        Config.FRONTEND_URL,
        "http://localhost:5173"
    ]}})
    
    # poveži db sa aplikacijom
    db.init_app(app)
    
    with app.app_context():
        db.create_all()  # kreira tabele u bazi ako ne postoje
        app.register_blueprint(auth_bp)
        app.register_blueprint(categories_bp)
        app.register_blueprint(transactions_bp)
        app.register_blueprint(budgets_bp)
        app.register_blueprint(dashboard_bp)

    @app.get("/api/health")
    def health():
        return {"status": "ok", "message": "FinFlow backend radi!"}
    
    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=5000)