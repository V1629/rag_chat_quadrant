from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

# Request models
class ChatRequest(BaseModel):
    message: str
    session_id: str
    top_k: Optional[int] = 5
    document_filter: Optional[List[str]] = None
    only_answer_if_sources: Optional[bool] = False

class DocumentUploadResponse(BaseModel):
    id: str
    filename: str
    status: str
    message: str

class SessionCreateRequest(BaseModel):
    session_name: Optional[str] = None

# Response models
class DocumentInfo(BaseModel):
    id: str
    filename: str
    original_filename: str
    file_size: int
    page_count: Optional[int]
    upload_timestamp: datetime
    processing_status: str
    chunk_count: int
    error_message: Optional[str] = None

class Source(BaseModel):
    document_id: str
    document_name: str
    page_number: int
    chunk_index: int
    content: str
    relevance_score: float

class ChatResponse(BaseModel):
    message: str
    sources: List[Source]
    context_chunks: List[Dict[str, Any]]
    response_time_ms: int
    session_id: str

class ChatMessageResponse(BaseModel):
    id: str
    message_type: str
    content: str
    sources: Optional[List[Source]] = None
    timestamp: datetime

class ChatSessionResponse(BaseModel):
    id: str
    session_name: Optional[str]
    created_at: datetime
    updated_at: datetime
    message_count: int

class UserResponse(BaseModel):
    session_id: str
    created_at: datetime
    last_active: datetime

class SettingsRequest(BaseModel):
    top_k: Optional[int] = 5
    document_filter: Optional[List[str]] = None
    model_selector: Optional[str] = "gemini-pro"
    only_answer_if_sources: Optional[bool] = False

class QueryMetricRequest(BaseModel):
    session_id: str
    user_feedback: int  # 1-5 rating
