import os
import uuid
from flask import Blueprint, request, jsonify, current_app
from models import db, User
from services.auth import token_required, hash_password, check_password

profile_bp = Blueprint("profile", __name__, url_prefix="/api/profile")

ALLOWED_AVATAR_EXT = {"png", "jpg", "jpeg", "gif", "webp"}


def _looks_like_image(head: bytes) -> bool:
    """Proverava stvarni sadrzaj fajla (prvih nekoliko bajtova), a ne samo ekstenziju."""
    return (
        head.startswith(b"\x89PNG\r\n\x1a\n")                      # PNG
        or head.startswith(b"\xff\xd8\xff")                          # JPEG
        or head.startswith((b"GIF87a", b"GIF89a"))                    # GIF
        or (head[:4] == b"RIFF" and head[8:12] == b"WEBP")           # WEBP
    )


def _profile_json(user):
    return {
        "id":       user.id,
        "name":     user.name,
        "email":    user.email,
        "avatar":   user.avatar,
        "currency": user.currency,
    }


@profile_bp.get("")
@token_required
def get_profile(current_user):
    # vraca podatke o trenutnom korisniku
    return jsonify({
        "id":       current_user.id,
        "name":     current_user.name,
        "email":    current_user.email,
        "avatar":   current_user.avatar,
        "currency": current_user.currency,
    })


@profile_bp.put("")
@token_required
def update_profile(current_user):
    data = request.get_json() or {}

    if "name" in data:
        current_user.name = data["name"].strip()
    if "email" in data:
        email = data["email"].strip().lower()
        if not email or "@" not in email:
            return jsonify({"error": "Email nije ispravan"}), 400
        taken = User.query.filter(User.email == email, User.id != current_user.id).first()
        if taken:
            return jsonify({"error": "Email već postoji"}), 409
        current_user.email = email
    if "currency" in data:
        current_user.currency = data["currency"]

    db.session.commit()
    return jsonify({
        "id":       current_user.id,
        "name":     current_user.name,
        "email":    current_user.email,
        "avatar":   current_user.avatar,
        "currency": current_user.currency,
    })


@profile_bp.put("/password")
@token_required
def change_password(current_user):
    data = request.get_json() or {}
    old_password = data.get("old_password") or data.get("current", "")
    new_password = data.get("new_password") or data.get("next", "")

    if not check_password(old_password, current_user.password):
        return jsonify({"error": "Stara lozinka nije ispravna"}), 400

    if check_password(new_password, current_user.password):
        return jsonify({"error": "Nova lozinka mora biti drugačija od stare"}), 400

    if len(new_password) < 6:
        return jsonify({"error": "Nova lozinka mora imati najmanje 6 karaktera"}), 400

    current_user.password = hash_password(new_password)
    db.session.commit()
    return jsonify({"message": "Lozinka uspesno promenjena"})

@profile_bp.post("/avatar")
@token_required
def upload_avatar(current_user):
    file = request.files.get("avatar")
    if not file or not file.filename:
        return jsonify({"error": "Slika nije poslata"}), 400

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ALLOWED_AVATAR_EXT:
        return jsonify({"error": "Dozvoljeni formati su PNG, JPG, GIF i WEBP"}), 400

    if not _looks_like_image(file.stream.read(16)):
        return jsonify({"error": "Fajl nije ispravna slika"}), 400
    file.stream.seek(0)

    upload_dir = os.path.join(current_app.root_path, "uploads", "avatars")
    os.makedirs(upload_dir, exist_ok=True)

    # Nasumicno ime fajla - ne koristimo ime koje je poslao korisnik
    filename = f"user_{current_user.id}_{uuid.uuid4().hex[:12]}.{ext}"
    file.save(os.path.join(upload_dir, filename))

    # Brisemo staru sliku (samo ako je nas fajl, ne spoljni URL)
    old = current_user.avatar or ""
    if old.startswith("/uploads/avatars/"):
        old_path = os.path.join(upload_dir, os.path.basename(old))
        if os.path.isfile(old_path):
            os.remove(old_path)

    current_user.avatar = f"/uploads/avatars/{filename}"
    db.session.commit()
    return jsonify(_profile_json(current_user))