from app import app, db, Coin


def initialize_database() -> None:
    with app.app_context():
        db.create_all()
        if Coin.query.count() == 0:
            for coin_id in ["bitcoin", "ethereum", "solana"]:
                db.session.add(Coin(coin_id=coin_id))
            db.session.commit()


if __name__ == "__main__":
    initialize_database()
    print("Database initialized.")


