import os, sqlite3, secrets, string
from datetime import datetime
from functools import wraps
from flask import Flask, request, redirect, url_for, session, flash, render_template_string, g
from werkzeug.security import generate_password_hash, check_password_hash
app=Flask(__name__); app.secret_key=os.environ.get('SECRET_KEY','change-me-before-deploy'); DB=os.environ.get('DATABASE_PATH','nsla.db'); ADMIN_USER=os.environ.get('ADMIN_USERNAME','nslaadmin'); ADMIN_PASS=os.environ.get('ADMIN_PASSWORD','')
PACKAGES=[('starter','Starter City Tyre','Small Car',20000,5000,80,400000,'product.jpg','Entry package for small city cars'),('standard','Standard Hatchback Tyre','Small Car',30000,7500,80,600000,'tyres.jpg','Budget-friendly tyre for city driving'),('premium','Premium Sedan Tyre','Small Car',50000,12500,80,1000000,'shop.jpg','Comfort tyre for sedan models'),('suv','SUV Grip Tyre','SUV & Sports',80000,20000,80,1600000,'lock.jpg','All-terrain performance tyre'),('sports','Sports Performance Tyre','SUV & Sports',100000,25000,80,2000000,'product.jpg','Performance-inspired tyre package'),('truck','Truck Fleet Tyre','Trucks & Vans',150000,37500,80,3000000,'tyres.jpg','Commercial fleet tyre category'),('van','Delivery Van Tyre','Trucks & Vans',120000,30000,80,2400000,'shop.jpg','For commercial delivery vans'),('heavy','Heavy Machinery Tyre','Heavy Machinery',250000,62500,80,5000000,'lock.jpg','Industrial tyre category'),('lock-bronze','Lock Bronze Tyre','Lock Tyres',15000,1500,16,39000,'product.jpg','Locked-funds package'),('lock-silver','Lock Silver Tyre','Lock Tyres',30000,3000,16,78000,'tyres.jpg','Locked-funds package'),('lock-gold','Lock Gold Tyre','Lock Tyres',55000,5500,16,143000,'shop.jpg','Locked-funds package'),('lock-platinum','Lock Platinum Tyre','Lock Tyres',90000,9000,16,234000,'lock.jpg','Locked-funds package'),('lock-diamond','Lock Diamond Tyre','Lock Tyres',120000,12000,16,312000,'product.jpg','Locked-funds package')]
SCHEMA='''CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY,full_name TEXT,username TEXT UNIQUE,phone TEXT UNIQUE,email TEXT UNIQUE,password_hash TEXT,referral_code TEXT UNIQUE,referred_by TEXT,balance INTEGER DEFAULT 3000,created_at TEXT); CREATE TABLE IF NOT EXISTS purchases(id INTEGER PRIMARY KEY,user_id INTEGER,package_id TEXT,package_name TEXT,cost INTEGER,started_at TEXT,status TEXT DEFAULT 'active'); CREATE TABLE IF NOT EXISTS requests(id INTEGER PRIMARY KEY,user_id INTEGER,kind TEXT,network TEXT,phone TEXT,amount INTEGER,transaction_id TEXT,status TEXT DEFAULT 'pending',created_at TEXT); CREATE TABLE IF NOT EXISTS ledger(id INTEGER PRIMARY KEY,user_id INTEGER,kind TEXT,amount INTEGER,note TEXT,created_at TEXT);'''
def conn():
 if 'db' not in g: g.db=sqlite3.connect(DB); g.db.row_factory=sqlite3.Row
 return g.db
@app.teardown_appcontext
def close(e=None):
 d=g.pop('db',None)
 if d:d.close()
def init():
 c=sqlite3.connect(DB);c.executescript(SCHEMA);c.commit();c.close()
def user(): return conn().execute('SELECT * FROM users WHERE id=?',(session.get('uid',-1),)).fetchone()
def loginreq(fn):
 @wraps(fn)
 def w(*a,**k):
  if not user(): return redirect(url_for('login'))
  return fn(*a,**k)
 return w
