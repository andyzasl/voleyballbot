import pytest
from models import Player, Question, Event
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

@pytest.fixture
def session():
    engine = create_engine('sqlite:///:memory:')
    Session = sessionmaker(bind=engine)
    session = Session()
    return session

def test_player_model(session):
    player = Player(telegram_id=123, name="Test Player")
    session.add(player)
    session.commit()
    assert player in session.query(Player).all()

def test_question_model(session):
    question = Question(question_text="Test question")
    session.add(question)
    session.commit()
    assert question in session.query(Question).all()

def test_event_model(session):
    event = Event(title="Test event")
    session.add(event)
    session.commit()
    assert event in session.query(Event).all()
