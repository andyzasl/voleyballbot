from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, mapped_column
from sqlalchemy import Index

Base = declarative_base()

class Player(Base):
    __tablename__ = 'players'

    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    telegram_handle = Column(String(100), unique=True, nullable=True)
    name = Column(String(100), nullable=True)
    skill_level = Column(Integer, default=0)
    preferred_position = Column(String(50), nullable=True)
    is_active = Column(Boolean, default=True)
    registered_at = Column(DateTime, default=datetime.utcnow)

    # Responses to survey questions
    responses = relationship("Response", back_populates="player")

    # Events the player is participating in
    events = relationship("EventParticipant", back_populates="player")

    def __repr__(self):
        return f"<Player(telegram_id={self.telegram_id}, name={self.name})>"

class Question(Base):
    __tablename__ = 'questions'

    id = Column(Integer, primary_key=True)
    question_text = Column(Text, nullable=False)
    question_weight = Column(Integer, default=1)  # Importance factor

    # Options for this question
    options = relationship("QuestionOption", back_populates="question")

    def __repr__(self):
        return f"<Question(id={self.id}, question_text={self.question_text[:20]})>"

class QuestionOption(Base):
    __tablename__ = 'question_options'

    id = Column(Integer, primary_key=True)
    question_id = Column(Integer, ForeignKey('questions.id'), nullable=False)
    option_text = Column(String(200), nullable=False)
    response_points = Column(Integer, nullable=False)

    # The question this option belongs to
    question = relationship("Question", back_populates="options")

    def __repr__(self):
        return f"<QuestionOption(id={self.id}, option_text={self.option_text[:20]})>"

class Response(Base):
    __tablename__ = 'responses'

    id = Column(Integer, primary_key=True)
    player_id = Column(Integer, ForeignKey('players.id'), nullable=False)
    question_id = Column(Integer, ForeignKey('questions.id'), nullable=False)
    option_id = Column(Integer, ForeignKey('question_options.id'), nullable=False)
    response_time = Column(DateTime, default=datetime.utcnow)

    # Relationships
    player = relationship("Player", back_populates="responses")
    question = relationship("Question")
    option = relationship("QuestionOption")

    def __repr__(self):
        return f"<Response(player_id={self.player_id}, question_id={self.question_id}, option_id={self.option_id})>"

class Event(Base):
    __tablename__ = 'events'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    date = Column(DateTime, nullable=True)
    location = Column(String(255), nullable=True)
    max_participants = Column(Integer, default=12)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    # Participants in this event
    participants = relationship("EventParticipant", back_populates="event")

    def __repr__(self):
        return f"<Event(name={self.name}, date={self.date})>"

class EventParticipant(Base):
    __tablename__ = 'event_participants'

    id = Column(Integer, primary_key=True)
    event_id = Column(Integer, ForeignKey('events.id'), nullable=False)
    player_id = Column(Integer, ForeignKey('players.id'), nullable=False)
    joined_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    event = relationship("Event", back_populates="participants")
    player = relationship("Player", back_populates="events")

    def __repr__(self):
        return f"<EventParticipant(event_id={self.event_id}, player_id={self.player_id})>"

# Indexes for performance
Index('player_telegram_id_idx', Player.telegram_id)
Index('event_date_idx', Event.date)
Index('event_participant_event_id_idx', EventParticipant.event_id)
Index('event_participant_player_id_idx', EventParticipant.player_id)
