from flask import Blueprint, render_template, request, redirect, url_for, session
import psycopg2
from config import Config

auth_bp = Blueprint("auth", __name__)


def get_db():
    return psycopg2.connect(
        host=Config.DB_HOST,
        port=Config.DB_PORT,
        database=Config.DB_NAME,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD
    )


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("main.index"))

    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        try:
            conn = get_db()
            cur = conn.cursor()
            cur.execute(
                'SELECT id, username FROM users WHERE username = %s AND password = %s',
                (username, password)
            )
            user = cur.fetchone()
            conn.close()
            if user:
                session["user_id"] = user[0]
                session["username"] = user[1]
                return redirect(url_for("main.index"))
            else:
                error = "Identifiants incorrects."
        except Exception as e:
            error = "Erreur de connexion à la base de données."

    return render_template("login.html", error=error)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if "user_id" in session:
        return redirect(url_for("main.index"))

    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        password_confirm = request.form.get("password_confirm", "")

        if not username or not password:
            error = "Tous les champs sont obligatoires."
        elif len(username) < 3:
            error = "Le nom d'utilisateur doit faire au moins 3 caractères."
        elif len(password) < 6:
            error = "Le mot de passe doit faire au moins 6 caractères."
        elif password != password_confirm:
            error = "Les mots de passe ne correspondent pas."
        else:
            try:
                conn = get_db()
                cur = conn.cursor()
                cur.execute('SELECT id FROM users WHERE username = %s', (username,))
                if cur.fetchone():
                    error = "Ce nom d'utilisateur est déjà pris."
                else:
                    cur.execute(
                        'INSERT INTO users (username, password) VALUES (%s, %s)',
                        (username, password)
                    )
                    conn.commit()
                    conn.close()
                    return redirect(url_for("auth.login"))
                conn.close()
            except Exception as e:
                error = "Erreur de connexion à la base de données."
                print(e)

    return render_template("register.html", error=error)


@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("main.index"))