# API Documentation

## Overview
The PDF RAG API provides endpoints for document management, chat functionality, and system administration.

## Base URL
```
http://localhost:8000
```

## Authentication
Currently, the API uses session-based identification. Each user is identified by a unique `session_id`.

## Endpoints

### Health Check
#### GET /health
Returns the health status of the system.

**Response:**
```json
{
  "status": "healthy",
  "database": "connected",
  "vector_db": "connected",
  "total_chunks": 1234
}
```

### User Management
#### POST /api/users
Create or retrieve a user by session ID.

**Parameters:**
- `session_id` (query): Unique session identifier

**Response:**
```json
{
  "session_id": "uuid-string",
  "user_id": "uuid-string"
}
```

### Document Management

#### POST /api/documents/upload
Upload a PDF document for processing.

**Request:**
- File upload (multipart/form-data)
- File type: PDF only
- Max size: 50MB

**Response:**
```json
{
  "id": "uuid-string",
  "filename": "document.pdf",
  "status": "uploaded",
  "message": "Document uploaded successfully"
}
```

#### GET /api/documents
Retrieve all uploaded documents.

**Response:**
```json
[
  {
    "id": "uuid-string",
    "filename": "stored_filename.pdf",
    "original_filename": "document.pdf",
    "file_size": 1024000,
    "page_count": 10,
    "upload_timestamp": "2023-01-01T00:00:00",
    "processing_status": "completed",
    "chunk_count": 45,
    "error_message": null
  }
]
```

#### DELETE /api/documents/{document_id}
Delete a document and all associated data.

**Response:**
```json
{
  "message": "Document deleted successfully"
}
```

### Chat Management

#### POST /api/sessions
Create a new chat session.

**Parameters:**
- `session_id` (query): User session ID

**Request Body:**
```json
{
  "session_name": "Optional session name"
}
```

**Response:**
```json
{
  "id": "uuid-string",
  "session_name": "Chat Session",
  "created_at": "2023-01-01T00:00:00",
  "updated_at": "2023-01-01T00:00:00",
  "message_count": 0
}
```

#### GET /api/sessions
Get all chat sessions for a user.

**Parameters:**
- `session_id` (query): User session ID

**Response:**
```json
[
  {
    "id": "uuid-string",
    "session_name": "Chat Session",
    "created_at": "2023-01-01T00:00:00",
    "updated_at": "2023-01-01T00:00:00",
    "message_count": 5
  }
]
```

#### DELETE /api/sessions/{session_id}
Delete a chat session and all messages.

**Response:**
```json
{
  "message": "Session deleted successfully"
}
```

#### GET /api/sessions/{session_id}/messages
Get all messages in a chat session.

**Response:**
```json
[
  {
    "id": "uuid-string",
    "message_type": "user",
    "content": "What is this document about?",
    "sources": null,
    "timestamp": "2023-01-01T00:00:00"
  },
  {
    "id": "uuid-string",
    "message_type": "assistant",
    "content": "This document discusses...",
    "sources": [
      {
        "document_id": "uuid-string",
        "document_name": "document.pdf",
        "page_number": 1,
        "chunk_index": 0,
        "content": "Relevant text...",
        "relevance_score": 0.95
      }
    ],
    "timestamp": "2023-01-01T00:00:01"
  }
]
```

### Chat Interaction

#### POST /api/chat
Send a message and get an AI response.

**Request Body:**
```json
{
  "message": "What is the main topic?",
  "session_id": "uuid-string",
  "top_k": 5,
  "document_filter": ["doc-id-1", "doc-id-2"],
  "only_answer_if_sources": false
}
```

**Response:**
```json
{
  "message": "Based on the documents, the main topic is...",
  "sources": [
    {
      "document_id": "uuid-string",
      "document_name": "document.pdf",
      "page_number": 1,
      "chunk_index": 0,
      "content": "Relevant text from document...",
      "relevance_score": 0.95
    }
  ],
  "context_chunks": [
    {
      "id": "chunk-id",
      "score": 0.95,
      "document_id": "uuid-string",
      "page_number": 1,
      "chunk_index": 0,
      "content": "Full chunk content...",
      "filename": "document.pdf"
    }
  ],
  "response_time_ms": 1500,
  "session_id": "uuid-string"
}
```

### Feedback

#### POST /api/feedback
Submit user feedback for a query.

**Request Body:**
```json
{
  "session_id": "uuid-string",
  "user_feedback": 5
}
```

**Response:**
```json
{
  "message": "Feedback submitted successfully"
}
```

### Statistics

#### GET /api/stats
Get system statistics.

**Response:**
```json
{
  "documents": {
    "total": 10,
    "completed": 8,
    "processing": 2
  },
  "chunks": {
    "total": 450,
    "in_vector_db": 450
  },
  "chat": {
    "sessions": 25,
    "messages": 150
  }
}
```

## Error Responses

All endpoints return appropriate HTTP status codes:

- `200` - Success
- `400` - Bad Request (invalid input)
- `404` - Not Found
- `422` - Validation Error
- `500` - Internal Server Error

Error response format:
```json
{
  "detail": "Error description"
}
```

## Rate Limiting

Currently, no rate limiting is implemented. In production, consider implementing rate limiting based on user sessions or IP addresses.

## File Upload Limits

- **File Types**: PDF only
- **File Size**: Maximum 50MB
- **Processing**: Asynchronous background processing
- **Status Tracking**: Real-time status updates via the documents endpoint
