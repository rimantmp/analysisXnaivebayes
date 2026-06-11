from functools import wraps
import re
from urllib.parse import urljoin, urlparse

from flask import (
    Blueprint,
    current_app,
    flash,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash


auth = Blueprint("auth", __name__)


def database():
    return current_app.extensions["database"]


def is_safe_redirect(target):
    host = urlparse(request.host_url)
    destination = urlparse(urljoin(request.host_url, target))
    return destination.scheme in {"http", "https"} and host.netloc == destination.netloc


@auth.before_app_request
def load_logged_in_user():
    g.user = None
    if current_app.config["AUTH_DISABLED"]:
        g.user = {
            "id": 0,
            "name": "Test User",
            "username": "test",
            "role": "admin",
            "is_active": True,
        }
        return

    user_id = session.get("user_id")
    if user_id and database().available:
        g.user = database().find_user_by_id(user_id)
        if g.user and not g.user["is_active"]:
            session.clear()
            g.user = None


@auth.before_app_request
def require_authentication():
    if current_app.config["AUTH_DISABLED"]:
        return None
    allowed = {"auth.login", "static"}
    if request.endpoint in allowed or request.endpoint is None:
        return None
    if g.user is None:
        return redirect(url_for("auth.login", next=request.full_path.rstrip("?")))
    return None


def login_required(view):
    @wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for("auth.login"))
        return view(**kwargs)

    return wrapped_view


def admin_required(view):
    @wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for("auth.login"))
        if g.user["role"] != "admin":
            return render_template("403.html"), 403
        return view(**kwargs)

    return wrapped_view


@auth.route("/login", methods=["GET", "POST"])
def login():
    if g.user is not None:
        return redirect(url_for("web.import_data"))

    if request.method == "POST":
        username = request.form.get("username", "").strip().lower()
        password = request.form.get("password", "")
        db = database()

        if not db.available:
            flash("Database tidak tersedia. Login belum dapat diproses.", "error")
        else:
            user = db.find_user_by_username(username)
            if (
                user is None
                or not user["is_active"]
                or not check_password_hash(user["password_hash"], password)
            ):
                flash("Username atau password tidak benar.", "error")
            else:
                session.clear()
                session["user_id"] = user["id"]
                db.record_login(user["id"])
                next_url = request.args.get("next", "")
                if next_url and is_safe_redirect(next_url):
                    return redirect(next_url)
                return redirect(url_for("web.import_data"))

    return render_template("login.html")


@auth.post("/logout")
def logout():
    session.clear()
    flash("Anda telah keluar dari aplikasi.", "success")
    return redirect(url_for("auth.login"))


@auth.route("/admin/users", methods=["GET", "POST"])
@admin_required
def users():
    db = database()
    if not db.available:
        flash("Database tidak tersedia. Akun tidak dapat dikelola.", "error")
        return render_template("users.html", users=[])

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        username = request.form.get("username", "").strip().lower()
        role = request.form.get("role", "operator").strip().lower()
        password = request.form.get("password", "")
        password_confirmation = request.form.get("password_confirmation", "")

        error = None
        if len(name) < 3 or len(name) > 120:
            error = "Nama harus terdiri dari 3 sampai 120 karakter."
        elif not re.fullmatch(r"[a-z0-9._-]{3,80}", username):
            error = (
                "Username minimal 3 karakter dan hanya boleh berisi huruf kecil, "
                "angka, titik, garis bawah, atau tanda minus."
            )
        elif role not in {"admin", "operator"}:
            error = "Role pengguna tidak valid."
        elif len(password) < 8:
            error = "Password minimal terdiri dari 8 karakter."
        elif password != password_confirmation:
            error = "Konfirmasi password tidak cocok."

        if error:
            flash(error, "error")
        else:
            try:
                db.create_user(
                    name,
                    username,
                    generate_password_hash(password),
                    role,
                )
                flash(f"Akun {username} berhasil dibuat.", "success")
                return redirect(url_for("auth.users"))
            except ValueError as exc:
                flash(str(exc), "error")

    return render_template("users.html", users=db.list_users())
