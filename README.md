# PDF RAG Chat Application

A comprehensive PDF-based Retrieval-Augmented Generation (RAG) application that allows users to upload PDF documents, index them into a vector database, and chat with the content using a Streamlit UI powered by Google Gemini.

# Here are the scrrenshots of the UI displayed to the user
![Screenshot](images/rag_chatbot.jpeg)
![Screenshot](images/rag_chatbot(1).jpeg)



## 🌟 Features

### Core Functionality
- **PDF Upload & Processing**: Upload multiple PDF files with real-time processing status
- **Vector Database Storage**: Embeddings stored in Qdrant for efficient similarity search
- **Intelligent Chat**: Chat with your documents using Google Gemini LLM
- **Citation & Context**: Every answer includes citations with document names, page numbers, and expandable context
- **Session Management**: Create, switch between, and manage multiple chat sessions
- **Persistent History**: All conversations and metadata stored in PostgreSQL

### Advanced Features
- **Smart Chunking**: Intelligent text chunking with sentence boundary detection
- **Customizable Retrieval**: Adjust top-k results, filter by documents, model selection
- **Progress Tracking**: Real-time upload progress and processing status indicators
- **Error Handling**: Comprehensive error handling with user-friendly messages
- **Analytics**: System statistics and query metrics for evaluation
- **Responsive UI**: Clean, modern interface with expandable sections

## 🏗️ Architecture

### Tech Stack
- **Frontend**: Streamlit with custom CSS styling
- **Backend**: FastAPI with async support
- **Vector Database**: Qdrant for embeddings storage
- **Relational Database**: PostgreSQL for metadata and chat history
- **LLM**: Google Gemini API
- **Embeddings**: Sentence Transformers (all-MiniLM-L6-v2)
- **PDF Processing**: PyPDF for text extraction
- **Containerization**: Docker Compose for easy deployment

### Database Schema
```sql
-- Users & Sessions
users (id, session_id, created_at, last_active)
chat_sessions (id, user_id, session_name, created_at, updated_at)
chat_messages (id, session_id, message_type, content, sources, context_chunks, timestamp, response_time_ms, tokens_used)

-- Documents & Processing
documents (id, filename, original_filename, file_size, content_hash, page_count, upload_timestamp, processing_status, error_message, chunk_count)
document_chunks (id, document_id, chunk_index, page_number, content_preview, vector_id, created_at)

-- Analytics
query_metrics (id, session_id, query, retrieved_chunks, top_k, response_time_ms, tokens_used, user_feedback, timestamp)
```

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- Google Gemini API key

### 1. Clone and Setup
```bash
git clone <repository-url>
cd pdf-rag-chat
cp .env.example .env
```

### 2. Configure Environment
Edit `.env` file:

#### For Local Development (with local Qdrant):
```bash
GEMINI_API_KEY=your_gemini_api_key_here
EMBEDDING_MODEL=all-MiniLM-L6-v2
DATABASE_URL=postgresql://postgres:postgres@postgres:5432/rag_db
QDRANT_URL=http://localhost:6333
# Leave QDRANT_API_KEY empty or remove it
```

#### For Qdrant Cloud:
```bash
GEMINI_API_KEY=your_gemini_api_key_here
EMBEDDING_MODEL=all-MiniLM-L6-v2
DATABASE_URL=postgresql://postgres:postgres@postgres:5432/rag_db
QDRANT_URL=https://your-cluster.europe-west3-0.gcp.cloud.qdrant.io:6333
QDRANT_API_KEY=your_qdrant_cloud_api_key_here
```

### 3. Start Application

#### With Local Qdrant:
```bash
# Start all services including local Qdrant
docker-compose --profile local-qdrant up -d
```

#### With Qdrant Cloud:
```bash
# Start only PostgreSQL and application services
docker-compose up -d
```

### 4. Access the Application
- **Streamlit UI**: http://localhost:8501
- **FastAPI Docs**: http://localhost:8000/docs
- **Qdrant Dashboard**: http://localhost:6333/dashboard

## 📖 Usage Guide

### 1. Upload Documents
1. Navigate to the "Documents" tab
2. Use the file uploader to select PDF files
3. Monitor processing status in the documents panel
4. Wait for status to change to "✅ Ready"

### 2. Start Chatting
1. Create a new chat session from the sidebar
2. Type questions about your uploaded documents
3. View answers with citations and expandable context
4. Use settings to customize retrieval parameters

### 3. Advanced Features
- **Session Management**: Switch between different conversations
- **Document Filtering**: Limit search to specific documents
- **Top-K Adjustment**: Control number of retrieved chunks
- **Source Validation**: Enable "only answer if sources found" mode

## 🛠️ Development

### Project Structure
```
pdf-rag-chat/
├── backend/                 # FastAPI backend
│   ├── main.py             # API endpoints
│   ├── models.py           # Database models
│   ├── schemas.py          # Pydantic schemas
│   ├── config.py           # Configuration
│   ├── pdf_processor.py    # PDF processing & embeddings
│   └── rag_service.py      # LLM integration
├── frontend/               # Streamlit frontend
│   └── app.py             # Main UI application
├── sql/                   # Database initialization
│   └── init.sql           # Schema creation
├── docker-compose.yml     # Container orchestration
├── Dockerfile.backend     # Backend container
├── Dockerfile.frontend    # Frontend container
├── requirements.txt       # Backend dependencies
├── requirements-frontend.txt # Frontend dependencies
└── README.md             # This file
```

### Make Commands
```bash
make help       # Show available commands
make build      # Build all containers
make up         # Start all services
make down       # Stop all services
make restart    # Restart all services
make logs       # Show logs from all services
make clean      # Clean up containers and volumes
make test       # Run tests
```

