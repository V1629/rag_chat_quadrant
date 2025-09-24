import os
import uuid
import shutil
import asyncio
from pathlib import Path
from typing import List, Optional
import logging
from dotenv import load_dotenv

# Load environment variables first from project root
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from models import (
    User, Document, ChatSession, ChatMessage, QueryMetric, DocumentChunk, 
    get_db, engine, Base
)
from schemas import (
    ChatRequest, ChatResponse, DocumentUploadResponse, DocumentInfo, 
    ChatSessionResponse, ChatMessageResponse, SessionCreateRequest,
    QueryMetricRequest, SettingsRequest
)
from config import settings
from pdf_processor import pdf_processor, calculate_file_hash
from rag_service import rag_service

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create tables (after environment is loaded)
try:
    Base.metadata.create_all(bind=engine)
    logger.info("✅ Database tables created successfully")
except Exception as e:
    logger.error(f"❌ Failed to create database tables: {e}")
    # Don't exit, let the app start anyway

# Initialize FastAPI app
app = FastAPI(
    title="PDF RAG API",
    description="API for PDF-based Retrieval-Augmented Generation",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure upload directory exists
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("Starting PDF RAG API...")
    logger.info(f"Upload directory: {settings.UPLOAD_DIR}")
    logger.info(f"Qdrant URL: {settings.QDRANT_URL}")

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "PDF RAG API is running", "status": "healthy"}

