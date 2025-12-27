import os
import webbrowser
from flask import Flask, request, jsonify, session
from openai import OpenAI
from PyPDF2 import PdfReader

# ================= CONFIG =================
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY is not set")

app = Flask(__name__)
app.secret_key = "varxu_secret_key"

client = OpenAI(api_key=OPENAI_API_KEY)

# ================= UI =================
HTML = """<!DOCTYPE html>
<html>
<head>
<title>Varxu AI</title>
<style>
body{margin:0;background:#0b0f19;font-family:system-ui;color:white}
.hidden{display:none}
.center{display:flex;align-items:center;justify-content:center;height:100vh;flex-direction:column}
.brand{font-size:40px;font-weight:800}
.brand span{color:#3b82f6}
.box{background:#020617;padding:25px;border-radius:14px}
input,textarea{width:100%;padding:12px;margin-top:10px;border:none;border-radius:10px;background:#0b0f19;color:white}
button{margin-top:12px;padding:12px;width:100%;border:none;border-radius:10px;background:#2563eb;color:white;cursor:pointer}
.container{display:flex;height:100vh}
.sidebar{width:240px;background:#020617;padding:20px}
.main{flex:1;display:flex;flex-direction:column}
.chat{flex:1;padding:25px;overflow-y:auto}
.msg{max-width:70%;padding:14px 18px;margin:12px 0;border-radius:16px}
.user{margin-left:auto;background:#2563eb}
.ai{margin-right:auto;background:#1e293b}
.system{margin:10px auto;background:#020617;color:#94a3b8;font-size:13px;padding:10px;border-radius:10px}
.input-box{display:flex;padding:15px;background:#020617;align-items:center}
.send{width:46px;height:46px;margin-left:8px;border-radius:50%;background:#2563eb;display:flex;align-items:center;justify-content:center;cursor:pointer}
</style>
</head>

<body>
<div id="login" class="center">
  <div class="box">
    <div class="brand">VAR<span>XU</span> AI</div>
    <p style="color:#94a3b8">Created by Sahitya Kumar</p>
    <input id="user" placeholder="Enter your name" />
    <button onclick="login()">Start Chat</button>
  </div>
</div>

<div id="app" class="container hidden">
  <div class="sidebar">
    <div class="brand">VAR<span>XU</span></div>
    <p style="color:#94a3b8;font-size:13px">
      User: <b id="uname"></b><br>
      Creator: Sahitya Kumar<br>
      Version: 1.3
    </p>
    <input type="file" id="file" onchange="upload()" />
  </div>

  <div class="main">
    <div id="chat" class="chat">
      <div class="system">👋 I am Varxu AI, created by <b>Sahitya Kumar</b></div>
    </div>

    <div class="input-box">
      <textarea id="msg" placeholder="Message Varxu AI..."></textarea>
      <div class="send" onclick="send()">➤</div>
      <div class="send" onclick="voice()">🎤</div>
      <div class="send" onclick="toggle()">🔊</div>
    </div>
  </div>
</div>

<script>
let speakOn=true;
const chat=document.getElementById("chat");
const msg=document.getElementById("msg");

function login(){
  let u=document.getElementById("user").value.trim();
  if(!u) return;
  fetch("/login",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({user:u})});
  document.getElementById("uname").innerText=u;
  document.getElementById("login").classList.add("hidden");
  document.getElementById("app").classList.remove("hidden");
}

function add(role,text){
  let d=document.createElement("div");
  d.className="msg "+role;
  d.innerText=text;
  chat.appendChild(d);
  chat.scrollTop=chat.scrollHeight;
}

async function send(){
  let t=msg.value.trim(); if(!t) return;
  add("user",t); msg.value="";
  let r=await fetch("/chat",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({message:t})});
  let d=await r.json();
  add("ai",d.reply);
}

function upload(){
  let f=document.getElementById("file").files[0];
  let fd=new FormData(); fd.append("file",f);
  fetch("/upload",{method:"POST",body:fd});
}

function voice(){
  if("webkitSpeechRecognition" in window){
    let r=new webkitSpeechRecognition();
    r.lang="en-IN";
    r.onresult=e=>msg.value+=e.results[0][0].transcript;
    r.start();
  }
}
function toggle(){speakOn=!speakOn;}
</script>
</body>
</html>"""

# ================= ROUTES =================
@app.route("/")
def home():
    return HTML

@app.route("/login", methods=["POST"])
def login():
    session.clear()
    session["history"] = [
        {"role": "system", "content": "You are Varxu AI, created by Sahitya Kumar."}
    ]
    return "ok"

@app.route("/upload", methods=["POST"])
def upload():
    f = request.files["file"]
    text = ""

    if f.filename.endswith(".pdf"):
        reader = PdfReader(f)
        for p in reader.pages:
            text += p.extract_text() or ""
    else:
        text = f.read().decode("utf-8")

    session["history"].append({
        "role": "system",
        "content": "User uploaded file content:\n" + text[:3000]
    })
    return jsonify({"status": "ok"})

@app.route("/chat", methods=["POST"])
def chat():
    if "history" not in session:
        session["history"] = [
            {"role": "system", "content": "You are Varxu AI, created by Sahitya Kumar."}
        ]

    user_msg = request.json.get("message", "")
    session["history"].append({"role": "user", "content": user_msg})

    response = client.responses.create(
        model="gpt-4.1-mini",
        input=session["history"]
    )

    reply = response.output_text
    session["history"].append({"role": "assistant", "content": reply})

    return jsonify({"reply": reply})

# ================= START =================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
