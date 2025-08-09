from flask import Flask, render_template, request, redirect, url_for, jsonify, session, flash
from flask_sqlalchemy import SQLAlchemy
from pycoingecko import CoinGeckoAPI
from pathlib import Path
from sqlalchemy import event
from sqlalchemy.engine import Engine
from functools import wraps
import os
import time
import requests

app = Flask(__name__, static_folder='static', template_folder='templates')

# Ensure SQLite uses an absolute path so all workers/processes point to the same DB
BASE_DIR = Path(__file__).resolve().parent
DB_DIR = BASE_DIR / 'instance'
DB_DIR.mkdir(exist_ok=True)
DB_PATH = DB_DIR / 'coins.db'
VERSION_PATH = BASE_DIR / 'VERSION'
try:
    APP_VERSION = VERSION_PATH.read_text(encoding='utf-8').strip()
except Exception:
    APP_VERSION = ""
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_PATH}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'connect_args': {
        'check_same_thread': False,
        'timeout': 30,
    }
}

# Secret key for session cookies (set SECRET_KEY in production)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-insecure-change-me')

# Admin credentials: prefer hash, fallback to plaintext for convenience in dev
ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD_HASH = os.environ.get('ADMIN_PASSWORD_HASH')  # e.g. pbkdf2:sha256:...
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD')  # plaintext fallback if no hash provided


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):  # noqa: D401
    try:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL;")
        cursor.execute("PRAGMA synchronous=NORMAL;")
        cursor.execute("PRAGMA busy_timeout=30000;")
        cursor.close()
    except Exception:
        # Non-sqlite or failure to set pragmas; ignore
        pass
db = SQLAlchemy(app)
# Use a bounded network timeout to avoid worker hangs on upstream issues.
# Some environments have an older pycoingecko that doesn't accept the keyword.
try:
    cg = CoinGeckoAPI(request_timeout=10)
except TypeError:
    cg = CoinGeckoAPI()
    try:
        setattr(cg, 'request_timeout', 10)
    except Exception:
        pass

class Coin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    coin_id = db.Column(db.String(50), unique=True, nullable=False)
    # Portfolio-related fields
    buy_price = db.Column(db.Float)
    amount = db.Column(db.Float)
    found_raises = db.Column(db.Float)
    investor_percentage = db.Column(db.Float)
    financing_valuation = db.Column(db.Float)
    financing_based_price = db.Column(db.Float)
    annualized_income = db.Column(db.Float)
    income_valuation = db.Column(db.Float)
    income_based_price = db.Column(db.Float)
    tokenomics = db.Column(db.Text)
    vesting = db.Column(db.Text)
    cexs = db.Column(db.Text)
    tags = db.Column(db.Text)

_coin_list_cache = {
    'ids': set(),
    'last_fetch_epoch': 0.0,
}

def get_valid_coin_ids_set(cache_ttl_seconds: int = 3600) -> set:
    now = time.time()
    if now - _coin_list_cache['last_fetch_epoch'] > cache_ttl_seconds or not _coin_list_cache['ids']:
        try:
            coins = cg.get_coins_list()
            _coin_list_cache['ids'] = {c['id'] for c in coins if 'id' in c}
            _coin_list_cache['last_fetch_epoch'] = now
        except Exception:
            # If CoinGecko is unreachable, keep whatever is in cache
            pass
    return _coin_list_cache['ids']

def fetch_market_data_for_configured_coins() -> dict:
    coins = Coin.query.all()
    coin_ids = [c.coin_id for c in coins]
    if not coin_ids:
        return {}
    try:
        markets_data = cg.get_coins_markets(vs_currency='usd', ids=','.join(coin_ids))
    except Exception:
        markets_data = []
    return {market['id']: market for market in markets_data}

# Cache market data to respect free API limits
_market_cache = {
    'data': {},                 # id -> market dict
    'last_fetch_epoch': 0.0,    # last successful fetch epoch
    'last_attempt_epoch': 0.0,  # last attempt (successful or not)
    'ids_key': '',
}

def _fetch_markets_via_requests(coin_ids: list[str], timeout_seconds: int = 10) -> list[dict]:
    if not coin_ids:
        return []
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        'vs_currency': 'usd',
        'ids': ','.join(coin_ids),
        'price_change_percentage': '24h,7d',
    }
    headers = {
        'User-Agent': 'crypto-prices-dashboard/1.0 (+https://github.com/BenjaminZH1777/crypto-prices-dashboard)'
    }
    resp = requests.get(url, params=params, headers=headers, timeout=timeout_seconds)
    resp.raise_for_status()
    return resp.json() or []

