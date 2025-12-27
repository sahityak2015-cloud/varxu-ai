import os, sqlite3
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
    <h2 style='font-family:system-ui;color:#0b0f19;'>Varxu AI</h2>
    <p>Created by Sahitya Kumar</p>
    <a href="/login">Login</a> | <a href="/signup">Signup</a> | <a href="/admin">Admin Panel</a>
    """

# ================= SIGNUP =================
@app.route("/signup", methods=["GET","POST"])
def signup():
    if request.method=="POST":
        u=request.form["username"]
        p=request.form["password"]
        con=db(); cur=con.cursor()
        try:
            cur.execute("INSERT INTO users(username,password) VALUES(?,?)",(u,p))
            con.commit()
            return redirect("/login")
        except:
            return "<h3>User already exists</h3><a href='/signup'>Go Back</a>"
        finally:
            con.close()
    return """
    <h2>Signup - Varxu AI</h2>
    <form method="post">
      <input name="username" placeholder="Username"><br><br>
      <input name="password" type="password" placeholder="Password"><br><br>
      <button>Create Account</button>
    </form>
    <br><a href="/login">Already have an account? Login</a>
    """

# ================= LOGIN =================
@app.route("/login", methods=["GET","POST"])
def login():
    if request.method=="POST":
        u=request.form["username"]
        p=request.form["password"]
        con=db(); cur=con.cursor()
        cur.execute("SELECT * FROM users WHERE username=? AND password=?",(u,p))
        user=cur.fetchone(); con.close()
        if user:
            session["user"]=u
            return redirect("/chat-ui")
        return "<h3>Invalid login</h3><a href='/login'>Go Back</a>"
    return """
    <h2>Login - Varxu AI</h2>
    <form method="post">
      <input name="username" placeholder="Username"><br><br>
      <input name="password" type="password" placeholder="Password"><br><br>
      <button>Login</button>
    </form>
    <br><a href="/signup">No account? Signup</a>
    """

# ================= CHAT UI =================
@app.route("/chat-ui")
def chat_ui():
    if "user" not in session:
        return redirect("/login")
    user=session["user"]
    return f"""
<!DOCTYPE html>
<html>
<head>
<title>Varxu AI</title>
<style>
body{{margin:0;font-family:system-ui;background:#0b0f19;color:white;}}
.container{{display:flex;height:100vh;}}
.sidebar{{width:250px;background:#020617;padding:20px;}}
.main{{flex:1;display:flex;flex-direction:column;}}
.chat{{flex:1;padding:20px;overflow-y:auto;}}
.msg{{max-width:70%;padding:12px 18px;margin:10px 0;border-radius:15px;}}
.user{{margin-left:auto;background:#2563eb;}}
.ai{{margin-right:auto;background:#1e293b;}}
.input-box{{display:flex;padding:10px;background:#020617;}}
textarea{{flex:1;padding:12px;border-radius:10px;background:#0b0f19;color:white;border:none;resize:none;}}
button.send{{width:50px;height:50px;border-radius:50%;background:#2563eb;color:white;border:none;cursor:pointer;margin-left:10px;}}
</style>
</head>
<body>
<div class="container">
  <div class="sidebar">
    <h2>VAR<span style="color:#3b82f6;">XU</span> AI</h2>
    <p>User: {user}<br>Creator: Sahitya Kumar</p>
    <input type="file" id="file" onchange="uploadFile()">
    <br><br><a href='/logout' style='color:#3b82f6;'>Logout</a>
  </div>
  <div class="main">
    <div id="chat" class="chat">
      <div class="ai msg">👋 Hello! I am Varxu AI.</div>
    </div>
    <div class="input-box">
      <textarea id="msg" rows="2" placeholder="Type a message..."></textarea>
      <button class="send" onclick="sendMessage()">➤</button>
    </div>
  </div>
</div>

<script>
const chat=document.getElementById("chat");
const msg=document.getElementById("msg");

function addMessage(role,text){
  let d=document.createElement("div");
  d.className="msg "+role;
  chat.appendChild(d);
  chat.scrollTop=chat.scrollHeight;
  if(role==="ai"){typeWriter(d,text);}
  else{d.innerText=text;}
}

function typeWriter(element,text,index=0){
  element.innerText="";
  let i=0;
  let interval=setInterval(()=>{
    element.innerText+=text.charAt(i);
    i++;
    chat.scrollTop=chat.scrollHeight;
    if(i>=text.length) clearInterval(interval);
  },25);
}

async function sendMessage(){
  let t=msg.value.trim(); if(!t) return;
  addMessage("user",t);
  msg.value="";
  let typing=document.createElement("div");
  typing.className="msg ai";
  typing.innerText="Varxu AI is typing...";
  chat.appendChild(typing);
  chat.scrollTop=chat.scrollHeight;

  let r=await fetch("/chat",{method:"POST",
          headers:{"Content-Type":"application/json"},
          body:JSON.stringify({message:t})});
  let d=await r.json();
  chat.removeChild(typing);
  addMessage("ai",d.reply);
}

// Optional: Voice output
function speak(text){
  let u=new SpeechSynthesisUtterance(text);
  u.lang="en-IN";
  speechSynthesis.speak(u);
}

</script>


# ================= CHAT API =================
@app.route("/chat", methods=["POST"])
def chat():
    if "user" not in session:
        return jsonify({"reply":"Login required"})
    user=session["user"]
    msg=request.json.get("message","")
    res=client.responses.create(model="gpt-4.1-mini",input=msg)
    reply=res.output_text
    con=db(); cur=con.cursor()
    cur.execute("INSERT INTO chats(username,message,reply) VALUES(?,?,?)",(user,msg,reply))
    con.commit(); con.close()
    return jsonify({"reply":reply})

# ================= FILE UPLOAD =================
@app.route("/upload",methods=["POST"])
def upload():
    if "user" not in session: return jsonify({"status":"Login required"})
    f=request.files.get("file")
    text=""
    if f.filename.endswith(".pdf"):
        reader=PdfReader(f)
        for p in reader.pages: text+=p.extract_text() or ""
    else:
        text=f.read().decode("utf-8")
    con=db(); cur=con.cursor()
    cur.execute("INSERT INTO chats(username,message,reply) VALUES(?,?,?)",(session["user"],"[Uploaded File]",text))
    con.commit(); con.close()
    return jsonify({"status":"ok"})

# ================= ADMIN PANEL =================
@app.route("/admin",methods=["GET","POST"])
def admin():
    if request.method=="POST":
        if request.form.get("u")==ADMIN_USER and request.form.get("p")==ADMIN_PASS:
            session["admin"]=True
            return redirect("/admin/dashboard")
        return "Wrong admin credentials"
    return """
<h3>Admin Login</h3>
<form method="post">
<input name="u" placeholder="Username"><br><br>
<input name="p" type="password" placeholder="Password"><br><br>
<button>Login</button>
</form>
"""

@app.route("/admin/dashboard")
def admin_dashboard():
    if not session.get("admin"): return redirect("/admin")
    con=db(); cur=con.cursor()
    cur.execute("SELECT username,COUNT(*) FROM chats GROUP BY username")
    data=cur.fetchall(); con.close()
    html="<h2>Admin Panel</h2><p>Created by Sahitya Kumar</p><ul>"
    for u,c in data: html+=f"<li>{u} : {c} chats</li>"
    html+="</ul><br><a href='/logout'>Logout</a>"
    return html

# ================= LOGOUT =================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ================= START =================
if __name__=="__main__":
    port=int(os.environ.get("PORT",10000))
    app.run(host="0.0.0.0",port=port)
