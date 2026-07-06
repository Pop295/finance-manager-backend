import os
import uuid
from werkzeug.utils import secure_filename
from flask import Blueprint, request, jsonify
from models import db
from services.auth import token_required, hash_password, check_password

profile_bp = Blueprint("profile", __name__, url_prefix="/api/profile")


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
    if "avatar" in data:
        current_user.avatar = data["avatar"]
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

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
UPLOAD_FOLDER = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static", "avatars"
)


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@profile_bp.post("/avatar")
@token_required
def upload_avatar(current_user):
    if "avatar" not in request.files:
        return jsonify({"error": "Fajl nije poslat"}), 400

    file = request.files["avatar"]

    if file.filename == "":
        return jsonify({"error": "Fajl nije izabran"}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": "Dozvoljeni formati su: PNG, JPG, WEBP"}), 400

    # provera veličine fajla
    file.seek(0, os.SEEK_END)
    size = file.tell()
    file.seek(0)
    if size > MAX_FILE_SIZE:
        return jsonify({"error": "Fajl je prevelik (maksimum 5MB)"}), 400

    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    ext = file.filename.rsplit(".", 1)[1].lower()
    filename = secure_filename(f"user_{current_user.id}_{uuid.uuid4().hex}.{ext}")
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)

    # puna URL adresa do slike (Flask servira /static automatski)
    avatar_url = f"{request.host_url.rstrip('/')}/static/avatars/{filename}"
    current_user.avatar = avatar_url
    db.session.commit()

    return jsonify({"avatar": avatar_url})