from flask_sqlalchemy import SQLAlchemy

# db je glavni objekat kroz koji komuniciramo sa bazom
# sve tabele i upiti idu kroz njega
db = SQLAlchemy()

from datetime import datetime

class User(db.Model):
    __tablename__ = "users"  # naziv tabele u bazi

    id         = db.Column(db.Integer, primary_key=True)
    name       = db.Column(db.String(100), nullable=False)
    email      = db.Column(db.String(150), unique=True, nullable=False)
    password   = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    avatar    = db.Column(db.String(255), nullable=True)
    currency  = db.Column(db.String(10), default="RSD")

class Category(db.Model):
    __tablename__ = "categories"

    id      = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    name    = db.Column(db.String(100), nullable=False)
    color   = db.Column(db.String(20), default="#6366f1")
    icon    = db.Column(db.String(50), default="tag")


class Transaction(db.Model):
    __tablename__ = "transactions"

    id          = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=True)
    type        = db.Column(db.Enum("income", "expense"), nullable=False)
    amount      = db.Column(db.Numeric(12, 2), nullable=False)
    description = db.Column(db.String(255), nullable=True)
    date        = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)


class Budget(db.Model):
    __tablename__ = "budgets"

    id          = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=True)
    amount      = db.Column(db.Numeric(12, 2), nullable=False)
    month       = db.Column(db.String(7), nullable=False)  # format: "2026-06"