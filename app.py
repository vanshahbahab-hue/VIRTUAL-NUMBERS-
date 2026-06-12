from flask import Flask, render_template_string, request, redirect, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
import random
import qrcode
from io import BytesIO
import base64

app = Flask(__name__)
app.secret_key = "virtual_secret_key_2024"

# Database
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(basedir, "virtual_numbers.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Owner config
OWNER_ID = 8586849798
BOT_TOKEN = "8679581798:AAGZtycapDdwpwYR8ro5M4xZNFiIR4QuetI"

# ============ DATABASE MODELS ============
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(100), nullable=True)
    password = db.Column(db.String(200), nullable=True)
    balance = db.Column(db.Float, default=0)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class VirtualNumber(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.String(50), unique=True, nullable=False)
    country = db.Column(db.String(50), nullable=False)
    price = db.Column(db.Float, nullable=False)
    is_sold = db.Column(db.Boolean, default=False)
    sold_to = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    sold_at = db.Column(db.DateTime, nullable=True)

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    transaction_id = db.Column(db.String(50), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    qr_amount = db.Column(db.Float, nullable=True)
    status = db.Column(db.String(20), default='Pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.String(20), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    number_id = db.Column(db.Integer, db.ForeignKey('virtual_number.id'), nullable=False)
    number = db.Column(db.String(50), nullable=False)
    country = db.Column(db.String(50), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='Completed')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Create tables
with app.app_context():
    db.create_all()
    
    admin = User.query.filter_by(username="ADMIN").first()
    if not admin:
        admin = User(username="ADMIN", email="admin@virtual.com", password="ADMIN123", is_admin=True, balance=0)
        db.session.add(admin)
        db.session.commit()
    
    numbers_data = {
        "USA": {"price": 320, "flag": "https://i.ibb.co/pv1YDt7X/photo-AQADIh-Br-G81-GYFV.jpg", "prefix": "+1"},
        "CANADA": {"price": 365, "flag": "https://i.ibb.co/DHJcy546/photo-AQADIx-Br-G81-GYFVy.jpg", "prefix": "+1"},
        "UAE": {"price": 385, "flag": "https://i.ibb.co/cS23Q3S3/photo-AQADJBBr-G81-GYFVy.jpg", "prefix": "+971"},
        "AUSTRALIA": {"price": 325, "flag": "https://i.ibb.co/CKNrdykP/photo-AQADIRBr-G81-GYFVy.jpg", "prefix": "+61"}
    }
    
    for country, data in numbers_data.items():
        existing = VirtualNumber.query.filter_by(country=country).count()
        if existing < 25:
            for i in range(existing, 25):
                number = f"{data['prefix']}{random.randint(1000000000, 9999999999)}"
                vn = VirtualNumber(number=number, country=country, price=data['price'], is_sold=False)
                db.session.add(vn)
    db.session.commit()

# ============ HELPERS ============
def generate_transaction_id():
    return f"TXN{random.randint(100000, 999999)}"

def generate_random_paise():
    return random.randint(1, 99)

def generate_qr(amount, transaction_id):
    upi_id = "v76009423@oksbi"
    upi_link = f"upi://pay?pa={upi_id}&pn=VNR&am={amount}&cu=INR&tn={transaction_id}"
    qr = qrcode.QRCode(version=1, box_size=10, border=2)
    qr.add_data(upi_link)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()

# ============ HTML TEMPLATES ============
LOGIN_HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Virtual Numbers | Login</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; font-family: 'Orbitron', monospace; }
        body { min-height: 100vh; background: linear-gradient(135deg, #0a0a2a, #1a0a3a, #2a1a4a); display: flex; justify-content: center; align-items: center; position: relative; overflow: hidden; }
        body::before { content: ''; position: absolute; width: 200%; height: 200%; background: radial-gradient(circle, rgba(128,0,255,0.15) 0%, transparent 60%); animation: rotate 25s linear infinite; z-index: 0; }
        @keyframes rotate { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
        .login-card { position: relative; z-index: 1; background: rgba(10, 10, 42, 0.95); backdrop-filter: blur(15px); border-radius: 30px; padding: 45px 40px; width: 100%; max-width: 480px; border: 1px solid rgba(128,0,255,0.3); }
        .logo { text-align: center; margin-bottom: 25px; }
        .logo img { max-width: 200px; }
        .sub { color: rgba(255,255,255,0.5); text-align: center; font-size: 12px; margin-bottom: 30px; }
        .tab { display: flex; margin-bottom: 30px; border-bottom: 1px solid rgba(128,0,255,0.3); }
        .tab-btn { flex: 1; background: none; border: none; padding: 12px; color: rgba(255,255,255,0.5); font-size: 16px; font-weight: bold; cursor: pointer; }
        .tab-btn.active { color: #aa00ff; border-bottom: 2px solid #aa00ff; }
        .form-container { display: none; }
        .form-container.active { display: block; }
        .input-group { margin-bottom: 22px; }
        .input-group input { width: 100%; padding: 15px 20px; background: rgba(255,255,255,0.05); border: 1px solid rgba(128,0,255,0.3); border-radius: 15px; color: white; font-size: 14px; }
        .input-group input:focus { outline: none; border-color: #aa00ff; }
        .btn { width: 100%; padding: 15px; background: linear-gradient(135deg, #aa00ff, #6600cc); border: none; border-radius: 15px; color: white; font-size: 16px; font-weight: bold; cursor: pointer; margin-top: 10px; }
        .btn:hover { transform: translateY(-2px); }
        .error { background: rgba(255,51,102,0.2); border: 1px solid #ff3366; border-radius: 12px; padding: 12px; margin-bottom: 20px; text-align: center; color: #ff6b6b; font-size: 12px; }
        .success { background: rgba(0,255,204,0.15); border: 1px solid #00ffcc; border-radius: 12px; padding: 12px; margin-bottom: 20px; text-align: center; color: #00ffcc; }
        .divider { text-align: center; margin: 20px 0; color: rgba(255,255,255,0.3); font-size: 11px; }
        .footer { text-align: center; margin-top: 30px; font-size: 9px; color: rgba(255,255,255,0.25); }
    </style>
</head>
<body>
    <div class="login-card">
        <div class="logo"><img src="https://i.ibb.co/4cHCQB4/photo-AQADKx-Br-G81-GYFV.jpg" alt="Virtual Numbers"></div>
        <p class="sub">VIRTUAL NUMBERS FOR VERIFICATION</p>
        
        <div class="tab">
            <button class="tab-btn active" onclick="switchTab('login')">LOGIN</button>
            <button class="tab-btn" onclick="switchTab('register')">REGISTER</button>
        </div>
        
        {% if error %}<div class="error">{{ error }}</div>{% endif %}
        {% if success %}<div class="success">{{ success }}</div>{% endif %}
        
        <div id="loginForm" class="form-container active">
            <form method="POST" action="/login">
                <div class="input-group"><input type="text" name="username" placeholder="USERNAME" required></div>
                <div class="input-group"><input type="password" name="password" placeholder="PASSWORD" required></div>
                <button type="submit" class="btn">LOGIN</button>
            </form>
        </div>
        
        <div id="registerForm" class="form-container">
            <form method="POST" action="/register">
                <div class="input-group"><input type="text" name="username" placeholder="USERNAME" required></div>
                <div class="input-group"><input type="email" name="email" placeholder="EMAIL" required></div>
                <div class="input-group"><input type="password" name="password" placeholder="PASSWORD" required></div>
                <button type="submit" class="btn">REGISTER</button>
            </form>
        </div>
        
        <div class="divider">OR</div>
        <a href="/google-login"><button class="btn" style="background:rgba(255,255,255,0.1);">SIGN IN WITH GOOGLE</button></a>
        
        <div class="footer">2025 VIRTUAL NUMBERS</div>
    </div>
    
    <script>
        function switchTab(tab) {
            var loginForm = document.getElementById('loginForm');
            var registerForm = document.getElementById('registerForm');
            var btns = document.querySelectorAll('.tab-btn');
            loginForm.classList.remove('active');
            registerForm.classList.remove('active');
            for(var i = 0; i < btns.length; i++) {
                btns[i].classList.remove('active');
            }
            if(tab === 'login') {
                loginForm.classList.add('active');
                btns[0].classList.add('active');
            } else {
                registerForm.classList.add('active');
                btns[1].classList.add('active');
            }
        }
    </script>
</body>
</html>
"""

# ============ FLASK ROUTES ============
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect('/dashboard')
    return LOGIN_HTML

@app.route('/health')
def health():
    return "OK", 200

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    user = User.query.filter_by(username=username, password=password).first()
    if user:
        session['user_id'] = user.id
        session['username'] = user.username
        session['is_admin'] = user.is_admin
        return redirect('/admin' if user.is_admin else '/dashboard')
    return LOGIN_HTML.replace('{% if error %}', '<div class="error">Invalid credentials!</div>')

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')
    
    existing = User.query.filter_by(username=username).first()
    if existing:
        return LOGIN_HTML.replace('{% if error %}', '<div class="error">Username exists!</div>')
    
    new_user = User(username=username, email=email, password=password, balance=0)
    db.session.add(new_user)
    db.session.commit()
    return LOGIN_HTML.replace('{% if success %}', '<div class="success">Account created! Please login.</div>')

@app.route('/google-login')
def google_login():
    return redirect('/')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect('/')
    user = User.query.get(session['user_id'])
    numbers = VirtualNumber.query.filter_by(is_sold=False).all()
    orders = Order.query.filter_by(user_id=user.id).order_by(Order.created_at.desc()).limit(10).all()
    
    return render_template_string('''
<!DOCTYPE html>
<html>
<head><title>Dashboard | Virtual Numbers</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
*{margin:0;padding:0;box-sizing:border-box;font-family:'Orbitron',monospace;}
body{background:linear-gradient(135deg,#0a0a2a,#1a0a3a,#2a1a4a);}
.navbar{background:rgba(10,10,42,0.95);padding:15px 30px;display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid #aa00ff;}
.logo img{height:50px;}
.wallet{background:linear-gradient(135deg,#aa00ff,#6600cc);padding:10px 25px;border-radius:30px;color:white;font-weight:bold;}
.menu-btn{background:none;border:none;cursor:pointer;display:flex;flex-direction:column;gap:5px;}
.menu-btn span{width:25px;height:2px;background:#aa00ff;}
.sidebar{position:fixed;top:0;right:-300px;width:280px;height:100%;background:rgba(10,10,42,0.98);backdrop-filter:blur(15px);border-left:1px solid #aa00ff;padding:80px 20px 20px;transition:0.3s;z-index:200;}
.sidebar.active{right:0;}
.sidebar a{display:block;color:white;text-decoration:none;padding:15px;margin:10px 0;border-radius:10px;}
.sidebar a:hover{background:rgba(170,0,255,0.2);color:#aa00ff;}
.close-sidebar{position:absolute;top:20px;right:20px;font-size:24px;cursor:pointer;color:#aa00ff;}
.overlay{position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.5);display:none;z-index:150;}
.container{padding:30px;max-width:1400px;margin:0 auto;}
.welcome{color:#aa00ff;margin-bottom:30px;font-size:24px;}
.welcome span{color:white;}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:20px;margin-bottom:40px;}
.stat-card{background:rgba(255,255,255,0.05);border:1px solid rgba(170,0,255,0.3);border-radius:20px;padding:25px;text-align:center;}
.stat-card h3{color:rgba(255,255,255,0.6);font-size:12px;}
.stat-card .value{color:#aa00ff;font-size:32px;font-weight:bold;}
.section-title{color:#aa00ff;margin:30px 0 20px;font-size:20px;}
.countries{display:grid;grid-template-columns:repeat(4,1fr);gap:25px;margin-bottom:40px;}
@media(max-width:1000px){.countries{grid-template-columns:repeat(2,1fr);}}
@media(max-width:600px){.countries{grid-template-columns:1fr;}}
.country-section{background:rgba(255,255,255,0.05);border:1px solid rgba(170,0,255,0.3);border-radius:20px;padding:20px;}
.country-header{display:flex;align-items:center;gap:15px;margin-bottom:20px;padding-bottom:15px;border-bottom:1px solid rgba(170,0,255,0.3);}
.country-header img{width:40px;height:30px;object-fit:cover;border-radius:5px;}
.country-header h3{color:#aa00ff;font-size:18px;}
.numbers-list{max-height:500px;overflow-y:auto;}
.number-item{display:flex;justify-content:space-between;align-items:center;padding:12px;margin:8px 0;background:rgba(0,0,0,0.3);border-radius:10px;}
.number-info{display:flex;align-items:center;gap:10px;}
.number-info img{width:25px;height:18px;object-fit:cover;border-radius:3px;}
.number-info span{color:white;font-size:13px;}
.price-detail{font-size:10px;color:rgba(255,255,255,0.5);margin-top:5px;}
.number-price{color:#aa00ff;font-weight:bold;font-size:14px;}
.buy-btn{background:linear-gradient(135deg,#aa00ff,#6600cc);border:none;padding:6px 15px;border-radius:20px;color:white;font-weight:bold;cursor:pointer;font-size:12px;}
.table-container{background:rgba(255,255,255,0.05);border-radius:16px;overflow-x:auto;}
table{width:100%;border-collapse:collapse;}
th,td{padding:12px;text-align:left;color:white;border-bottom:1px solid rgba(255,255,255,0.1);font-size:12px;}
th{color:#aa00ff;}
.modal{display:none;position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.85);justify-content:center;align-items:center;z-index:300;}
.modal-content{background:#0a0a2a;padding:35px;border-radius:25px;max-width:450px;width:90%;border:1px solid #aa00ff;text-align:center;}
.modal-content h2{color:#aa00ff;margin-bottom:20px;}
.modal-content input{width:100%;padding:14px;margin:12px 0;background:rgba(255,255,255,0.08);border:1px solid rgba(170,0,255,0.3);border-radius:12px;color:white;}
.modal-content button{width:100%;padding:14px;background:linear-gradient(135deg,#aa00ff,#6600cc);border:none;border-radius:12px;color:white;font-weight:bold;cursor:pointer;margin:5px 0;}
.close-btn{background:rgba(255,255,255,0.1);}
#qrResult img{width:200px;margin:10px 0;}
.toast{position:fixed;bottom:30px;right:30px;background:#ff3366;color:white;padding:12px 20px;border-radius:10px;z-index:400;display:none;}
.toast.success{background:#00cc66;}
</style>
</head>
<body>
<div class="navbar"><div class="logo"><img src="https://i.ibb.co/4cHCQB4/photo-AQADKx-Br-G81-GYFV.jpg"></div><div style="display:flex;align-items:center;gap:20px;"><div class="wallet">💰 ₹{{ user.balance }}</div><button class="menu-btn" onclick="toggleSidebar()"><span></span><span></span><span></span></button></div></div>
<div class="sidebar" id="sidebar"><div class="close-sidebar" onclick="toggleSidebar()">X</div><a href="#" onclick="openAddCash()">ADD FUNDS</a><a href="/order-history">MY ORDERS</a><a href="/transaction-history">TRANSACTIONS</a><a href="#" onclick="showNotifications()">NOTIFICATIONS</a><a href="/logout">LOGOUT</a></div>
<div class="overlay" id="overlay" onclick="toggleSidebar()"></div>
<div id="toast" class="toast"></div>
<div class="container"><div class="welcome">WELCOME, <span>{{ user.username }}</span></div>
<div class="stats"><div class="stat-card"><h3>BALANCE</h3><div class="value">₹{{ user.balance }}</div></div><div class="stat-card"><h3>ORDERS</h3><div class="value">{{ orders|length }}</div></div></div>
<div class="countries">
<div class="country-section"><div class="country-header"><img src="https://i.ibb.co/pv1YDt7X/photo-AQADIh-Br-G81-GYFV.jpg"><h3>USA</h3></div><div class="numbers-list">{% for num in numbers if num.country == 'USA' %}<div class="number-item"><div class="number-info"><img src="https://i.ibb.co/pv1YDt7X/photo-AQADIh-Br-G81-GYFV.jpg"><span>{{ num.number }}</span><div class="price-detail">telegram, whatsapp, any app login</div></div><div class="number-price">₹{{ num.price }}</div><button class="buy-btn" onclick="buyNumber({{ num.id }}, {{ num.price }})">BUY</button></div>{% endfor %}</div></div>
<div class="country-section"><div class="country-header"><img src="https://i.ibb.co/DHJcy546/photo-AQADIx-Br-G81-GYFVy.jpg"><h3>CANADA</h3></div><div class="numbers-list">{% for num in numbers if num.country == 'CANADA' %}<div class="number-item"><div class="number-info"><img src="https://i.ibb.co/DHJcy546/photo-AQADIx-Br-G81-GYFVy.jpg"><span>{{ num.number }}</span><div class="price-detail">telegram, whatsapp, any app login</div></div><div class="number-price">₹{{ num.price }}</div><button class="buy-btn" onclick="buyNumber({{ num.id }}, {{ num.price }})">BUY</button></div>{% endfor %}</div></div>
<div class="country-section"><div class="country-header"><img src="https://i.ibb.co/cS23Q3S3/photo-AQADJBBr-G81-GYFVy.jpg"><h3>UAE</h3></div><div class="numbers-list">{% for num in numbers if num.country == 'UAE' %}<div class="number-item"><div class="number-info"><img src="https://i.ibb.co/cS23Q3S3/photo-AQADJBBr-G81-GYFVy.jpg"><span>{{ num.number }}</span><div class="price-detail">telegram, whatsapp, any app login</div></div><div class="number-price">₹{{ num.price }}</div><button class="buy-btn" onclick="buyNumber({{ num.id }}, {{ num.price }})">BUY</button></div>{% endfor %}</div></div>
<div class="country-section"><div class="country-header"><img src="https://i.ibb.co/CKNrdykP/photo-AQADIRBr-G81-GYFVy.jpg"><h3>AUSTRALIA</h3></div><div class="numbers-list">{% for num in numbers if num.country == 'AUSTRALIA' %}<div class="number-item"><div class="number-info"><img src="https://i.ibb.co/CKNrdykP/photo-AQADIRBr-G81-GYFVy.jpg"><span>{{ num.number }}</span><div class="price-detail">telegram, whatsapp, any app login</div></div><div class="number-price">₹{{ num.price }}</div><button class="buy-btn" onclick="buyNumber({{ num.id }}, {{ num.price }})">BUY</button></div>{% endfor %}</div></div>
</div>
<h3 class="section-title">RECENT ORDERS</h3>
<div class="table-container"><table><thead><tr><th>ORDER ID</th><th>NUMBER</th><th>COUNTRY</th><th>AMOUNT</th><th>STATUS</th><th>DATE</th></tr></thead><tbody>{% for o in orders %}<tr><td>{{ o.order_id }}</td><td>{{ o.number }}</td><td>{{ o.country }}</td><td>₹{{ o.amount }}</td><td style="color:#00ff00;">{{ o.status }}</td><td>{{ o.created_at.strftime('%Y-%m-%d') }}</td></tr>{% else %}<tr><td colspan="6">No orders yet</td></tr>{% endfor %}</tbody></table></div></div>
<div id="addCashModal" class="modal"><div class="modal-content"><h2>ADD FUNDS</h2><p style="color:#ffaa00;">Minimum Deposit: ₹349</p><input type="number" id="cashAmount" placeholder="AMOUNT (349-10000)" min="349" max="10000"><button onclick="generateQR()">GENERATE QR</button><button class="close-btn" onclick="closeAddCash()">CANCEL</button><div id="qrResult"></div></div></div>
<div id="notifModal" class="modal"><div class="modal-content"><h2>NOTIFICATIONS</h2><div id="notifContent" style="color:white;">Welcome to Virtual Numbers! Minimum deposit: ₹349</div><button class="close-btn" onclick="closeNotif()">CLOSE</button></div></div>
<script>
var userBalance = {{ user.balance }};
function showToast(msg, isSuccess) {
    var toast = document.getElementById('toast');
    toast.textContent = msg;
    toast.className = 'toast';
    if(isSuccess) { toast.className = 'toast success'; }
    toast.style.display = 'block';
    setTimeout(function() { toast.style.display = 'none'; }, 3000);
}
function toggleSidebar() {
    var sidebar = document.getElementById('sidebar');
    var overlay = document.getElementById('overlay');
    sidebar.classList.toggle('active');
    overlay.style.display = sidebar.classList.contains('active') ? 'block' : 'none';
}
function buyNumber(id, price) {
    if(userBalance < price) {
        showToast('INSUFFICIENT FUNDS! Need ₹' + price, false);
        setTimeout(function() { openAddCash(); }, 1500);
        return;
    }
    if(confirm('Buy this number for ₹' + price + '?')) {
        fetch('/buy-number', { method: 'POST', headers: {'Content-Type': 'application/x-www-form-urlencoded'}, body: 'number_id=' + id })
        .then(function(res) { return res.json(); })
        .then(function(data) {
            if(data.success) {
                showToast('NUMBER PURCHASED! ' + data.number, true);
                setTimeout(function() { location.reload(); }, 1500);
            } else {
                showToast('ERROR: ' + data.error, false);
            }
        });
    }
}
function openAddCash() { document.getElementById('addCashModal').style.display = 'flex'; }
function closeAddCash() { document.getElementById('addCashModal').style.display = 'none'; document.getElementById('qrResult').innerHTML = ''; document.getElementById('cashAmount').value = ''; }
function generateQR() {
    var amt = document.getElementById('cashAmount').value;
    if(amt < 349) { showToast('Minimum deposit is ₹349', false); return; }
    if(amt > 10000) { showToast('Maximum deposit is ₹10000', false); return; }
    fetch('/add-cash', { method: 'POST', headers: {'Content-Type': 'application/x-www-form-urlencoded'}, body: 'amount=' + amt })
    .then(function(res) { return res.json(); })
    .then(function(data) {
        if(data.success) {
            document.getElementById('qrResult').innerHTML = '<p style="color:#00ffcc;">PAY: ₹' + data.qr_amount + '</p><img src="data:image/png;base64,' + data.qr_code + '" style="width:200px;"><p style="color:#ffaa00;">TXN ID: ' + data.transaction_id + '</p><p>UPI: v76009423@oksbi</p><input type="text" id="verifyTxn" placeholder="Enter Transaction ID" style="width:100%; padding:10px; margin:10px 0;"><button onclick="verifyPayment()">VERIFY PAYMENT</button>';
        } else { showToast('Error: ' + data.error, false); }
    });
}
function verifyPayment() {
    var txn = document.getElementById('verifyTxn').value;
    if(!txn) { showToast('Enter Transaction ID', false); return; }
    fetch('/verify-payment', { method: 'POST', headers: {'Content-Type': 'application/x-www-form-urlencoded'}, body: 'transaction_id=' + txn })
    .then(function(res) { return res.json(); })
    .then(function(data) {
        if(data.success) {
            showToast('Payment verified! Balance: ₹' + data.balance, true);
            setTimeout(function() { location.reload(); }, 1500);
        } else { showToast('Error: ' + data.error, false); }
    });
}
function showNotifications() { document.getElementById('notifModal').style.display = 'flex'; }
function closeNotif() { document.getElementById('notifModal').style.display = 'none'; }
</script>
</body>
</html>
    ''', user=user, numbers=numbers, orders=orders)

@app.route('/buy-number', methods=['POST'])
def buy_number():
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    number_id = request.form.get('number_id')
    number = VirtualNumber.query.get(number_id)
    user = User.query.get(session['user_id'])
    
    if not number or number.is_sold:
        return jsonify({'error': 'Number not available'}), 400
    
    if user.balance < number.price:
        return jsonify({'error': f'Insufficient Funds! Need ₹{number.price}'}), 400
    
    user.balance -= number.price
    number.is_sold = True
    number.sold_to = user.id
    number.sold_at = datetime.now()
    
    order_id = f"ORD{random.randint(100000, 999999)}"
    order = Order(order_id=order_id, user_id=user.id, number_id=number.id, 
                  number=number.number, country=number.country, amount=number.price, status='Completed')
    db.session.add(order)
    db.session.commit()
    
    return jsonify({'success': True, 'number': number.number, 'balance': user.balance})

@app.route('/add-cash', methods=['POST'])
def add_cash():
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    amount = int(request.form.get('amount'))
    if amount < 349:
        return jsonify({'error': 'Minimum deposit is ₹349'}), 400
    if amount > 10000:
        return jsonify({'error': 'Maximum deposit is ₹10000'}), 400
    
    random_paise = generate_random_paise()
    qr_amount = amount + (random_paise / 100)
    transaction_id = generate_transaction_id()
    
    transaction = Transaction(transaction_id=transaction_id, user_id=session['user_id'], amount=amount, qr_amount=qr_amount)
    db.session.add(transaction)
    db.session.commit()
    
    qr_base64 = generate_qr(qr_amount, transaction_id)
    
    return jsonify({'success': True, 'qr_code': qr_base64, 'qr_amount': qr_amount, 'transaction_id': transaction_id})

@app.route('/verify-payment', methods=['POST'])
def verify_payment():
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    transaction_id = request.form.get('transaction_id')
    transaction = Transaction.query.filter_by(transaction_id=transaction_id).first()
    
    if not transaction:
        return jsonify({'error': 'Transaction not found'}), 404
    
    if transaction.status == 'Completed':
        return jsonify({'error': 'Already verified'}), 400
    
    transaction.status = 'Completed'
    user = User.query.get(transaction.user_id)
    user.balance += transaction.amount
    db.session.commit()
    
    return jsonify({'success': True, 'balance': user.balance})

@app.route('/order-history')
def order_history():
    if 'user_id' not in session:
        return redirect('/')
    orders = Order.query.filter_by(user_id=session['user_id']).order_by(Order.created_at.desc()).all()
    return render_template_string('''
<!DOCTYPE html>
<html>
<head><title>Order History | Virtual Numbers</title>
<style>
*{margin:0;padding:0;box-sizing:border-box;font-family:'Orbitron',monospace;}
body{background:linear-gradient(135deg,#0a0a2a,#1a0a3a,#2a1a4a);}
.navbar{background:rgba(10,10,42,0.95);padding:15px 30px;display:flex;justify-content:space-between;border-bottom:1px solid #aa00ff;}
.logo img{height:50px;}
.container{padding:30px;}
.back{color:#aa00ff;text-decoration:none;}
.table-container{background:rgba(255,255,255,0.05);border-radius:16px;overflow-x:auto;margin-top:20px;}
table{width:100%;border-collapse:collapse;}
th,td{padding:12px;color:white;border-bottom:1px solid rgba(255,255,255,0.1);font-size:12px;}
th{color:#aa00ff;}
h2{color:#aa00ff;margin-bottom:20px;}
</style>
</head>
<body>
<div class="navbar"><div class="logo"><img src="https://i.ibb.co/4cHCQB4/photo-AQADKx-Br-G81-GYFV.jpg"></div><a href="/dashboard" class="back">BACK</a></div>
<div class="container"><h2>ORDER HISTORY</h2><div class="table-container"><tr><thead><tr><th>ORDER ID</th><th>NUMBER</th><th>COUNTRY</th><th>AMOUNT</th><th>STATUS</th><th>DATE</th></tr></thead><tbody>{% for o in orders %}<tr><td style="font-family:monospace;">{{ o.order_id }}<\/td><td>{{ o.number }}<\/td><td>{{ o.country }}<\/td><td>₹{{ o.amount }}<\/td><td style="color:#00ff00;">{{ o.status }}<\/td><td>{{ o.created_at.strftime('%Y-%m-%d %H:%M') }}<\/td><\/tr>{% else %}<tr><td colspan="6">No orders yet<\/td><\/tr>{% endfor %}</tbody><\/table><\/div><\/div><\/body><\/html>
    ''', orders=orders)

@app.route('/transaction-history')
def transaction_history():
    if 'user_id' not in session:
        return redirect('/')
    transactions = Transaction.query.filter_by(user_id=session['user_id']).order_by(Transaction.created_at.desc()).all()
    return render_template_string('''
<!DOCTYPE html>
<html>
<head><title>Transaction History | Virtual Numbers</title>
<style>
*{margin:0;padding:0;box-sizing:border-box;font-family:'Orbitron',monospace;}
body{background:linear-gradient(135deg,#0a0a2a,#1a0a3a,#2a1a4a);}
.navbar{background:rgba(10,10,42,0.95);padding:15px 30px;display:flex;justify-content:space-between;border-bottom:1px solid #aa00ff;}
.logo img{height:50px;}
.container{padding:30px;}
.back{color:#aa00ff;text-decoration:none;}
.table-container{background:rgba(255,255,255,0.05);border-radius:16px;overflow-x:auto;margin-top:20px;}
table{width:100%;border-collapse:collapse;}
th,td{padding:12px;color:white;border-bottom:1px solid rgba(255,255,255,0.1);font-size:12px;}
th{color:#aa00ff;}
h2{color:#aa00ff;margin-bottom:20px;}
</style>
</head>
<body>
<div class="navbar"><div class="logo"><img src="https://i.ibb.co/4cHCQB4/photo-AQADKx-Br-G81-GYFV.jpg"></div><a href="/dashboard" class="back">BACK</a></div>
<div class="container"><h2>TRANSACTION HISTORY</h2><div class="table-container"><table><thead><tr><th>TXN ID</th><th>AMOUNT</th><th>QR AMOUNT</th><th>STATUS</th><th>DATE</th></tr></thead><tbody>{% for t in transactions %}</td><td style="font-family:monospace;">{{ t.transaction_id }}<\/td><td>₹{{ t.amount }}<\/td><td>₹{{ t.qr_amount }}<\/td><td style="color:#00ff00;">{{ t.status }}<\/td><td>{{ t.created_at.strftime('%Y-%m-%d %H:%M') }}<\/td><\/tr>{% else %}<tr><td colspan="5">No transactions yet<\/td><\/tr>{% endfor %}</tbody><\/table><\/div><\/div><\/body><\/html>
    ''', transactions=transactions)

@app.route('/admin')
def admin_panel():
    if 'user_id' not in session:
        return redirect('/')
    user = User.query.get(session['user_id'])
    if not user or not user.is_admin:
        return redirect('/')
    
    users = User.query.all()
    orders = Order.query.all()
    numbers = VirtualNumber.query.all()
    return render_template_string('''
<!DOCTYPE html>
<html>
<head><title>Admin Panel | Virtual Numbers</title>
<style>
*{margin:0;padding:0;box-sizing:border-box;font-family:'Orbitron',monospace;}
body{background:linear-gradient(135deg,#0a0a2a,#1a0a3a,#2a1a4a);}
.navbar{background:rgba(10,10,42,0.95);padding:15px 30px;display:flex;justify-content:space-between;border-bottom:1px solid #aa00ff;}
.logo img{height:50px;}
.container{padding:30px;}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:20px;margin-bottom:30px;}
.stat-card{background:rgba(255,255,255,0.05);border:1px solid #aa00ff;border-radius:20px;padding:25px;text-align:center;}
.stat-card h3{color:rgba(255,255,255,0.6);font-size:12px;}
.stat-card .value{color:#aa00ff;font-size:28px;font-weight:bold;}
.table-container{background:rgba(255,255,255,0.05);border-radius:16px;overflow-x:auto;margin:20px 0;}
table{width:100%;border-collapse:collapse;}
th,td{padding:10px;color:white;border-bottom:1px solid rgba(255,255,255,0.1);font-size:12px;}
th{color:#aa00ff;}
button{background:#aa00ff;border:none;padding:5px 10px;border-radius:5px;cursor:pointer;font-weight:bold;color:white;}
</style>
</head>
<body>
<div class="navbar"><div class="logo"><img src="https://i.ibb.co/4cHCQB4/photo-AQADKx-Br-G81-GYFV.jpg"></div><a href="/logout" style="color:#aa00ff;">LOGOUT</a></div>
<div class="container"><h2 style="color:#aa00ff;">ADMIN PANEL</h2>
<div class="stats"><div class="stat-card"><h3>TOTAL USERS</h3><div class="value">{{ users|length }}</div></div><div class="stat-card"><h3>TOTAL ORDERS</h3><div class="value">{{ orders|length }}</div></div><div class="stat-card"><h3>TOTAL NUMBERS</h3><div class="value">{{ numbers|length }}</div></div></div>
<h3 style="color:#aa00ff;">USERS</h3><div class="table-container"><table><thead><tr><th>ID</th><th>USERNAME</th><th>BALANCE</th><th>ACTION</th></tr></thead><tbody>{% for u in users %}<tr><td>{{ u.id }}<\/td><td>{{ u.username }}<\/td><td>₹{{ u.balance }}<\/td><td><input type="number" id="amt_{{ u.id }}" placeholder="AMOUNT" style="width:80px;"><button onclick="addBalance({{ u.id }})">+ ADD<\/button><\/td><\/tr>{% endfor %}</tbody><\/table><\/div>
<h3 style="color:#aa00ff;">ORDERS</h3><div class="table-container"><tr><thead><tr><th>ORDER ID</th><th>USER ID</th><th>NUMBER</th><th>AMOUNT</th><th>DATE</th></tr></thead><tbody>{% for o in orders %}<tr><td style="font-family:monospace;">{{ o.order_id }}<\/td><td>{{ o.user_id }}<\/td><td>{{ o.number }}<\/td><td>₹{{ o.amount }}<\/td><td>{{ o.created_at.strftime('%Y-%m-%d') }}<\/td><\/tr>{% endfor %}</tbody><\/table><\/div><\/div>
<script>function addBalance(id){var amt=document.getElementById('amt_'+id).value;fetch('/admin/add-balance',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:'user_id='+id+'&amount='+amt}).then(function(){location.reload();});}</script>
</body>
</html>
    ''', users=users, orders=orders, numbers=numbers)

@app.route('/admin/add-balance', methods=['POST'])
def admin_add_balance():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    user = User.query.get(session['user_id'])
    if not user or not user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 401
    
    user_id = request.form.get('user_id')
    amount = float(request.form.get('amount'))
    target_user = User.query.get(user_id)
    if target_user:
        target_user.balance += amount
        db.session.commit()
    return jsonify({'success': True})

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
