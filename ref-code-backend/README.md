# RAG Agent Backend

This is the backend service for the USFS RAG Agent application, built with FastAPI and Google ADK.

## Structure

```
backend/
├── src/
│   ├── api/
│   │   ├── server.py          # Main FastAPI application
│   │   ├── routes/            # API route modules
│   │   └── middleware/        # Custom middleware
│   ├── rag_agent/
│   │   ├── agent.py           # ADK agent configuration
│   │   ├── config.py          # Configuration settings
│   │   └── tools/             # RAG tools (query, corpus management)
│   └── database/
│       └── models.py          # Database models
├── tests/                     # Unit and integration tests
├── Dockerfile                 # Container configuration
├── requirements.txt           # Python dependencies
├── cloudbuild.yaml           # Google Cloud Build configuration
└── README.md                 # This file
```

## Environment Variables

### Vertex AI
- `PROJECT_ID`: Google Cloud project ID
- `GOOGLE_CLOUD_LOCATION`: Vertex AI location (e.g., us-central1)
- `GOOGLE_GENAI_USE_VERTEXAI`: Set to "true" to use Vertex AI
- `VERTEXAI_PROJECT`: Vertex AI project ID
- `VERTEXAI_LOCATION`: Vertex AI location

### Database (PostgreSQL Only)
- `DB_HOST`: PostgreSQL host (localhost or /cloudsql/...)
- `DB_PORT`: PostgreSQL port (5432)
- `DB_NAME`: Database name (adk_agents_db)
- `DB_USER`: Database user (adk_app_user)
- `DB_PASSWORD`: Database password
- `CLOUD_SQL_CONNECTION_NAME`: Cloud SQL connection name (for production)

### Other
- `LOG_LEVEL`: Logging level (INFO, DEBUG, etc.)

## Development

### Prerequisites
- Docker and Docker Compose (for PostgreSQL)
- Python 3.11+

### Setup

1. Start PostgreSQL:
   ```bash
   docker-compose up -d postgres
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set environment variables:
   ```bash
   cp .env.example .env.local
   # Edit .env.local with PostgreSQL connection details
   ```

4. Run the server:
   ```bash
   python src/api/server.py
   ```

**Note:** This application uses PostgreSQL exclusively. SQLite is not supported.

## Deployment

The backend is deployed to Google Cloud Run using the deployment script in `infrastructure/deploy.sh`.