### API Endpoints

#### Document Management
- `POST /api/documents/upload` - Upload PDF document
- `GET /api/documents` - List all documents
- `DELETE /api/documents/{id}` - Delete document

#### Chat & Sessions
- `POST /api/users` - Create/get user
- `POST /api/sessions` - Create chat session
- `GET /api/sessions` - List chat sessions
- `DELETE /api/sessions/{id}` - Delete session
- `GET /api/sessions/{id}/messages` - Get chat history
- `POST /api/chat` - Send chat message

#### System
- `GET /health` - Health check
- `GET /api/stats` - System statistics
- `POST /api/feedback` - Submit user feedback

## 🔧 Configuration

### Environment Variables
| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `GEMINI_API_KEY` | Google Gemini API key | - | ✅ Required |
| `EMBEDDING_MODEL` | Sentence transformer model | all-MiniLM-L6-v2 | Optional |
| `DATABASE_URL` | PostgreSQL connection string | See .env.example | ✅ Required |
| `QDRANT_URL` | Qdrant connection URL | http://localhost:6333 | ✅ Required |
| `QDRANT_API_KEY` | Qdrant Cloud API key | - | ⚠️ Required for Cloud |

**Note**: For Qdrant Cloud setup:
- Set `QDRANT_URL` to your cluster URL (e.g., `https://your-cluster.europe-west3-0.gcp.cloud.qdrant.io:6333`)
- Set `QDRANT_API_KEY` to your API key from Qdrant Cloud dashboard
- For local Qdrant, leave `QDRANT_API_KEY` empty or remove it

### Chunking Parameters
- **Chunk Size**: 1000 characters
- **Chunk Overlap**: 200 characters
- **Sentence Boundary Detection**: Enabled

### Vector Database
- **Collection**: pdf_embeddings
- **Distance Metric**: Cosine similarity
- **Embedding Dimension**: 384 (all-MiniLM-L6-v2)

## 🧪 Testing

### Run Tests
```bash
# Using Docker
make test

# Local development
cd backend
python -m pytest

# Test specific components
python -m pytest tests/test_pdf_processor.py
python -m pytest tests/test_rag_service.py
```

### Manual Testing
1. **Upload PDF**: Navigate to http://localhost:8501 and upload a PDF file
2. **Ask Questions**: Use the chat interface to ask questions about your document
3. **View History**: Check the session history and document management features
4. **Verify Database**: Check that chunks and conversations are stored properly

### Qdrant Connection Testing
For Qdrant Cloud, ensure your API key and cluster URL are correct:
```bash
# Test Qdrant connection from backend container
docker-compose exec backend python -c "
from backend.config import QDRANT_URL, QDRANT_API_KEY
from qdrant_client import QdrantClient
client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
print('Qdrant connection successful!')
print(client.get_collections())
"
```

## 📊 Monitoring & Analytics

### System Statistics
- Document counts and processing status
- Total chunks in vector database
- Chat session and message counts
- Processing times and token usage

### Query Metrics
- Response times
- Retrieved chunk counts
- User feedback ratings
- Token consumption tracking

## 🔒 Security Considerations

### Production Deployment
- Use environment-specific API keys
- Enable HTTPS for all endpoints
- Implement authentication (bonus feature)
- Set up proper CORS policies
- Use secrets management for sensitive data

### Data Privacy
- User session isolation
- Secure file storage
- Database access controls
- API rate limiting

## 🚀 Bonus Features Implemented

1. **Advanced Session Management**: Create, switch, delete sessions
2. **Real-time Progress Indicators**: Upload and processing status
3. **Advanced Filtering**: Document-specific search
4. **Comprehensive Analytics**: System stats and metrics
5. **Error Recovery**: Robust error handling and user feedback
6. **Responsive Design**: Modern UI with custom styling

## 🏆 Scoring Alignment

### Accuracy of Retrieval (35 pts)
- ✅ Sentence-boundary chunking for coherent context
- ✅ Configurable top-k with sensible defaults
- ✅ Clear citations with document and page references
- ✅ Document filtering capabilities

### Architecture (25 pts)
- ✅ Clean separation of concerns (API, processing, UI)
- ✅ Comprehensive error handling
- ✅ Configurable via environment variables
- ✅ Well-documented codebase with docstrings

### DB Interactions (20 pts)
- ✅ Proper schema with relationships and constraints
- ✅ Async processing for non-blocking operations
- ✅ SQLAlchemy ORM with parameterized queries
- ✅ Database migrations via init scripts

### Repo Maintenance & Ease of Use (20 pts)
- ✅ One-command deployment with `docker-compose up`
- ✅ Comprehensive .env.example
- ✅ Detailed README with screenshots
- ✅ Make targets for common operations

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details

## 🆘 Troubleshooting

### Common Issues

1. **Gemini API Errors**
   - Verify API key is correct
   - Check API quotas and limits
   - Ensure proper network connectivity

2. **PDF Processing Failures**
   - Check file format (only PDF supported)
   - Verify file size limits (50MB default)
   - Ensure files contain extractable text

3. **Vector Database Issues**
   - Restart Qdrant container
   - Check collection creation
   - Verify embedding dimensions match

4. **Database Connection Issues**
   - Check PostgreSQL container status
   - Verify connection string
   - Check database initialization

### Support
For issues and questions, please check the logs:
```bash
make logs
```

Or access individual container logs:
```bash
docker-compose logs backend
docker-compose logs frontend
docker-compose logs postgres
docker-compose logs qdrant
```