def get_cached_market_data(ttl_seconds: int = 300) -> tuple[dict, float, int]:
    """Return (data_dict, last_fetch_epoch, ttl) with simple in-process cache.

    - Re-fetch when ttl expired or configured coin ids changed
    - On fetch error, keep previous cache and timestamps
    """
    coins = Coin.query.all()
    coin_ids = [c.coin_id for c in coins]
    ids_key = ','.join(sorted(coin_ids))
    now = time.time()

    should_refresh = (
        ids_key != _market_cache['ids_key'] or
        (now - _market_cache['last_fetch_epoch'] > ttl_seconds)
    )
    if coin_ids and should_refresh:
        _market_cache['last_attempt_epoch'] = now
        try:
            # Prefer requests with explicit timeout to avoid library differences
            markets_data = _fetch_markets_via_requests(coin_ids, timeout_seconds=10)
        except Exception:
            markets_data = None
        if markets_data is not None:
            _market_cache['data'] = {m.get('id'): m for m in (markets_data or []) if m.get('id')}
            _market_cache['last_fetch_epoch'] = now
            _market_cache['ids_key'] = ids_key
    return _market_cache['data'], _market_cache['last_fetch_epoch'], ttl_seconds

def resolve_coingecko_id(user_input: str) -> str:
    """Resolve user-entered text to a CoinGecko API coin id.

    - If the input already matches a known id, return it as-is.
    - Otherwise query CoinGecko search endpoint and return the first result id.
    - On any failure, return the original input.
    """
    entered = (user_input or "").strip()
    if not entered:
        return entered

    # Quick accept if we already know it's valid
    valid_ids = get_valid_coin_ids_set()
    if valid_ids and entered in valid_ids:
        return entered

    # Try search to map names/symbols/slugs like "spark" -> "spark-2"
    try:
        search = cg.search(entered)
        coins = (search or {}).get('coins') or []
        if coins:
            # Prefer exact id match (case-insensitive), then by name, then symbol
            lower_entered = entered.lower()
            exact_id = next((c for c in coins if c.get('id','').lower() == lower_entered), None)
            if exact_id:
                return exact_id.get('id', entered)

            exact_name = next((c for c in coins if (c.get('name') or '').lower() == lower_entered), None)
            if exact_name:
                return exact_name.get('id', entered)

            exact_symbol = next((c for c in coins if (c.get('symbol') or '').lower() == lower_entered), None)
            if exact_symbol:
                return exact_symbol.get('id', entered)

            # Fallback to the top-ranked search result
            return coins[0].get('id', entered)
    except Exception:
        # Network or API error; keep original
        pass
    return entered


# --------------------------- Admin auth helpers ---------------------------
def _verify_admin_credentials(username: str, password: str) -> bool:
    try:
        if not username or not password:
            return False
        if username != ADMIN_USERNAME:
            return False
        # Prefer hashed verification if provided
        if ADMIN_PASSWORD_HASH:
            try:
                from werkzeug.security import check_password_hash
                return check_password_hash(ADMIN_PASSWORD_HASH, password)
            except Exception:
                return False
        # Fallback to plaintext env for dev
        if ADMIN_PASSWORD is not None:
            return password == ADMIN_PASSWORD
        # If neither provided, reject login for safety
        return False
    except Exception:
        return False