@app.context_processor
def glob(): return {'u':user(),'endpoint':request.endpoint}
BASE='''<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,viewport-fit=cover"><meta name="theme-color" content="#781632"><title>NSLA Tyre Hire</title><link rel="stylesheet" href="{{url_for('static',filename='style.css')}}"></head><body><header><a href="{{url_for('home') if u else url_for('index')}}" class="brand">◉ <span>NSLA<small>CARHIRINGTYRES EARN</small></span></a>{% if u %}<span class="avatar">{{u['username'][:2]|upper}}</span>{% endif %}</header><main>{% with ms=get_flashed_messages(with_categories=true) %}{% for cat,msg in ms %}<p class="flash {{cat}}">{{msg}}</p>{% endfor %}{% endwith %}{{content|safe}}</main>{% if u %}<nav>{% for ep,label,ico in [('home','Home','⌂'),('tyres','Tyres','◉'),('lock','Lock','♙'),('team','Team','♧'),('profile','Profile','♙')] %}<a class="{{'active' if endpoint==ep else ''}}" href="{{url_for(ep)}}"><b>{{ico}}</b>{{label}}</a>{% endfor %}</nav>{% endif %}<script>document.querySelectorAll('[data-toggle]').forEach(b=>b.onclick=()=>{let e=document.getElementById(b.dataset.toggle);e.type=e.type==='password'?'text':'password'});document.querySelectorAll('[data-copy]').forEach(b=>b.onclick=async()=>{try{await navigator.clipboard.writeText(b.dataset.copy);b.textContent='Copied'}catch(e){alert(b.dataset.copy)}});document.querySelectorAll('[data-buy]').forEach(b=>b.onclick=()=>{if(confirm('Confirm package: '+b.dataset.name+'\\nCost UGX '+Number(b.dataset.price).toLocaleString()+'\\nReview the package terms before continuing.')){let f=document.createElement('form');f.method='post';f.action='/purchase/'+b.dataset.buy;document.body.appendChild(f);f.submit()}})</script></body></html>'''
def page(content,**kw): return render_template_string(BASE,content=render_template_string(content,**kw))
@app.route('/')
def index():
 if user():return redirect(url_for('home'))
 return page('''<div class="hero"><img src="{{url_for('static',filename='images/tyres.jpg')}}"></div><section class="intro"><p class="eyebrow">CARHIRINGTYRES EARN</p><h1>Keep cars moving.<br>Earn daily.</h1><p class="muted">Mobile-first tyre package platform.</p><div class="actions"><a class="btn" href="{{url_for('signup')}}">Create account</a><a class="btn outline" href="{{url_for('login')}}">Sign in</a></div><p class="hint">Account actions are recorded securely. Deposits require payment verification.</p></section>''')
@app.route('/signup',methods=['GET','POST'])
def signup():
 ref=request.args.get('ref','')
 if request.method=='POST':
  f=request.form; vals=[f.get(k,'').strip() for k in ('full_name','username','phone','email')]; pw=f.get('password',''); ref=f.get('referral_code','').strip().upper()
  if not all(vals) or len(pw)<6: flash('Complete all fields; password needs 6+ characters.','error')
  else:
   code='NSLA-'+''.join(secrets.choice(string.ascii_uppercase+string.digits) for _ in range(6)); c=conn()
   try:
    cur=c.execute('INSERT INTO users(full_name,username,phone,email,password_hash,referral_code,referred_by,balance,created_at) VALUES(?,?,?,?,?,?,?,?,?)',(*vals,generate_password_hash(pw),code,ref,0,datetime.utcnow().isoformat())); uid=cur.lastrowid;c.execute('INSERT INTO ledger(user_id,kind,amount,note,created_at) VALUES(?,?,?,?,?)',(uid,'account_created',0,'Account created',datetime.utcnow().isoformat()));c.commit();session['uid']=uid;return redirect(url_for('home'))
   except sqlite3.IntegrityError: flash('Username, phone or email is already registered.','error')
 return page('''<section class="auth"><h2>Create Account</h2><form method="post">{% for name,label,ph in [('full_name','Full Name','e.g. Tyre man'),('username','Username','e.g. Teria'),('phone','Phone Number','0771234567'),('email','Email','you@example.com')] %}<label>{{label}}<input name="{{name}}" placeholder="{{ph}}" {{'type=email' if name=='email' else ''}} required></label>{% endfor %}<label>Password<div class="pw"><input id="pw" type="password" name="password" minlength="6" placeholder="Min 6 characters" required><button type="button" data-toggle="pw">◉</button></div></label><label>Referral Code (from your invite)<input name="referral_code" value="{{ref}}" placeholder="NSLA-ABC123"></label><p class="muted tiny">Filled in automatically from the invite link you used.</p><button class="btn full">Create Account</button></form><p class="center muted">Already have an account? <a href="{{url_for('login')}}">Sign In</a></p></section>''',ref=ref)
