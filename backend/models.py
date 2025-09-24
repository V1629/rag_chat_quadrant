from sqlalchemy import create_engine, Column, String, Integer, BigInteger, DateTime, Text, JSON, ForeignKey, CheckConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/rag_db")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(String(255), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_active = Column(DateTime, default=datetime.utcnow)
    
    chat_sessions = relationship("ChatSession", back_populates="user", cascade="all, delete-orphan")

class Document(Base):
    __tablename__ = "documents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_size = Column(BigInteger, nullable=False)
    content_hash = Column(String(255), unique=True, nullable=False)
    page_count = Column(Integer)
    upload_timestamp = Column(DateTime, default=datetime.utcnow)
    processing_status = Column(String(50), default='pending')
    error_message = Column(Text)
    chunk_count = Column(Integer, default=0)
    
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")

class ChatSession(Base):
    __tablename__ = "chat_sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    session_name = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("chat_sessions.id", ondelete="CASCADE"))
    message_type = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    sources = Column(JSON)
    context_chunks = Column(JSON)
    timestamp = Column(DateTime, default=datetime.utcnow)
    response_time_ms = Column(Integer)
    tokens_used = Column(Integer)
    
    session = relationship("ChatSession", back_populates="messages")
    
    __table_args__ = (
        CheckConstraint("message_type IN ('user', 'assistant')", name='check_message_type'),
    )

class QueryMetric(Base):
    __tablename__ = "query_metrics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("chat_sessions.id"))
    query = Column(Text, nullable=False)
    retrieved_chunks = Column(Integer)
    top_k = Column(Integer)
    response_time_ms = Column(Integer)
    tokens_used = Column(Integer)
    user_feedback = Column(Integer)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        CheckConstraint("user_feedback BETWEEN 1 AND 5", name='check_user_feedback'),
    )

class DocumentChunk(Base):
    __tablename__ = "document_chunks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"))
    chunk_index = Column(Integer, nullable=False)
    page_number = Column(Integer)
    content_preview = Column(Text)
    vector_id = Column(String(255), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    document = relationship("Document", back_populates="chunks")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
