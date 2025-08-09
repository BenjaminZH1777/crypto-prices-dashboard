from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from pycoingecko import CoinGeckoAPI
import time

app = Flask(__name__, static_folder='static', template_folder='templates')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///coins.db'
db = SQLAlchemy(app)
cg = CoinGeckoAPI()

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

@app.route('/')
def index():
    data_dict = fetch_market_data_for_configured_coins()
    coins = Coin.query.all()
    table_data = []
    for coin in coins:
        market = data_dict.get(coin.coin_id)
        if market:
            table_row = {
                'coin_name': market['name'],
                'price': market['current_price'],
                'current_supply': market['circulating_supply'],
                'current_market_cap': market['market_cap'],
                'total_supply': market['total_supply'],
                'total_market_cap': market.get('fully_diluted_valuation', 0),
                'last_updated': market.get('last_updated'),
                'found_raises': coin.found_raises,
                'investor_percentage': coin.investor_percentage,
                'financing_valuation': coin.financing_valuation,
                'financing_based_price': coin.financing_based_price,
                'annualized_income': coin.annualized_income,
                'income_valuation': coin.income_valuation,
                'income_based_price': coin.income_based_price,
                'tokenomics': coin.tokenomics,
                'vesting': coin.vesting,
                'cexs': coin.cexs,
            }
            table_data.append(table_row)
    return render_template('index.html', table_data=table_data)

@app.route('/manage', methods=['GET', 'POST'])
def manage():
    error_message = None
    if request.method == 'POST':
        coin_id = (request.form.get('coin_id') or '').strip()
        buy_price = float(request.form['buy_price']) if request.form.get('buy_price') else None
        amount = float(request.form['amount']) if request.form.get('amount') else None
        found_raises = float(request.form['found_raises']) if request.form['found_raises'] else None
        investor_percentage = float(request.form['investor_percentage']) if request.form['investor_percentage'] else None
        financing_valuation = float(request.form['financing_valuation']) if request.form['financing_valuation'] else None
        financing_based_price = float(request.form['financing_based_price']) if request.form['financing_based_price'] else None
        annualized_income = float(request.form['annualized_income']) if request.form['annualized_income'] else None
        income_valuation = float(request.form['income_valuation']) if request.form['income_valuation'] else None
        income_based_price = float(request.form['income_based_price']) if request.form['income_based_price'] else None
        tokenomics = request.form['tokenomics']
        vesting = request.form['vesting']
        cexs = request.form['cexs']

        # Validate coin id against CoinGecko
        valid_ids = get_valid_coin_ids_set()
        if coin_id not in valid_ids:
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
            else:
                coin = Coin(
                    coin_id=coin_id,
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
                    cexs=cexs
                )
                db.session.add(coin)
            db.session.commit()
            return redirect(url_for('manage'))

    coins = Coin.query.all()
    return render_template('manage.html', coins=coins, error=error_message)

@app.route('/api/data')
def api_data():
    data_dict = fetch_market_data_for_configured_coins()
    coins = Coin.query.all()
    table_data = []
    for coin in coins:
        market = data_dict.get(coin.coin_id)
        if market:
            table_row = {
                'coin_name': market['name'],
                'price': market['current_price'],
                'current_supply': market['circulating_supply'],
                'current_market_cap': market['market_cap'],
                'total_supply': market['total_supply'],
                'total_market_cap': market.get('fully_diluted_valuation', 0),
                'last_updated': market.get('last_updated'),
                'found_raises': coin.found_raises,
                'investor_percentage': coin.investor_percentage,
                'financing_valuation': coin.financing_valuation,
                'financing_based_price': coin.financing_based_price,
                'annualized_income': coin.annualized_income,
                'income_valuation': coin.income_valuation,
                'income_based_price': coin.income_based_price,
                'tokenomics': coin.tokenomics,
                'vesting': coin.vesting,
                'cexs': coin.cexs,
            }
            table_data.append(table_row)
    return jsonify(table_data)

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
def delete_coin(coin_db_id: int):
    # Support both POST (form) and GET (direct link) to reduce 405/500 issues behind some proxies
    try:
        coin = Coin.query.get(coin_db_id)
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

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # Seed with a few popular coins if database is empty
        if Coin.query.count() == 0:
            for coin_id in ['bitcoin', 'ethereum', 'solana']:
                db.session.add(Coin(coin_id=coin_id))
            db.session.commit()
    app.run(debug=True)