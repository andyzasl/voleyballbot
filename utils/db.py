import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Question, QuestionOption

def create_db_engine(config):
    """Creates a database engine based on the configuration."""
    db_config = config['database']
    db_url = f"{db_config['dialect']}:///{db_config['name']}"
    return create_engine(db_url)

def create_db_session(engine):
    """Creates a database session."""
    return sessionmaker(bind=engine)

def load_questions(session, questions_file="data/initial_data.json"):
    """Loads questions from a JSON file into the database."""
    with open(questions_file, 'r') as f:
        questions_data = json.load(f)

    for q_data in questions_data['questions']:
        question = Question(question_text=q_data['question_text'], question_weight=q_data['question_weight'])
        for option_data in q_data['options']:
            option = QuestionOption(question_text=option_data['option_text'], response_points=option_data['response_points'])
            question.options.append(option)
        session.add(question)

    session.commit()
    return
    
def init_db(engine):
    """Initializes the database by creating the tables."""
    Base.metadata.create_all(engine)
    # load_questions(engine) # questions are loaded by alembic migration instead
