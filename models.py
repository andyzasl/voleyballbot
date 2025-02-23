from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class Player(Base):
    __tablename__ = 'players'
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    experience = Column(Integer, default=0)
    position = Column(String(50))
    power = Column(Integer, default=0)  # Calculated skill level
    
class Question(Base):
    __tablename__ = 'questions'
    
    id = Column(Integer, primary_key=True)
    question_text = Column(Text, nullable=False)
    question_weight = Column(Integer, default=1)  # Importance factor
    
class QuestionResponse(Base):
    __tablename__ = 'question_responses'
    
    id = Column(Integer, primary_key=True)
    question_id = Column(Integer, ForeignKey('questions.id'), nullable=False)
    response_text = Column(String(200), nullable=False)
    response_points = Column(Integer, nullable=False)
    
    question = relationship('Question', backref='responses')
    
class Event(Base):
    __tablename__ = 'events'
    
    id = Column(Integer, primary_key=True)
    title = Column(String(100), nullable=False)
    description = Column(Text)
    max_participants = Column(Integer, default=12)  # Default 2 teams of 6
    date = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
class EventParticipant(Base):
    __tablename__ = 'event_participants'
    
    id = Column(Integer, primary_key=True)
    event_id = Column(Integer, ForeignKey('events.id'), nullable=False)
    player_id = Column(Integer, ForeignKey('players.id'), nullable=False)
    
    event = relationship('Event', backref='participants')
    player = relationship('Player', backref='events')
