import os
from flask import Flask, request, jsonify, session, redirect
from openai import OpenAI
from PyPDF2 import PdfReader

# ================= CONFIG =================
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
ADMIN_USER = "admin"
ADMIN_PASS = "admin123"

if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY missing")

app = Flask(__name__)
app.secret_key = "varxu_secret_key"
client = OpenAI(api_key=OPENAI_API_KEY)

# In-memory storage (temporary)
users = {}
chat_logs = []

# ================= MAIN UI =================
@app.route("/")
def home():
    return """
    <h2>Varxu AI is running</h2>
    <p>Created by Sahitya Kumar</p>
    <a href="/admin">Admin Panel</a>
    """

# ================= CHAT =================
@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    msg = data.get("message", "").strip()
    user = session.get("user", "guest")

    if not msg:
        return jsonify({"reply": "Say something 🙂"})

    response = client.responses.create(
        model="gpt-4.1-mini",
        input=msg
    )

    reply = response.output_text

    users[user] = users.get(user, 0) + 1
    chat_logs.append({"user": user, "q": msg, "a": reply})

    return jsonify({"reply": reply})

# ================= ADMIN LOGIN =================
@app.route("/admin", methods=["GET", "POST"])
def admin():
    if request.method == "POST":
        u = request.form.get("username")
        p = request.form.get("password")

        if u == ADMIN_USER and p == ADMIN_PASS:
            session["admin"] = True
            return redirect("/admin/dashboard")
        return "Invalid credentials"

    return """
    <h2>Admin Login</h2>
    <form method="post">
      <input name="username" placeholder="Username"><br><br>
      <input name="password" type="password" placeholder="Password"><br><br>
      <button>Login</button>
    </form>
    """

# ================= ADMIN DASHBOARD =================
@app.route("/admin/dashboard")
def admin_dashboard():
    if not session.get("admin"):
        return redirect("/admin")

    total_users = len(users)
    total_chats = len(chat_logs)

    recent = chat_logs[-5:]

    html = f"""
    <h2>Varxu AI Admin Panel</h2>
    <p>Created by Sahitya Kumar</p>
    <hr>
    <b>Total Users:</b> {total_users}<br>
    <b>Total Chats:</b> {total_chats}<br><br>

    <h3>Recent Chats</h3>
    <ul>
    """

    for c in recent:
        html += f"<li><b>{c['user']}:</b> {c['q']} → {c['a']}</li>"

    html += """
    </ul>
    <br><a href="/admin/logout">Logout</a>
    """

    return html

# ================= ADMIN LOGOUT =================
@app.route("/admin/logout")
def admin_logout():
    session.pop("admin", None)
    return redirect("/admin")

# ================= START =================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
