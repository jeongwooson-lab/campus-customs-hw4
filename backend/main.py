import hashlib
import hmac
import json
import os
import secrets
import time
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parents[1] / ".env")
from threading import Lock
from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from models import AgentDeps, AuthInput, AuthResponse, ChatInput, ChatMessage, ChatResponse, RegisterInput, UserPublic
from tools import DATA_DIR, connect, context_facts, get_product, list_products
from agent import answer

app = FastAPI(title='Campus Customs API')
app.add_middleware(CORSMiddleware, allow_origins=os.getenv('FRONTEND_ORIGINS','http://localhost:5173,http://127.0.0.1:5173').split(','), allow_methods=['GET','POST'], allow_headers=['*'])
if (DATA_DIR / 'products').is_dir():
    app.mount('/media/products', StaticFiles(directory=DATA_DIR / 'products'), name='products')
SECRET = os.getenv('SESSION_SECRET') or secrets.token_hex(32)
AUDIT_PATH = Path(__file__).resolve().parents[1] / 'output' / 'audit_trail.json'
_audit_lock = Lock()


def audit(tool, args, result, stop_reason):
    record = {'time': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), 'tool_name':tool,
              'args':str(args)[:160], 'result':str(result)[:160], 'stop_reason':stop_reason}
    with _audit_lock:
        try: previous = json.loads(AUDIT_PATH.read_text())
        except (FileNotFoundError, json.JSONDecodeError): previous = []
        previous.append(record)
        AUDIT_PATH.write_text(json.dumps(previous, indent=2) + '\n')


def hash_password(password, salt=None):
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 120000).hex()
    return f'pbkdf2_sha256${salt}${digest}'


def verify_password(password, stored):
    try:
        scheme,salt,_ = stored.split('$')
        return scheme == 'pbkdf2_sha256' and hmac.compare_digest(hash_password(password,salt),stored)
    except ValueError: return False


def issue_token(user_id):
    payload = f'{user_id}:{int(time.time()) + 60*60*24*7}'
    sig = hmac.new(SECRET.encode(),payload.encode(),hashlib.sha256).hexdigest()
    return f'{payload}:{sig}'


def current_user(authorization: str | None):
    if not authorization or not authorization.startswith('Bearer '): return None
    try:
        uid, exp, sig = authorization[7:].split(':')
        body = f'{uid}:{exp}'
        expected = hmac.new(SECRET.encode(),body.encode(),hashlib.sha256).hexdigest()
        if int(exp) < time.time() or not hmac.compare_digest(sig,expected): return None
        with connect() as db:
            row=db.execute('SELECT id,name,email,first_name,last_name FROM users WHERE id=?',(int(uid),)).fetchone()
            return dict(row) if row else None
    except (ValueError,TypeError): return None


def public_user(row):
    parts=(row['name'] or '').split(' ',1)
    return UserPublic(id=row['id'], first_name=row['first_name'] or parts[0], last_name=row['last_name'] or (parts[1] if len(parts)>1 else ''),email=row['email'])


@app.get('/api/health')
def health():
    return {'ok':True,'data_found':(DATA_DIR/'campus_customs.db').exists(),'ai_configured':bool(os.getenv('OPENAI_API_KEY') or os.getenv('PORTKEY_API_KEY'))}


@app.get('/api/products')
def products(): return list_products()


@app.get('/api/products/{product_id}')
def product(product_id: str):
    found=get_product(product_id)
    if not found: raise HTTPException(404,'Product not found')
    return found


@app.post('/api/register',response_model=AuthResponse)
def register(data: RegisterInput):
    first=data.first_name.strip(); last=data.last_name.strip(); email=data.email.strip().lower()
    if not first or not last or '@' not in email or len(data.password)<8:
        raise HTTPException(400,'Enter your name, a valid email, and a password of at least 8 characters.')
    with connect() as db:
        if db.execute('SELECT 1 FROM users WHERE lower(email)=?',(email,)).fetchone(): raise HTTPException(409,'An account with that email already exists.')
        cursor=db.execute('INSERT INTO users(name,email,password_hash,first_name,last_name) VALUES(?,?,?,?,?)',(first+' '+last,email,hash_password(data.password),first,last))
        db.commit()
        uid=cursor.lastrowid
    return AuthResponse(token=issue_token(uid),user=UserPublic(id=uid,first_name=first,last_name=last,email=email))


@app.post('/api/login',response_model=AuthResponse)
def login(data: AuthInput):
    with connect() as db:
        row=db.execute('SELECT * FROM users WHERE lower(email)=?',(data.email.strip().lower(),)).fetchone()
    if not row or not verify_password(data.password,row['password_hash']): raise HTTPException(401,'Email or password is incorrect.')
    return AuthResponse(token=issue_token(row['id']),user=public_user(row))


@app.get('/api/me',response_model=UserPublic)
def me(authorization: str | None=Header(None)):
    user=current_user(authorization)
    if not user: raise HTTPException(401,'Please log in again.')
    return public_user(user)


@app.get('/api/history',response_model=list[ChatMessage])
def history(authorization: str | None=Header(None)):
    user=current_user(authorization)
    if not user: raise HTTPException(401,'Please log in to see chat history.')
    with connect() as db:
        rows=db.execute('SELECT role,content,products_json FROM chat_messages WHERE user_id=? ORDER BY id DESC LIMIT 40',(user['id'],)).fetchall()
    return [ChatMessage(role=r['role'],content=r['content'],products=json.loads(r['products_json'] or '[]')) for r in reversed(rows)]


@app.post('/api/chat',response_model=ChatResponse)
async def chat(data: ChatInput, authorization: str | None=Header(None)):
    user=current_user(authorization)
    if data.product_id and not get_product(data.product_id): raise HTTPException(400,'Unknown product page.')
    facts=context_facts(data.message,data.product_id)
    deps=AgentDeps(user_name=(user['name'] if user else None),user_email=(user['email'] if user else None),product_id=data.product_id)
    prior=[]
    if user:
        with connect() as db:
            rows=db.execute('SELECT role,content FROM chat_messages WHERE user_id=? ORDER BY id DESC LIMIT 6',(user['id'],)).fetchall()
            prior=[dict(r) for r in reversed(rows)]
    reply,stop=await answer(data.message,deps,facts,prior)
    if user:
        with connect() as db:
            db.execute('INSERT INTO chat_messages(user_id,role,content) VALUES(?,?,?)',(user['id'],'user',data.message))
            db.execute('INSERT INTO chat_messages(user_id,role,content,products_json) VALUES(?,?,?,?)',(user['id'],'assistant',reply,json.dumps([p.model_dump() for p in facts])))
            db.commit()
    for event in deps.tool_events: audit(event['tool'],event['args'],event['result'],stop)
    audit('chat',{'user':user['id'] if user else 'guest','message':data.message[:80],'product_id':data.product_id},f'{len(facts)} products',stop)
    return ChatResponse(reply=reply,products=facts)
