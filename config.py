# Konfiguracija aplikacije - čita podatke iz .env fajla

import os
from dotenv import load_dotenv

# Učitava .env fajl da bi os.getenv() mogao da čita vrednosti iz njega
load_dotenv()

class Config:
    # MySQL konfiguracija - podaci za konekciju na bazu
    MYSQL_HOST     = os.getenv("MYSQL_HOST")        # adresa servera (127.0.0.1)
    MYSQL_PORT     = int(os.getenv("MYSQL_PORT"))   # port (3306) - mora biti broj
    MYSQL_USER     = os.getenv("MYSQL_USER")        # korisničko ime (root)
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")    # lozinka
    MYSQL_DB       = os.getenv("MYSQL_DB")          # naziv baze (finflow)

    # Connection string - SQLAlchemy koristi ovaj format da se poveže na MySQL
    # Format: mysql+pymysql://korisnik:lozinka@adresa:port/naziv_baze
    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}"
        f"@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}"
    )
    
    # Gasi nepotrebna upozorenja koja SQLAlchemy inače prikazuje
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Tajni ključ za potpisivanje JWT tokena
    # Ako neko promeni token, potpis više ne važi i backend ga odbija
    JWT_SECRET = os.getenv("JWT_SECRET")
    
    # URL frontenda - koristi se za CORS podešavanja
    FRONTEND_URL = os.getenv("FRONTEND_URL")