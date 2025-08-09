from app import app, db, Coin
from sqlalchemy import inspect, text


def initialize_database() -> None:
    with app.app_context():
        db.create_all()
        # Add new columns if missing (simple migrate)
        inspector = inspect(db.engine)
        cols = {c['name'] for c in inspector.get_columns('coin')}
        # If table name differs on some setups, try fallback
        if not cols:
            try:
                cols = {c['name'] for c in inspector.get_columns('Coin')}
            except Exception:
                cols = set()
        # Naive migration via ALTER TABLE if not exists
        migrations = [
            ('buy_price', 'FLOAT'),
            ('amount', 'FLOAT'),
            ('found_raises', 'FLOAT'),
            ('investor_percentage', 'FLOAT'),
            ('financing_valuation', 'FLOAT'),
            ('financing_based_price', 'FLOAT'),
            ('annualized_income', 'FLOAT'),
            ('income_valuation', 'FLOAT'),
            ('income_based_price', 'FLOAT'),
            ('tokenomics', 'TEXT'),
            ('vesting', 'TEXT'),
            ('cexs', 'TEXT'),
            ('tags', 'TEXT'),
        ]
        for col_name, col_type in migrations:
            if col_name not in cols:
                try:
                    db.session.execute(text(f'ALTER TABLE coin ADD COLUMN {col_name} {col_type}'))
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