@app.route('/login',methods=['GET','POST'])
def login():
 if request.method=='POST':
  x=request.form.get('identity','').strip(); pw=request.form.get('password','')
  if x==ADMIN_USER and ADMIN_PASS and pw==ADMIN_PASS:
   session.clear(); session['admin']=True; return redirect(url_for('admin_panel'))
  r=conn().execute('SELECT * FROM users WHERE username=? OR phone=? OR email=?',(x,x,x.lower())).fetchone()
  if r and check_password_hash(r['password_hash'],pw):session['uid']=r['id'];return redirect(url_for('home'))
  flash('Incorrect login details.','error')
 return page('''<section class="auth"><div class="hero inside"><img src="{{url_for('static',filename='images/shop.jpg')}}"></div><p class="eyebrow center">CARHIRINGTYRES EARN</p><h2>Welcome Back</h2><form method="post"><label>Email / username / phone<input name="identity" placeholder="you@example.com" required></label><label>Password<div class="pw"><input id="pw" type="password" name="password" required><button type="button" data-toggle="pw">◉</button></div></label><button class="btn full">Sign In</button></form><p class="center muted">Don't have an account? <a href="{{url_for('signup')}}">Sign Up</a></p></section>''')
@app.route('/logout')
def logout():session.clear();return redirect(url_for('index'))
@app.route('/home')
@loginreq
def home():
 u=user(); ps=conn().execute('SELECT * FROM purchases WHERE user_id=?',(u['id'],)).fetchall(); refs=conn().execute('SELECT count(*) n FROM users WHERE referred_by=?',(u['referral_code'],)).fetchone()['n']
 return page('''<div class="hero"><img src="{{url_for('static',filename='images/shop.jpg')}}"></div><section class="headline"><p class="eyebrow">CARHIRINGTYRES EARN</p><h1>FOREX TRY</h1></section><section class="balance"><p class="eyebrow">Available Balance</p><strong>UGX {{'{:,}'.format(u['balance'])}}</strong><span class="pill">Package details</span><hr><p class="muted">Balances update from recorded account transactions. Package returns are not guaranteed.</p></section><div class="actions"><a class="btn" href="{{url_for('money',kind='deposit')}}">↓ Deposit</a><a class="btn outline" href="{{url_for('money',kind='withdraw')}}">↑ Withdraw</a></div><section class="tile"><b>▣ Daily check-in</b><p class="muted">Daily account check-in</p><form method="post" action="{{url_for('checkin')}}"><button class="btn small">Check in</button></form></section><div class="stats"><div>◉<small>Active tyres</small><b>{{ps|length}}</b></div><div>▣<small>Invested</small><b>UGX 0</b></div><div>↗<small>Earnings</small><b>UGX 0</b></div><div>♧<small>Referrals</small><b>{{refs}}</b></div></div><section class="panel"><p class="eyebrow">Portfolio</p><h2>Active Tyres <a class="link" href="{{url_for('tyres')}}">View all →</a></h2>{% if ps %}{% for p in ps %}<p class="list">{{p['package_name']}} <small>{{p['status']}}</small></p>{% endfor %}{% else %}<div class="empty"><h3>No active tyres</h3><p class="muted">Browse available tyre packages.</p><a class="btn" href="{{url_for('tyres')}}">Browse tyres</a></div>{% endif %}</section><section class="panel"><h3>Community & Support</h3><p class="list">♧ Join WhatsApp group</p><p class="list">☏ Inbox admin on WhatsApp</p></section>''',u=u,ps=ps,refs=refs)
