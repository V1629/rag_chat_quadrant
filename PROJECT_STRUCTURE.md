# Project Structure

```
pdf-rag-chat/
├── README.md                      # Main documentation
├── API_DOCS.md                   # API documentation  
├── .env.example                  # Environment template
├── .gitignore                    # Git ignore rules
├── Makefile                      # Development commands
├── docker-compose.yml            # Container orchestration
├── Dockerfile.backend            # Backend container
├── Dockerfile.frontend           # Frontend container
├── requirements.txt              # Backend dependencies
├── requirements-frontend.txt     # Frontend dependencies
├── requirements-test.txt         # Testing dependencies
├── pytest.ini                   # Test configuration
│
├── backend/                      # FastAPI backend
│   ├── __init__.py              # Python package
│   ├── main.py                  # API endpoints & app setup
│   ├── models.py                # Database models (SQLAlchemy)
│   ├── schemas.py               # Pydantic schemas
│   ├── config.py                # Configuration management
│   ├── pdf_processor.py         # PDF processing & embeddings
│   └── rag_service.py           # RAG logic & Gemini integration
│
├── frontend/                     # Streamlit frontend
│   └── app.py                   # Main UI application
│
├── sql/                         # Database setup
│   └── init.sql                 # PostgreSQL initialization
│
├── scripts/                     # Utility scripts
│   ├── setup.sh                # Development setup
│   ├── load_test.py             # Load testing script
│   └── verify_deployment.py     # Deployment verification
│
├── tests/                       # Test suite
│   ├── test_pdf_processor.py    # PDF processing tests
│   └── test_rag_service.py      # RAG service tests
│
└── uploads/                     # File upload directory
    └── .gitkeep                 # Keep directory in git
```

## Component Responsibilities

### Backend (`/backend/`)
- **main.py**: FastAPI application with all REST endpoints
- **models.py**: SQLAlchemy database models for PostgreSQL
- **schemas.py**: Pydantic models for request/response validation
- **config.py**: Environment configuration and settings
- **pdf_processor.py**: PDF text extraction, chunking, and vector storage
- **rag_service.py**: Retrieval-augmented generation with Gemini

### Frontend (`/frontend/`)
- **app.py**: Complete Streamlit UI with chat, upload, and management features

### Infrastructure
- **docker-compose.yml**: Multi-container setup with PostgreSQL, Qdrant, backend, and frontend
- **sql/init.sql**: Database schema initialization
- **Dockerfiles**: Container definitions for backend and frontend

### Development & Testing
- **scripts/**: Setup, testing, and verification utilities
- **tests/**: Unit and integration tests
- **Makefile**: Common development commands
- **.env.example**: Configuration template

This structure provides clear separation of concerns, easy development workflow, and production-ready deployment capabilities.
