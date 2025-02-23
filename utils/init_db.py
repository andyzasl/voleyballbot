def init_db():
    """Initialize the database schema and create an admin user if needed."""
    from models import Base
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    import json
    
    # Load config
    with open('config.json') as f:
        config = json.load(f)
    
    # Initialize db engine and session
    engine = create_engine(config['database_url'])
    Base.metadata.create_all(engine)
    
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Add admin user if database is empty
    from models import Player
    if not session.query(Player).first():
        admin = Player(
            telegram_id=config['admin_user_id'],
            name="Volleyball Admin",
            experience=10,
            position="Organizer",
            power=100
        )
        session.add(admin)
        session.commit()

if __name__ == '__main__':
    init_db()