@app.route('/tyres')
@loginreq
def tyres():
 cats=['Small Car','SUV & Sports','Trucks & Vans','Heavy Machinery'];return page('''<div class="hero"><img src="{{url_for('static',filename='images/tyres.jpg')}}"></div><section class="intro"><p class="eyebrow">Investment Garage</p><h1>Choose a tyre package</h1><p class="muted">Review package cost and stated schedule before purchase.</p></section><section class="balance"><p class="eyebrow">Available Balance</p><strong>UGX {{'{:,}'.format(u['balance'])}}</strong></section><div class="cats">{% for c in cats %}<a href="#{{c|replace(' ','-')}}">{{c}}</a>{% endfor %}</div>{% for cat in cats %}<h2 id="{{cat|replace(' ','-')}}">{{cat}}</h2><div class="grid">{% for p in packages if p[2]==cat %}<article class="card"><img src="{{url_for('static',filename='images/'+p[7])}}"><div class="pad"><h3>{{p[1]}}</h3><p class="muted">{{p[8]}}</p><div class="minis"><div><b>UGX {{'{:,}'.format(p[6])}}</b><small>Total*</small></div><div><b>UGX {{'{:,}'.format(p[4])}}</b><small>Daily*</small></div><div><b>{{p[5]}}</b><small>Days</small></div></div><p class="price">UGX {{'{:,}'.format(p[3])}}</p><button class="btn full" data-buy="{{p[0]}}" data-name="{{p[1]}}" data-price="{{p[3]}}">Invest Now</button></div></article>{% endfor %}</div>{% endfor %}<p class="hint">*Displayed figures are package information, not a guarantee of profit or payout.</p>''',u=user(),cats=cats,packages=PACKAGES)
@app.route('/lock')
@loginreq
def lock():return page('''<div class="hero"><img src="{{url_for('static',filename='images/lock.jpg')}}"></div><section class="intro"><h1>Lock Tyres</h1><p class="muted">16-day lock period · review package terms</p></section><section class="balance"><p class="eyebrow">Locked Funds</p><strong>UGX 0</strong><p class="muted">Balance UGX {{'{:,}'.format(u['balance'])}}</p></section><div class="grid">{% for p in packages if p[2]=='Lock Tyres' %}<article class="card"><div class="pad"><p class="eyebrow">♙ 10% · 16d</p><h3>{{p[1]}}</h3><p class="price">UGX {{'{:,}'.format(p[3])}}</p><p class="muted">UGX {{'{:,}'.format(p[4])}}/day · sample total UGX {{'{:,}'.format(p[6])}}</p><form method="post" action="{{url_for('purchase',pid=p[0])}}"><button class="btn full">Lock now</button></form></div></article>{% endfor %}</div><section class="panel"><h3>My Locked Tyres</h3><p class="muted">Your purchased packages appear in your portfolio.</p></section>''',u=user(),packages=PACKAGES)
@app.route('/purchase/<pid>',methods=['POST'])
@loginreq
def purchase(pid):
 p=next((x for x in PACKAGES if x[0]==pid),None);u=user()
 if not p:flash('Package not found.','error')
 elif u['balance']<p[3]:flash('Your available balance is too low for this package.','error')
 else:
  c=conn();c.execute('UPDATE users SET balance=balance-? WHERE id=?',(p[3],u['id']));c.execute('INSERT INTO purchases(user_id,package_id,package_name,cost,started_at) VALUES(?,?,?,?,?)',(u['id'],p[0],p[1],p[3],datetime.utcnow().isoformat()));c.execute('INSERT INTO ledger(user_id,kind,amount,note,created_at) VALUES(?,?,?,?,?)',(u['id'],'package_purchase',-p[3],'Package purchase: '+p[1],datetime.utcnow().isoformat()));c.commit();flash('Package purchase recorded and balance updated.','success')
 return redirect(request.referrer or url_for('tyres'))
