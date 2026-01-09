"""
Database models for the application
"""
from sqlalchemy import create_engine, Column, String, Integer, Text, DateTime, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

Base = declarative_base()

# Database URL (SQLite for development)
DATABASE_URL = "sqlite:///./test_analysis.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Test(Base):
    __tablename__ = "tests"
    
    id = Column(String, primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    images = Column(JSON)  # Store image paths/URLs
    extracted_content = Column(JSON)  # Store OCR results
    
    mistakes = relationship("Mistake", back_populates="test")
    practice_sessions = relationship("PracticeSession", back_populates="test")


class Mistake(Base):
    __tablename__ = "mistakes"
    
    id = Column(String, primary_key=True)
    test_id = Column(String, ForeignKey("tests.id"))
    question_number = Column(Integer)
    mistake_description = Column(Text)
    why_wrong = Column(Text)
    how_to_fix = Column(Text)
    weak_area = Column(String)
    user_answer = Column(Text)
    correct_answer = Column(Text)
    
    test = relationship("Test", back_populates="mistakes")
    practice_questions = relationship("PracticeQuestion", back_populates="mistake")


class PracticeQuestion(Base):
    __tablename__ = "practice_questions"
    
    id = Column(String, primary_key=True)
    mistake_id = Column(String, ForeignKey("mistakes.id"))
    question_text = Column(Text)
    difficulty = Column(String)
    topic = Column(String)
    correct_answer = Column(Text)
    solution_steps = Column(JSON)
    
    mistake = relationship("Mistake", back_populates="practice_questions")
    submissions = relationship("PracticeSubmission", back_populates="question")


class PracticeSession(Base):
    __tablename__ = "practice_sessions"
    
    id = Column(String, primary_key=True)
    test_id = Column(String, ForeignKey("tests.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    completed = Column(Integer, default=0)  # 0 = in progress, 1 = completed
    
    test = relationship("Test", back_populates="practice_sessions")
    submissions = relationship("PracticeSubmission", back_populates="session")


class PracticeSubmission(Base):
    __tablename__ = "practice_submissions"
    
    id = Column(String, primary_key=True)
    question_id = Column(String, ForeignKey("practice_questions.id"))
    session_id = Column(String, ForeignKey("practice_sessions.id"))
    submitted_answer = Column(Text)
    is_correct = Column(Integer)  # 0 = wrong, 1 = correct
    feedback = Column(Text)
    submitted_at = Column(DateTime, default=datetime.utcnow)
    
    question = relationship("PracticeQuestion", back_populates="submissions")
    session = relationship("PracticeSession", back_populates="submissions")


def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

