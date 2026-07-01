import os
from dotenv import load_dotenv

load_dotenv()  # učitava .env fajl

class Config:
    MYSQL_HOST     = os.getenv("MYSQL_HOST")           # adresa servera
    MYSQL_PORT     = int(os.getenv("MYSQL_PORT"))      # port (mora biti broj)
    MYSQL_USER     = os.getenv("MYSQL_USER")           # korisničko ime
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")       # lozinka
    MYSQL_DB       = os.getenv("MYSQL_DB")             # naziv baze

    # connection string - SQLAlchemy koristi ovaj format da se poveže na MySQL
    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}"
        f"@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False  # gasi nepotrebna upozorenja

    JWT_SECRET = os.getenv("JWT_SECRET")  # tajni ključ za tokene
    FRONTEND_URL = os.getenv("FRONTEND_URL")