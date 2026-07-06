# Modeli - Python klase koje predstavljaju tabele u MySQL bazi
# SQLAlchemy automatski kreira tabele na osnovu ovih klasa

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# Glavni objekat kroz koji komuniciramo sa bazom
# Sve tabele i upiti idu kroz njega
db = SQLAlchemy()


class User(db.Model):
    """Tabela korisnika - čuva podatke o registrovanim korisnicima"""
    __tablename__ = "users"

    id         = db.Column(db.Integer, primary_key=True)                          # jedinstveni ID, automatski se uvećava
    name       = db.Column(db.String(100), nullable=False)                        # ime korisnika
    email      = db.Column(db.String(150), unique=True, nullable=False)           # email mora biti jedinstven
    password   = db.Column(db.String(255), nullable=False)                        # hashirana lozinka (nikad plain text)
    avatar     = db.Column(db.String(255), nullable=True)                         # URL avatara
    currency   = db.Column(db.String(10), default="RSD")                         # valuta korisnika
    created_at = db.Column(db.DateTime, default=datetime.utcnow)                  # datum registracije

    # Veze sa drugim tabelama - omogućava brisanje svih podataka korisnika kad se obriše nalog
    categories   = db.relationship("Category",   backref="user", lazy=True, cascade="all,delete")
    transactions = db.relationship("Transaction", backref="user", lazy=True, cascade="all,delete")
    budgets      = db.relationship("Budget",      backref="user", lazy=True, cascade="all,delete")


class Category(db.Model):
    """Tabela kategorija - korisnik organizuje transakcije u kategorije"""
    __tablename__ = "categories"

    id      = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)   # koja kategorija pripada kom korisniku
    name    = db.Column(db.String(100), nullable=False)                           # naziv kategorije (npr. Hrana)
    color   = db.Column(db.String(20), default="#6366f1")                        # boja za prikaz u grafikonu
    icon    = db.Column(db.String(50), default="tag")                            # ikonica kategorije


class Transaction(db.Model):
    """Tabela transakcija - svaki prihod ili rashod korisnika"""
    __tablename__ = "transactions"

    id          = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)      # čiji je trošak
    title       = db.Column(db.String(255), nullable=True)                               # naziv transakcije (npr. Pica)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=True)  # kojoj kategoriji pripada
    type        = db.Column(db.Enum("income", "expense"), nullable=False)               # prihod ili rashod
    amount      = db.Column(db.Numeric(12, 2), nullable=False)                          # iznos (do 12 cifara, 2 decimale)
    description = db.Column(db.String(255), nullable=True)                               # napomena/opis
    date        = db.Column(db.Date, nullable=False, default=datetime.utcnow)           # datum transakcije
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)                       # kad je uneta u sistem

    # Veza sa kategorijom - omogućava pisanje t.category.name umesto posebnog upita
    category = db.relationship("Category", foreign_keys=[category_id])


class Budget(db.Model):
    """Tabela budžeta - korisnik postavlja limite potrošnje"""
    __tablename__ = "budgets"

    id          = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=True)  # NULL = ukupni mesečni budžet
    amount      = db.Column(db.Numeric(12, 2), nullable=False)                          # limit potrošnje
    month       = db.Column(db.String(7), nullable=False)                               # mesec u formatu "2026-07"

    # Veza sa kategorijom
    category = db.relationship("Category", foreign_keys=[category_id])