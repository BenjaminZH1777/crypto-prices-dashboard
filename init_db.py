from app import app, db, Coin
from sqlalchemy import inspect


def initialize_database() -> None:
    with app.app_context():
        db.create_all()
        # Add columns buy_price, amount if missing (simple migrate)
        inspector = inspect(db.engine)
        cols = {c['name'] for c in inspector.get_columns('coin')}
        # If table name differs on some setups, try fallback
        if not cols:
            try:
                cols = {c['name'] for c in inspector.get_columns('Coin')}
            except Exception:
                cols = set()
        # Naive migration via ALTER TABLE if not exists
        if 'buy_price' not in cols:
            try:
                db.session.execute(db.text('ALTER TABLE coin ADD COLUMN buy_price FLOAT'))
                db.session.commit()
            except Exception:
                db.session.rollback()
        if 'amount' not in cols:
            try:
                db.session.execute(db.text('ALTER TABLE coin ADD COLUMN amount FLOAT'))
                db.session.commit()
            except Exception:
                db.session.rollback()
        if Coin.query.count() == 0:
            for coin_id in ["bitcoin", "ethereum", "solana"]:
                db.session.add(Coin(coin_id=coin_id))
            db.session.commit()


if __name__ == "__main__":
    initialize_database()
    print("Database initialized.")


