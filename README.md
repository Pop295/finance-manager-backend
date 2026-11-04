# FinFlow – Backend

REST API za aplikaciju za upravljanje ličnim finansijama (FinFlow), razvijen u Python-u pomoću Flask-a. Frontend se nalazi u posebnom repozitorijumu: [finance-manager-frontend](https://github.com/Pop295/finance-manager-frontend).

## Funkcionalnosti

- Registracija i prijava korisnika uz JWT autentifikaciju (token važi 7 dana)
- Bezbedno čuvanje lozinki (bcrypt) i promena lozinke
- Prihodi i rashodi (transakcije): dodavanje, izmena, brisanje i pretraga
- Kategorije sa bojom i ikonicom (svaki korisnik ima svoje)
- Budžeti: ukupni mesečni budžet i budžeti po kategorijama
- Dashboard: bilans, prihodi, rashodi i upozorenja o prekoračenju budžeta
- Izveštaji: mesečni prihodi i rashodi, potrošnja po kategorijama
- Profil korisnika (ime, email, avatar, valuta)
- Zaštićene rute: svaki korisnik vidi samo svoje podatke

## Tehnologije

- Python, Flask 3
- Flask-SQLAlchemy / SQLAlchemy 2 (ORM)
- MySQL / MariaDB (PyMySQL)
- PyJWT, bcrypt
- Flask-CORS, python-dotenv

## Struktura projekta

```
app.py          Pokretanje aplikacije, CORS, registracija ruta
config.py       Konfiguracija (učitava vrednosti iz .env)
models/         SQLAlchemy modeli (User, Category, Transaction, Budget)
routes/         API rute (auth, transactions, categories, budgets, dashboard, profile)
services/       Pomoćne funkcije (hash lozinke, JWT, token_required)
uploads/        Otpremljene slike profila (pravi se automatski, nije u Git-u)
```

## Baza podataka

Tabele: `users`, `categories`, `transactions`, `budgets`. Tabele se kreiraju automatski pri prvom pokretanju (`db.create_all()`), pa je potrebno samo da postoji prazna baza.

## Pokretanje

### Preduslovi

- Python 3.10+
- MySQL ili MariaDB server

### Koraci

1. Kloniraj repozitorijum:
   ```bash
   git clone https://github.com/Pop295/finance-manager-backend.git
   cd finance-manager-backend
   ```
2. Napravi i aktiviraj virtuelno okruženje:
   ```bash
   python -m venv venv
   venv\Scripts\activate        # Windows
   source venv/bin/activate     # Linux / macOS
   ```
3. Instaliraj zavisnosti:
   ```bash
   pip install -r requirements.txt
   ```
4. Napravi praznu bazu:
   ```sql
   CREATE DATABASE finflow CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   ```
5. Kopiraj `.env.example` u `.env` i unesi svoje vrednosti:
   ```
   MYSQL_HOST=127.0.0.1
   MYSQL_PORT=3306
   MYSQL_USER=root
   MYSQL_PASSWORD=<lozinka>
   MYSQL_DB=finflow
   JWT_SECRET=<dug-nasumican-kljuc>
   FRONTEND_URL=http://localhost:5173
   ```
6. Pokreni server:
   ```bash
   python app.py
   ```
7. API radi na `http://localhost:5000`. Provera: `http://localhost:5000/api/health`.

## API pregled

Sve rute osim registracije, prijave i health check-a zahtevaju header `Authorization: Bearer <token>`.

| Ruta | Metode | Opis |
|------|--------|------|
| `/api/auth/register`, `/api/auth/login` | POST | Registracija i prijava |
| `/api/transactions` | GET, POST | Lista i kreiranje transakcija |
| `/api/transactions/<id>` | PUT, DELETE | Izmena i brisanje |
| `/api/categories` | GET, POST | Lista i kreiranje kategorija |
| `/api/categories/<id>` | PUT, DELETE | Izmena i brisanje |
| `/api/budgets` | GET, POST | Lista i kreiranje budžeta |
| `/api/budgets/monthly` | PUT | Izmena ukupnog mesečnog budžeta |
| `/api/budgets/<id>` | PUT, DELETE | Izmena i brisanje |
| `/api/dashboard` | GET | Podaci za početnu stranu |
| `/api/dashboard/alerts` | GET | Upozorenja o budžetu |
| `/api/reports` | GET | Mesečni izveštaji |
| `/api/profile` | GET, PUT | Pregled i izmena profila |
| `/api/profile/password` | PUT | Promena lozinke |
| `/api/profile/avatar` | POST | Upload slike profila (PNG, JPG, GIF, WEBP, do 2 MB) |
| `/api/health` | GET | Provera da server radi |

## Autori

- [@ISSAmaci](https://github.com/ISSAmaci): backend
- [@Pop295](https://github.com/Pop295): frontend, ispravke u backendu
