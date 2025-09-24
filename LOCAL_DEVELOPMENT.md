# Local Development Quick Start

## Setup for Local Development

If you want to run the services locally (without Docker), follow these steps:

### 1. Environment Setup
```bash
# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-frontend.txt

# Setup environment variables
cp .env.example .env
# Edit .env with your Gemini API key
```

### 2. Start Services

#### Option A: Use Docker (Recommended)
```bash
# Start all services with Docker
docker-compose up -d

# Verify deployment
python scripts/verify_deployment.py
```

#### Option B: Run Locally
```bash
# Start PostgreSQL and Qdrant with Docker
docker-compose up -d postgres qdrant

# Start backend API
./scripts/start_backend.sh

# In another terminal, start frontend
streamlit run frontend/app.py --server.address 0.0.0.0 --server.port 8501
```

### 3. Access the Application
- **Frontend**: http://localhost:8501
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## Troubleshooting

### Import Errors
If you get import errors when running locally, make sure you:
1. Are in the project root directory
2. Have activated your virtual environment
3. Use the provided startup scripts

### Database Connection Issues
- Ensure PostgreSQL and Qdrant are running (via Docker or locally)
- Check your `.env` file for correct connection strings
- Verify services with: `docker-compose ps`

### API Key Issues
- Make sure your `.env` file has a valid `GEMINI_API_KEY`
- The API key should have access to the Gemini API
- Check for any trailing spaces or quote marks in the key