@app.route('/team')
@loginreq
def team():
 u=user(); rs=conn().execute('SELECT username,created_at FROM users WHERE referred_by=?',(u['referral_code'],)).fetchall();return page('''<div class="hero"><img src="{{url_for('static',filename='images/team.jpg')}}"></div><section class="intro"><p class="eyebrow">Grow your crew</p><h1>Refer & Earn</h1><p class="muted">Share once. Referral registrations are tracked here.</p></section><section class="balance"><p class="eyebrow">Referral Activity</p><strong>UGX 0</strong><span class="pill">Referral levels</span></section><div class="stats three"><div>Level 1<b>{{rs|length}}</b><small>30%*</small></div><div>Level 2<b>0</b><small>2%*</small></div><div>Level 3<b>0</b><small>1%*</small></div></div><section class="panel"><h3>Your Invite</h3><p class="muted">Referral code</p><div class="copy"><code>{{u['referral_code']}}</code><button class="btn small" data-copy="{{u['referral_code']}}">Copy</button></div><p class="muted">Invite URL</p><div class="copy"><code>{{request.url_root}}signup?ref={{u['referral_code']}}</code><button class="btn small" data-copy="{{request.url_root}}signup?ref={{u['referral_code']}}">Copy</button></div></section><section class="panel"><h3>Direct referrals</h3>{% for r in rs %}<p class="list">{{r['username']}} <small>{{r['created_at'][:10]}}</small></p>{% else %}<p class="muted">No referrals yet.</p>{% endfor %}</section>''',u=u,rs=rs)
@app.route('/profile')
@loginreq
def profile():
 u=user();return page('''<div class="hero"><img src="{{url_for('static',filename='images/profile.jpg')}}"></div><section class="intro"><p class="eyebrow">CARHIRINGTYRES EARN</p><h1>My Profile</h1><span class="pill">Member</span></section><section class="panel"><div class="profile"><span class="avatar">{{u['username'][:2]|upper}}</span><div><h2>{{u['full_name']}}</h2><p class="muted">{{u['email']}}</p><p class="muted">{{u['phone']}}</p></div></div><div class="balance tinted"><p class="eyebrow">Available Balance</p><strong>UGX {{'{:,}'.format(u['balance'])}}</strong></div></section><section class="panel"><h3>About NSLA</h3><p class="muted">Deposits are credited only after admin verification. Withdrawals are processed after payout is sent and verified.</p></section><a class="btn full danger" href="{{url_for('logout')}}">⇥ Sign Out</a>''',u=u)
@app.route('/money/<kind>',methods=['GET','POST'])
@loginreq
def money(kind):
 if kind not in ('deposit','withdraw'):return redirect(url_for('home'))
 if request.method=='POST':
  f=request.form
  try: amount=int(f.get('amount','0'))
  except: amount=0
  if amount<(20000 if kind=='deposit' else 5000):flash('Amount is below the minimum.','error')
  elif kind=='withdraw' and amount>user()['balance']:flash('Insufficient available balance.','error')
  else:conn().execute('INSERT INTO requests(user_id,kind,network,phone,amount,transaction_id,created_at) VALUES(?,?,?,?,?,?,?)',(user()['id'],kind,f.get('network','MTN'),f.get('phone',''),amount,f.get('transaction_id',''),datetime.utcnow().isoformat()));conn().commit();flash('Request submitted for admin review. This does not itself transfer money.','success');return redirect(url_for('home'))
 return page('''<section class="auth"><h2>{{kind}} Money</h2><p class="muted center">{{'Send money to a real provider only after checking independently; this payments require manual verification; no automatic mobile-money transfer is connected.' if kind=='deposit' else 'Minimum UGX 5,000 · subject to review'}}</p><form method="post"><div class="net"><label><input type="radio" name="network" value="MTN" checked> MTN</label><label><input type="radio" name="network" value="Airtel"> Airtel</label></div><label>{{'Number you paid from' if kind=='deposit' else 'Your mobile money number'}}<input name="phone" placeholder="07XXXXXXXX" required></label><label>Amount (UGX)<input type="number" name="amount" min="{{20000 if kind=='deposit' else 5000}}" placeholder="{{20000 if kind=='deposit' else 5000}}" required></label>{% if kind=='deposit' %}<label>Transaction ID<input name="transaction_id" placeholder="Payment SMS transaction ID"></label>{% endif %}<button class="btn full">Submit {{kind}}</button></form><p class="hint">Submitting creates a pending request. Deposits are credited after transaction verification; withdrawals are deducted only after payout is sent.</p></section>''',kind=kind)
@app.route('/checkin',methods=['POST'])
@loginreq
def checkin():flash('Daily check-in recorded. This action does not credit money.','success');return redirect(url_for('home'))