def require_admin(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if not session.get('is_admin'):
            next_url = request.path
            return redirect(url_for('login', next=next_url))
        return view_func(*args, **kwargs)
    return wrapper

@app.route('/')
def index():
    # Keep homepage rendering lightweight to avoid upstream-induced 502s.
    # Data is loaded client-side via /api/data with caching and timeouts.
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    error_message = None
    if request.method == 'POST':
        username = (request.form.get('username') or '').strip()
        password = request.form.get('password') or ''
        if _verify_admin_credentials(username, password):
            session['is_admin'] = True
            session['admin_username'] = username
            dest = request.args.get('next') or url_for('manage')
            return redirect(dest)
        error_message = '用户名或密码错误，或管理员未配置'
        flash(error_message, 'error')
    return render_template('login.html', error=error_message)


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/manage', methods=['GET', 'POST'])
@require_admin
def manage():
    error_message = None
    if request.method == 'POST':
        coin_id = (request.form.get('coin_id') or '').strip()

        def to_float(v):
            return float(v) if v not in (None, "") else None

        buy_price = to_float(request.form.get('buy_price'))
        amount = to_float(request.form.get('amount'))
        found_raises = to_float(request.form.get('found_raises'))
        investor_percentage = to_float(request.form.get('investor_percentage'))
        financing_valuation = to_float(request.form.get('financing_valuation'))
        financing_based_price = to_float(request.form.get('financing_based_price'))
        annualized_income = to_float(request.form.get('annualized_income'))
        income_valuation = to_float(request.form.get('income_valuation'))
        income_based_price = to_float(request.form.get('income_based_price'))
        tokenomics = request.form.get('tokenomics', '')
        vesting = request.form.get('vesting', '')
        cexs = request.form.get('cexs', '')
        tags = request.form.get('tags', '')

        # Try to resolve friendly inputs (e.g., names/symbols) to a real CoinGecko id
        resolved_id = resolve_coingecko_id(coin_id)

        # Validate coin id against CoinGecko
        valid_ids = get_valid_coin_ids_set()
        # Only enforce validation when we actually fetched any ids; if cg unreachable, accept input
        if valid_ids and resolved_id not in valid_ids:
            error_message = f"无效的 CoinGecko 代币ID: {coin_id}"
        else:
            coin = Coin.query.filter_by(coin_id=coin_id).first()
            if coin:
                coin.buy_price = buy_price
                coin.amount = amount
                coin.found_raises = found_raises
                coin.investor_percentage = investor_percentage
                coin.financing_valuation = financing_valuation
                coin.financing_based_price = financing_based_price
                coin.annualized_income = annualized_income
                coin.income_valuation = income_valuation
                coin.income_based_price = income_based_price
                coin.tokenomics = tokenomics
                coin.vesting = vesting
                coin.cexs = cexs
                coin.tags = tags
            else:
                coin = Coin(
                    coin_id=resolved_id,
                    buy_price=buy_price,
                    amount=amount,
                    found_raises=found_raises,
                    investor_percentage=investor_percentage,
                    financing_valuation=financing_valuation,
                    financing_based_price=financing_based_price,
                    annualized_income=annualized_income,
                    income_valuation=income_valuation,
                    income_based_price=income_based_price,
                    tokenomics=tokenomics,
                    vesting=vesting,
                    cexs=cexs,
                    tags=tags
                )
                db.session.add(coin)
            try:
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                error_message = f"数据库写入失败: {e}"
            else:
                return redirect(url_for('manage'))

    coins = Coin.query.all()
    return render_template('manage.html', coins=coins, error=error_message)

@app.route('/manage/edit/<int:coin_db_id>', methods=['GET', 'POST'])
@require_admin
def edit_coin(coin_db_id: int):
    coin = db.session.get(Coin, coin_db_id)
    if not coin:
        return redirect(url_for('manage'))

    error_message = None
    if request.method == 'POST':
        new_coin_id = (request.form.get('coin_id') or '').strip()

        def to_float(v):
            return float(v) if v not in (None, "") else None

        buy_price = to_float(request.form.get('buy_price'))
        amount = to_float(request.form.get('amount'))
        found_raises = to_float(request.form.get('found_raises'))
        investor_percentage = to_float(request.form.get('investor_percentage'))
        financing_valuation = to_float(request.form.get('financing_valuation'))
        financing_based_price = to_float(request.form.get('financing_based_price'))
        annualized_income = to_float(request.form.get('annualized_income'))
        income_valuation = to_float(request.form.get('income_valuation'))
        income_based_price = to_float(request.form.get('income_based_price'))
        tokenomics = request.form.get('tokenomics', '')
        vesting = request.form.get('vesting', '')
        cexs = request.form.get('cexs', '')
        tags = request.form.get('tags', '')

        resolved_id = resolve_coingecko_id(new_coin_id)
        valid_ids = get_valid_coin_ids_set()
        if valid_ids and resolved_id not in valid_ids:
            error_message = f"无效的 CoinGecko 代币ID: {new_coin_id}"
        else:
            coin.coin_id = resolved_id
            coin.buy_price = buy_price
            coin.amount = amount
            coin.found_raises = found_raises
            coin.investor_percentage = investor_percentage
            coin.financing_valuation = financing_valuation
            coin.financing_based_price = financing_based_price
            coin.annualized_income = annualized_income
            coin.income_valuation = income_valuation
            coin.income_based_price = income_based_price
            coin.tokenomics = tokenomics
            coin.vesting = vesting
            coin.cexs = cexs
            coin.tags = tags
            try:
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                error_message = f"数据库写入失败: {e}"
            else:
                return redirect(url_for('manage'))

    return render_template('edit.html', coin=coin, error=error_message)

@app.route('/api/data')
def api_data():
    data_dict, last_epoch, ttl = get_cached_market_data(ttl_seconds=300)
    coins = Coin.query.all()
    table_data = []
    for coin in coins:
        market = data_dict.get(coin.coin_id)
        # Compute financing_based_price if inputs available
        computed_fbp = None
        try:
            total_supply = (market or {}).get('total_supply')
            found_raises = coin.found_raises
            investor_pct = coin.investor_percentage
            if total_supply and total_supply > 0 and found_raises and investor_pct:
                investor_fraction = investor_pct if investor_pct <= 1 else investor_pct / 100.0
                denom = total_supply * investor_fraction
                if denom:
                    computed_fbp = float(found_raises) / float(denom)
        except Exception:
            computed_fbp = None

        table_row = {
            'coin_id': coin.coin_id,
            'coin_name': (market or {}).get('name') or coin.coin_id,
            'price': (market or {}).get('current_price'),
            'current_supply': (market or {}).get('circulating_supply'),
            'current_market_cap': (market or {}).get('market_cap'),
            'total_supply': (market or {}).get('total_supply'),
            'total_market_cap': (market or {}).get('fully_diluted_valuation', 0),
            'last_updated': (market or {}).get('last_updated'),
            'pct_24h': (market or {}).get('price_change_percentage_24h_in_currency', (market or {}).get('price_change_percentage_24h')),
            'pct_7d': (market or {}).get('price_change_percentage_7d_in_currency'),
            'found_raises': coin.found_raises,
            'investor_percentage': coin.investor_percentage,
            'financing_valuation': coin.financing_valuation,
            'financing_based_price': computed_fbp if computed_fbp is not None else coin.financing_based_price,
            'annualized_income': coin.annualized_income,
            'income_valuation': coin.income_valuation,
            'income_based_price': coin.income_based_price,
            'tokenomics': coin.tokenomics,
            'vesting': coin.vesting,
            'cexs': coin.cexs,
            'tags': coin.tags,
        }
        table_data.append(table_row)
    # Include cache metadata so UI can show last/next refresh
    response = {
        'rows': table_data,
        'last_refresh_epoch': last_epoch if last_epoch else None,
        'next_refresh_epoch': (last_epoch + ttl) if last_epoch else None,
    }
    return jsonify(response)

@app.route('/api/prices')
def api_prices():
    data_dict = fetch_market_data_for_configured_coins()
    coins = Coin.query.all()
    response = []
    for coin in coins:
        market = data_dict.get(coin.coin_id)
        if not market:
            continue
        current_price = market.get('current_price')
        buy_price = coin.buy_price or 0.0
        amount = coin.amount or 0.0
        profit = 0.0
        if current_price is not None and buy_price and amount:
            profit = (current_price - buy_price) * amount
        response.append({
            'name': market.get('name'),
            'current_price': float(current_price) if current_price is not None else None,
            'buy_price': float(buy_price) if buy_price is not None else None,
            'amount': float(amount) if amount is not None else None,
            'profit': float(profit),
        })
    return jsonify(response)

@app.route('/manage/delete/<int:coin_db_id>', methods=['POST', 'GET'])
@require_admin
def delete_coin(coin_db_id: int):
    # Support both POST (form) and GET (direct link) to reduce 405/500 issues behind some proxies
    try:
        coin = db.session.get(Coin, coin_db_id)
        if coin:
            db.session.delete(coin)
            db.session.commit()
    except Exception:
        db.session.rollback()
        # Best-effort: log and continue redirect to manage
        app.logger.exception("Failed to delete coin %s", coin_db_id)
    return redirect(url_for('manage'))

@app.route('/api/coin_ids')
def api_coin_ids():
    # Returns a small sample of popular coin ids for UI help (not the full 7k list)
    popular = ['bitcoin', 'ethereum', 'tether', 'binancecoin', 'solana', 'ripple', 'dogecoin', 'cardano', 'tron', 'polkadot']
    return jsonify(popular)

@app.context_processor
def inject_version():
    return {
        "APP_VERSION": APP_VERSION,
        "IS_ADMIN": bool(session.get('is_admin')),
        "ADMIN_USERNAME": session.get('admin_username'),
    }

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # lightweight migration for new columns
        try:
            from sqlalchemy import text
            cols = db.session.execute(text("PRAGMA table_info(coin)")).fetchall()
            names = {c[1] for c in cols}
            if 'tags' not in names:
                db.session.execute(text("ALTER TABLE coin ADD COLUMN tags TEXT"))
                db.session.commit()
        except Exception:
            db.session.rollback()
        # Seed with a few popular coins if database is empty
        if Coin.query.count() == 0:
            for coin_id in ['bitcoin', 'ethereum', 'solana']:
                db.session.add(Coin(coin_id=coin_id))
            db.session.commit()
    app.run(debug=True)