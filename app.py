from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from pycoingecko import CoinGeckoAPI
import time

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///coins.db'
db = SQLAlchemy(app)
cg = CoinGeckoAPI()

class Coin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    coin_id = db.Column(db.String(50), unique=True, nullable=False)
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

@app.route('/manage/delete/<int:coin_db_id>', methods=['POST'])
def delete_coin(coin_db_id: int):
    coin = Coin.query.get(coin_db_id)
    if coin:
        db.session.delete(coin)
        db.session.commit()
    return redirect(url_for('manage'))

@app.route('/api/coin_ids')
def api_coin_ids():
    # Returns a small sample of popular coin ids for UI help (not the full 7k list)
    popular = ['bitcoin', 'ethereum', 'tether', 'binancecoin', 'solana', 'ripple', 'dogecoin', 'cardano', 'tron', 'polkadot']
    return jsonify(popular)

if __name__ == '__main__':
    db.create_all()
    # Seed with a few popular coins if database is empty
    if Coin.query.count() == 0:
        for coin_id in ['bitcoin', 'ethereum', 'solana']:
            db.session.add(Coin(coin_id=coin_id))
        db.session.commit()
    app.run(debug=True)