@app.route('/admin')
def admin_panel():
 if not session.get('admin'): return redirect(url_for('login'))
 c=conn()
 reqs=c.execute("SELECT r.*,u.username FROM requests r JOIN users u ON u.id=r.user_id ORDER BY r.id DESC LIMIT 100").fetchall()
 users=c.execute("SELECT id,username,full_name,phone,email,balance,created_at FROM users ORDER BY id DESC LIMIT 100").fetchall()
 return page("""<section class="intro"><p class="eyebrow">NSLA CONTROL CENTRE</p><h1>Admin Panel</h1><a class="btn outline" href="{{url_for('admin_logout')}}">Admin sign out</a></section><section class="panel"><h2>Payment requests</h2>{% for r in reqs %}<div class="list"><b>#{{r['id']}} {{r['kind']|title}} · {{r['status']}}</b><p>{{r['username']}} · {{r['network']}} · {{r['phone']}}</p><p><b>UGX {{'{:,}'.format(r['amount'])}}</b> · {{r['transaction_id'] or ''}}</p>{% if r['status']=='pending' %}<form method="post" action="{{url_for('admin_review',rid=r['id'],action='approve')}}"><button class="btn full">{{'Verify deposit' if r['kind']=='deposit' else 'Mark payout sent'}}</button></form><form method="post" action="{{url_for('admin_review',rid=r['id'],action='reject')}}"><button class="btn outline full">Reject</button></form>{% endif %}</div>{% else %}<p class="muted">No requests yet.</p>{% endfor %}</section><section class="panel"><h2>Users</h2>{% for x in users %}<div class="list"><b>{{x['username']}} · UGX {{'{:,}'.format(x['balance'])}}</b><small>{{x['full_name']}} · {{x['phone']}} · {{x['email']}}</small></div>{% endfor %}</section>""",reqs=reqs,users=users)

@app.route('/admin/logout')
def admin_logout():
 session.pop('admin',None)
 return redirect(url_for('login'))

@app.route('/admin/request/<int:rid>/<action>',methods=['POST'])
def admin_review(rid,action):
 if not session.get('admin'): return redirect(url_for('login'))
 if action not in ('approve','reject'): return redirect(url_for('admin_panel'))
 c=conn(); r=c.execute("SELECT * FROM requests WHERE id=?",(rid,)).fetchone()
 if not r: flash("Request not found.","error"); return redirect(url_for('admin_panel'))
 if r['status']!='pending': flash("Request already reviewed.","error"); return redirect(url_for('admin_panel'))
 now=datetime.utcnow().isoformat()
 if action=='approve' and r['kind']=='deposit':
  c.execute("UPDATE users SET balance=balance+? WHERE id=?",(r['amount'],r['user_id']))
  c.execute("INSERT INTO ledger(user_id,kind,amount,note,created_at) VALUES(?,?,?,?,?)",(r['user_id'],'deposit_verified',r['amount'],'Admin-verified deposit request #'+str(rid),now))
 elif action=='approve' and r['kind']=='withdraw':
  current=c.execute("SELECT balance FROM users WHERE id=?",(r['user_id'],)).fetchone()
  if not current or current['balance']<r['amount']:
   flash("Cannot approve: balance is now insufficient.","error"); return redirect(url_for('admin_panel'))
  c.execute("UPDATE users SET balance=balance-? WHERE id=?",(r['amount'],r['user_id']))
  c.execute("INSERT INTO ledger(user_id,kind,amount,note,created_at) VALUES(?,?,?,?,?)",(r['user_id'],'withdrawal_paid',-r['amount'],'Admin marked payout sent for request #'+str(rid),now))
 c.execute("UPDATE requests SET status=? WHERE id=?",('approved' if action=='approve' else 'rejected',rid));c.commit()
 flash("Request updated. Verify a deposit independently before approval; only approve withdrawal after sending payout.","success")
 return redirect(url_for('admin_panel'))

@app.route('/health')
def health():return {'status':'ok','app':'NSLA','mode':'manual-payment-review'}
init()
if __name__=='__main__':app.run(host='0.0.0.0',port=int(os.environ.get('PORT',5000)))
