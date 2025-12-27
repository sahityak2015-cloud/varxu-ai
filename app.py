import os, sqlite3
from flask import Flask, request, jsonify, session, redirect
from openai import OpenAI

# ================= CONFIG =================
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
ADMIN_USER = "admin"
ADMIN_PASS = "admin123"

if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY missing")

app = Flask(__name__)
app.secret_key = "varxu_secret_key"
client = OpenAI(api_key=OPENAI_API_KEY)

DB = "database.db"

# ================= DATABASE =================
def db(): return sqlite3.connect(DB)

def init_db():
    con = db(); cur = con.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS chats(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        message TEXT,
        reply TEXT
    )""")
    con.commit(); con.close()

init_db()

# ================= HOME =================
@app.route("/")
def home():
    if "user" in session:
        return redirect("/chat-ui")
    return """
    <h2>Varxu AI</h2>
    <p>Created by Sahitya Kumar</p>
    <a href="/login">Login</a> | <a href="/signup">Signup</a> | <a href="/admin">Admin Panel</a>
    """

# ================= SIGNUP =================
@app.route("/signup", methods=["GET","POST"])
def signup():
    if request.method == "POST":
        u = request.form["username"]
        p = request.form["password"]
        con = db(); cur = con.cursor()
        try:
            cur.execute("INSERT INTO users(username,password) VALUES(?,?)",(u,p))
            con.commit()
            return redirect("/login")
        except:
            return "User already exists"
        finally:
            con.close()
    return """
    <h3>Signup</h3>
    <form method="post">
    <input name="username" placeholder="Username"><br><br>
    <input name="password" type="password" placeholder="Password"><br><br>
    <button>Create Account</button>
    </form>
    """

# ================= LOGIN =================
@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        u = request.form["username"]
        p = request.form["password"]
        con=db(); cur=con.cursor()
        cur.execute("SELECT * FROM users WHERE username=? AND password=?",(u,p))
        user = cur.fetchone(); con.close()
        if user:
            session["user"] = u
            return redirect("/chat-ui")
        return "Invalid login"
    return """
    <h3>Login</h3>
    <form method="post">
    <input name="username"><br><br>
    <input name="password" type="password"><br><br>
    <button>Login</button>
    </form>
    """

# ================= CHAT UI (Normal User) =================
@app.route("/chat-ui")
def chat_ui():
    if "user" not in session:
        return redirect("/login")
    return f"""
    <h2>Varxu AI</h2>
    <p>User: {session['user']} | Created by Sahitya Kumar</p>
    <textarea id="msg"></textarea><br>
    <button onclick="send()">Send</button>
    <pre id="chat"></pre>

    <script>
    async function send(){{
      let m=document.getElementById("msg").value;
      let r=await fetch("/chat",{{method:"POST",headers:{{"Content-Type":"application/json"}},body:JSON.stringify({{message:m}})}});
      let d=await r.json();
      document.getElementById("chat").innerText+=
        "\\nYou: "+m+"\\nAI: "+d.reply+"\\n";
    }}
    </script>
    """

# ================= CHAT API =================
@app.route("/chat", methods=["POST"])
def chat():
    if "user" not in session:
        return jsonify({"reply":"Login required"})
    user = session["user"]
    msg = request.json.get("message","")
    res = client.responses.create(
        model="gpt-4.1-mini",
        input=msg
    )
    reply = res.output_text
    con=db(); cur=con.cursor()
    cur.execute("INSERT INTO chats(username,message,reply) VALUES(?,?,?)",(user,msg,reply))
    con.commit(); con.close()
    return jsonify({"reply":reply})

# ================= ADMIN LOGIN =================
@app.route("/admin", methods=["GET","POST"])
def admin():
    if request.method=="POST":
        if request.form.get("u")==ADMIN_USER and request.form.get("p")==ADMIN_PASS:
            session["admin"]=True
            return redirect("/admin/dashboard")
        return "Wrong admin credentials"
    return """
    <h3>Admin Login</h3>
    <form method="post">
    <input name="u"><br><br>
    <input name="p" type="password"><br><br>
    <button>Login</button>
    </form>
    """

# ================= ADMIN DASHBOARD =================
@app.route("/admin/dashboard")
def admin_dashboard():
    if not session.get("admin"):
        return redirect("/admin")
    con=db(); cur=con.cursor()
    cur.execute("SELECT username,COUNT(*) FROM chats GROUP BY username")
    data = cur.fetchall()
    cur.close()
    html="<h2>Admin Panel</h2><p>Created by Sahitya Kumar</p><ul>"
    for u,c in data:
        html+=f"<li>{u} : {c} chats</li>"
    html+="</ul>"
    return html

# ================= LOGOUT =================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ================= START =================
if __name__ == "__main__":
    port=int(os.environ.get("PORT",10000))
    app.run(host="0.0.0.0",port=port)