@app.get("/health")
async def health_check():
    """Detailed health check"""
    try:
        stats = pdf_processor.get_document_stats()
        return {
            "status": "healthy",
            "database": "connected",
            "vector_db": "connected",
            "total_chunks": stats.get("total_chunks", 0)
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

# User and Session Management
@app.post("/api/users", response_model=dict)
async def create_user(session_id: str, db: Session = Depends(get_db)):
    """Create or get user by session ID"""
    user = db.query(User).filter(User.session_id == session_id).first()
    if not user:
        user = User(session_id=session_id)
        db.add(user)
        db.commit()
        db.refresh(user)
    
    return {"session_id": user.session_id, "user_id": str(user.id)}

@app.post("/api/sessions", response_model=ChatSessionResponse)
async def create_chat_session(
    request: SessionCreateRequest,
    session_id: str,
    db: Session = Depends(get_db)
):
    """Create a new chat session"""
    user = db.query(User).filter(User.session_id == session_id).first()
    if not user:
        user = User(session_id=session_id)
        db.add(user)
        db.flush()
    
    chat_session = ChatSession(
        user_id=user.id,
        session_name=request.session_name or f"Chat {uuid.uuid4().hex[:8]}"
    )
    db.add(chat_session)
    db.commit()
    db.refresh(chat_session)
    
    return ChatSessionResponse(
        id=str(chat_session.id),
        session_name=chat_session.session_name,
        created_at=chat_session.created_at,
        updated_at=chat_session.updated_at,
        message_count=0
    )

@app.get("/api/sessions", response_model=List[ChatSessionResponse])
async def get_chat_sessions(session_id: str, db: Session = Depends(get_db)):
    """Get all chat sessions for a user"""
    user = db.query(User).filter(User.session_id == session_id).first()
    if not user:
        return []
    
    sessions = db.query(ChatSession).filter(ChatSession.user_id == user.id).all()
    
    result = []
    for session in sessions:
        message_count = db.query(ChatMessage).filter(ChatMessage.session_id == session.id).count()
        result.append(ChatSessionResponse(
            id=str(session.id),
            session_name=session.session_name,
            created_at=session.created_at,
            updated_at=session.updated_at,
            message_count=message_count
        ))
    
    return result

@app.delete("/api/sessions/{session_id}")
async def delete_chat_session(session_id: str, db: Session = Depends(get_db)):
    """Delete a chat session"""
    chat_session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not chat_session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    db.delete(chat_session)
    db.commit()
    return {"message": "Session deleted successfully"}

@app.get("/api/sessions/{session_id}/messages", response_model=List[ChatMessageResponse])
async def get_chat_messages(session_id: str, db: Session = Depends(get_db)):
    """Get all messages in a chat session"""
    messages = db.query(ChatMessage).filter(
        ChatMessage.session_id == session_id
    ).order_by(ChatMessage.timestamp).all()
    
    result = []
    for msg in messages:
        result.append(ChatMessageResponse(
            id=str(msg.id),
            message_type=msg.message_type,
            content=msg.content,
            sources=msg.sources,
            timestamp=msg.timestamp
        ))
    
    return result

# Document Management
@app.post("/api/documents/upload", response_model=DocumentUploadResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload and process a PDF document"""
    
    # Validate file
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    if file.size > settings.MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large")
    
    try:
        # Save file
        file_id = str(uuid.uuid4())
        filename = f"{file_id}_{file.filename}"
        file_path = os.path.join(settings.UPLOAD_DIR, filename)
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Calculate file hash
        file_hash = calculate_file_hash(file_path)
        
        # Check if document already exists
        existing_doc = db.query(Document).filter(Document.content_hash == file_hash).first()
        if existing_doc:
            os.remove(file_path)  # Remove duplicate file
            return DocumentUploadResponse(
                id=str(existing_doc.id),
                filename=existing_doc.filename,
                status="already_exists",
                message="Document already uploaded"
            )
        
        # Create document record
        document = Document(
            id=file_id,
            filename=filename,
            original_filename=file.filename,
            file_size=file.size,
            content_hash=file_hash,
            processing_status='pending'
        )
        db.add(document)
        db.commit()
        
        # Process document in background
        background_tasks.add_task(
            pdf_processor.process_pdf,
            file_path,
            file_id,
            db
        )
        
        return DocumentUploadResponse(
            id=file_id,
            filename=file.filename,
            status="uploaded",
            message="Document uploaded successfully and processing started"
        )
        
    except Exception as e:
        logger.error(f"Error uploading document: {e}")
        raise HTTPException(status_code=500, detail="Error uploading document")

@app.get("/api/documents", response_model=List[DocumentInfo])
async def get_documents(db: Session = Depends(get_db)):
    """Get all uploaded documents"""
    documents = db.query(Document).order_by(Document.upload_timestamp.desc()).all()
    
    result = []
    for doc in documents:
        result.append(DocumentInfo(
            id=str(doc.id),
            filename=doc.filename,
            original_filename=doc.original_filename,
            file_size=doc.file_size,
            page_count=doc.page_count,
            upload_timestamp=doc.upload_timestamp,
            processing_status=doc.processing_status,
            chunk_count=doc.chunk_count,
            error_message=doc.error_message
        ))
    
    return result

@app.delete("/api/documents/{document_id}")
async def delete_document(document_id: str, db: Session = Depends(get_db)):
    """Delete a document and its chunks"""
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    try:
        # Delete chunks from vector database
        chunks = db.query(DocumentChunk).filter(DocumentChunk.document_id == document_id).all()
        for chunk in chunks:
            try:
                pdf_processor.qdrant_client.delete(
                    collection_name=settings.QDRANT_COLLECTION_NAME,
                    points_selector=[chunk.vector_id]
                )
            except Exception as e:
                logger.warning(f"Error deleting vector {chunk.vector_id}: {e}")
        
        # Delete file
        file_path = os.path.join(settings.UPLOAD_DIR, document.filename)
        if os.path.exists(file_path):
            os.remove(file_path)
        
        # Delete from database
        db.delete(document)
        db.commit()
        
        return {"message": "Document deleted successfully"}
        
    except Exception as e:
        logger.error(f"Error deleting document: {e}")
        raise HTTPException(status_code=500, detail="Error deleting document")

# Chat
@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, db: Session = Depends(get_db)):
    """Chat with documents using RAG"""
    
    # Get chat session
    chat_session = db.query(ChatSession).filter(ChatSession.id == request.session_id).first()
    if not chat_session:
        raise HTTPException(status_code=404, detail="Chat session not found")
    
    try:
        # Save user message
        user_message = ChatMessage(
            session_id=request.session_id,
            message_type='user',
            content=request.message
        )
        db.add(user_message)
        
        # Get RAG response
        result = rag_service.answer_question(
            query=request.message,
            top_k=request.top_k or settings.DEFAULT_TOP_K,
            document_filter=request.document_filter,
            only_answer_if_sources=request.only_answer_if_sources or False
        )
        
        # Save assistant message
        assistant_message = ChatMessage(
            session_id=request.session_id,
            message_type='assistant',
            content=result['response'],
            sources=result['sources'],
            context_chunks=result['context_chunks'],
            response_time_ms=result['response_time_ms'],
            tokens_used=result['tokens_used']
        )
        db.add(assistant_message)
        
        # Save query metrics
        metric = QueryMetric(
            session_id=request.session_id,
            query=request.message,
            retrieved_chunks=len(result['context_chunks']),
            top_k=request.top_k or settings.DEFAULT_TOP_K,
            response_time_ms=result['response_time_ms'],
            tokens_used=result['tokens_used']
        )
        db.add(metric)
        
        # Update session timestamp to current time
        from datetime import datetime
        chat_session.updated_at = datetime.utcnow()
        
        db.commit()
        
        return ChatResponse(
            message=result['response'],
            sources=result['sources'],
            context_chunks=result['context_chunks'],
            response_time_ms=result['response_time_ms'],
            session_id=request.session_id
        )
        
    except Exception as e:
        logger.error(f"Error in chat: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Error processing chat message")

@app.post("/api/feedback")
async def submit_feedback(
    request: QueryMetricRequest,
    db: Session = Depends(get_db)
):
    """Submit user feedback for a query"""
    
    # Find the most recent metric for this session
    metric = db.query(QueryMetric).filter(
        QueryMetric.session_id == request.session_id
    ).order_by(QueryMetric.timestamp.desc()).first()
    
    if metric:
        metric.user_feedback = request.user_feedback
        db.commit()
        return {"message": "Feedback submitted successfully"}
    else:
        raise HTTPException(status_code=404, detail="No recent query found for feedback")

@app.get("/api/stats")
async def get_stats(db: Session = Depends(get_db)):
    """Get system statistics"""
    try:
        doc_count = db.query(Document).count()
        completed_docs = db.query(Document).filter(Document.processing_status == 'completed').count()
        total_chunks = db.query(DocumentChunk).count()
        chat_sessions = db.query(ChatSession).count()
        total_messages = db.query(ChatMessage).count()
        
        vector_stats = pdf_processor.get_document_stats()
        
        return {
            "documents": {
                "total": doc_count,
                "completed": completed_docs,
                "processing": doc_count - completed_docs
            },
            "chunks": {
                "total": total_chunks,
                "in_vector_db": vector_stats.get("total_chunks", 0)
            },
            "chat": {
                "sessions": chat_sessions,
                "messages": total_messages
            }
        }
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving statistics")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.API_HOST, port=settings.API_PORT)
