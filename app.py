from flask import Flask, render_template, request, redirect, session
from cryptography.fernet import Fernet
import os
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "secure123"   # session key
# Ensure notes file exists
if not os.path.exists("notes.txt"):
    open("notes.txt", "wb").close()
    
# ---------- KEY MANAGEMENT ----------
def load_key():
    if not os.path.exists("secret.key"):
        key = Fernet.generate_key()
        with open("secret.key", "wb") as f:
            f.write(key)

    return open("secret.key", "rb").read()

def encrypt_note(note):
    key = load_key()
    f = Fernet(key)
    return f.encrypt(note.encode())

def decrypt_note(note):
    key = load_key()
    f = Fernet(key)
    return f.decrypt(note).decode()

# ---------- LOGIN ----------
USERNAME = "admin"
PASSWORD_HASH = generate_password_hash("1234")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = request.form["username"]
        pw = request.form["password"]

        if user == USERNAME and check_password_hash(PASSWORD_HASH, pw):
            session["user"] = user
            return redirect("/")
        else:
            return render_template("login.html", error="Invalid credentials")

    return render_template("login.html")

# ---------- LOGOUT ----------
@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/login")

# ---------- HOME ----------
@app.route("/", methods=["GET", "POST"])
def home():

    if "user" not in session:
        return redirect("/login")

    notes = []

    if request.method == "POST":

        # DELETE NOTE
        if "delete" in request.form:
            index = int(request.form["delete"])

            if os.path.exists("notes.txt"):
                with open("notes.txt", "rb") as f:
                    lines = f.readlines()

                lines.pop(index)

                with open("notes.txt", "wb") as f:
                    f.writelines(lines)

        # ADD NOTE
        else:
            note = request.form["note"]

            timestamp = datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )

            full_note = f"{timestamp} | {note}"

            encrypted = encrypt_note(full_note)

            with open("notes.txt", "ab") as f:
                f.write(encrypted + b"\n")

    search_query = request.args.get("search", "")

    if os.path.exists("notes.txt"):
        with open("notes.txt", "rb") as f:
            for i, line in enumerate(f):
                try:
                    text = decrypt_note(line.strip())

                    if search_query.lower() in text.lower():
                        notes.append((i, text))

                except Exception:
                    # Skip corrupted or old encrypted notes
                    continue

    return render_template(
        "index.html",
        notes=notes,
        search=search_query
    )

if __name__ == "__main__":
    app.run(debug=True)