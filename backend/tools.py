import json
import os
import re
import sqlite3
from pathlib import Path
from models import Product, Stock

DATA_DIR = Path(os.getenv('DATA_DIR', Path(__file__).resolve().parents[1] / 'data')).expanduser().resolve()
DB_PATH = DATA_DIR / 'campus_customs.db'


def connect():
    if not DB_PATH.exists():
        raise FileNotFoundError(f'Data pack missing: {DB_PATH}. Set DATA_DIR to the folder containing campus_customs.db.')
    db = sqlite3.connect(DB_PATH, timeout=10)
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA foreign_keys=ON')
    return db


def product_from_row(db, row):
    stock = [Stock(size=s['size'], quantity=s['quantity']) for s in db.execute('SELECT size, quantity FROM inventory WHERE product_id=? ORDER BY id', (row['product_id'],))]
    path = str(row['image_file_path']).replace('\\', '/')
    return Product(product_id=row['product_id'], name=row['name'], garment_type=row['garment_type'],
                   description=row['description'], colors=json.loads(row['colors']),
                   search_tags=json.loads(row['search_tags']), image_url='/media/' + path,
                   price=row['price'], inventory=stock, total_stock=sum(s.quantity for s in stock))


def list_products(limit=102):
    with connect() as db:
        return [product_from_row(db, r) for r in db.execute('SELECT * FROM catalogue ORDER BY name LIMIT ?', (min(max(limit, 1), 102),))]


def get_product(product_id):
    with connect() as db:
        row = db.execute('SELECT * FROM catalogue WHERE product_id=?', (product_id,)).fetchone()
        return product_from_row(db, row) if row else None


def search_products(query, limit=8):
    terms = re.findall(r'[a-z0-9]+', query.lower())
    stop = {'what','do','you','have','in','the','a','an','for','me','show','find','any','are','there','is','this','it','price','stock','size','sizes','how','many','much','of','and','with','please','yale','can','i','get','some','looking','at','want','available'}
    terms = [t for t in terms if t not in stop]
    stems = {'hoodies':'hoodie','sweatshirts':'sweatshirt','crewnecks':'crewneck','shirts':'shirt','tees':'shirt','tshirts':'shirt','tshirt':'shirt','t-shirts':'shirt','jackets':'jacket','sweaters':'sweater','blue':'navy','grey':'gray'}
    terms = [stems.get(t,t) for t in terms]
    if not terms:
        return []
    scored = []
    for p in list_products():
        name = p.name.lower(); kind = p.garment_type.lower(); tags = ' '.join(p.search_tags).lower(); colors=' '.join(p.colors).lower()
        score = sum(5*(t in name) + 4*(t in kind) + 2*(t in tags) + 2*(t in colors) + (t in p.description.lower()) for t in terms)
        if score:
            scored.append((score,p))
    scored.sort(key=lambda x:(-x[0],x[1].name))
    return [p for _,p in scored[:min(max(limit,1),12)]]


def context_facts(message, product_id=None):
    lower=message.lower()
    contextual = get_product(product_id) if product_id else None
    if contextual and any(t in lower for t in ['this','it','these','here','pink','size','stock','price','color']):
        return [contextual]
    return search_products(message)
