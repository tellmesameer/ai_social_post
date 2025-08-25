# 🚀 AI Social Post Generator

Transform any article into engaging LinkedIn posts with AI-generated images using LangChain, Vertex AI, and OpenAI.

## ✨ Features

- **🔗 URL Scraping** - Automatically extract content from any article
- **🤖 AI Summarization** - Generate concise summaries using LangChain
- **📝 Post Generation** - Create A/B testing variants with professional tone
- **🎨 Image Generation** - AI-powered visuals using Vertex Imagen or DALL-E
- **✅ Content Moderation** - Safety checks before publishing
- **📤 LinkedIn Ready** - Optimized posts for professional networking
- **🔄 A/B Testing** - Compare two post variants for better engagement

## 🏗️ Architecture

```
ai-social-post-generator/
├── backend/                 # FastAPI backend
│   ├── main.py            # FastAPI app entry point
│   ├── api.py             # REST API endpoints
│   ├── services.py        # Business logic & job pipeline
│   ├── providers.py       # AI provider abstraction (Vertex/OpenAI)
│   ├── prompts.py         # LangChain prompt templates
│   ├── models.py          # Database models (SQLModel)
│   ├── storage.py         # File management & cleanup
│   └── config.py          # Configuration & settings
├── frontend/               # Streamlit frontend
│   ├── streamlit_app.py   # Main app with navigation
│   ├── pages/             # Page components
│   └── components/        # Reusable UI components
├── scripts/                # Utility scripts
└── tmp/                    # Temporary job files
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Virtual environment
- API keys (optional for development)

### 1. Setup Environment

```bash
# Clone the repository
git clone <repository-url>
cd ai-social-post-generator

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r backend/requirements.txt
pip install -r frontend/requirements.txt
```

### 2. Configuration

Create a `.env` file in the root directory:

```env
# AI Providers
GOOGLE_APPLICATION_CREDENTIALS=/path/to/gcp-creds.json
VERTEX_PROJECT=your-project-id
VERTEX_LOCATION=us-central1
OPENAI_API_KEY=sk-your-openai-key

# LinkedIn (optional)
LINKEDIN_CLIENT_ID=your-linkedin-client-id
LINKEDIN_CLIENT_SECRET=your-linkedin-client-secret

# App Settings
API_BASE=http://localhost:8000
PRIMARY_PROVIDER=vertex  # or openai
ENABLE_FALLBACK=true
```

### 3. Start the Application

#### Option A: Using the startup script (recommended)

```bash
# Make script executable (Unix/Mac)
chmod +x scripts/start_local.sh

# Start both backend and frontend
./scripts/start_local.sh
```

#### Option B: Manual startup

```bash
# Terminal 1: Start backend
cd backend
uvicorn main:app --reload --port 8000

# Terminal 2: Start frontend
cd frontend
streamlit run streamlit_app.py --server.port 8501
```

### 4. Access the Application

- **Frontend**: http://localhost:8501
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## 🔧 Development

### Project Structure

- **Backend**: FastAPI with SQLModel, LangChain integration
- **Frontend**: Streamlit with modular components
- **Database**: SQLite (development) / PostgreSQL (production)
- **AI Providers**: Vertex AI (primary), OpenAI (fallback)

### Key Components

#### LangChain Integration

The application uses LangChain for:
- **Prompt Management**: Structured prompts for different tasks
- **Provider Abstraction**: Seamless switching between AI providers
- **Content Generation**: Consistent, high-quality output

#### Job Pipeline

1. **URL Scraping** → Extract article content
2. **AI Summarization** → Generate key points
3. **Post Generation** → Create A/B variants
4. **Image Generation** → AI-powered visuals
5. **Content Moderation** → Safety checks
6. **Result Storage** → Save to temporary directory

### Adding New Features

#### Custom AI Providers

Extend `backend/providers.py`:

```python
class CustomProvider(BaseProvider):
    def generate_text(self, prompt: str, **kwargs) -> str:
        # Your implementation
        pass
    
    def generate_image(self, prompt: str, **kwargs) -> bytes:
        # Your implementation
        pass
```

#### New Prompt Templates

Add to `backend/prompts.py`:

```python
CUSTOM_PROMPT = PromptTemplate(
    input_variables=["input_var"],
    template="Your prompt template here: {input_var}"
)
```

## 🧪 Testing

### Run Tests

```bash
# Backend tests
cd backend
python -m pytest tests/

# Frontend tests (if implemented)
cd frontend
python -m pytest tests/
```

### Test API Endpoints

```bash
# Health check
curl http://localhost:8000/health

# Create post job
curl -X POST "http://localhost:8000/api/v1/posts" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com/article",
    "opinion": "Agree — solid arguments",
    "tone": "professional",
    "image_options": {
      "style": "photographic",
      "aspect_ratio": "16:9"
    }
  }'
```

## 📊 Monitoring & Maintenance

### Cleanup Temporary Files

```bash
# Clean files older than 24 hours
python scripts/cleanup_tmp.py

# Dry run to see what would be cleaned
python scripts/cleanup_tmp.py --dry-run

# Custom age threshold
python scripts/cleanup_tmp.py --max-age 48
```

### Logs

- **Backend logs**: `logs/backend.log`
- **Frontend logs**: `logs/frontend.log`

### Health Checks

- Backend: `GET /health`
- Frontend: Built-in health check in sidebar

## 🚀 Deployment

### Production Considerations

1. **Environment Variables**: Use proper secret management
2. **Database**: Switch to PostgreSQL for production
3. **File Storage**: Use cloud storage (S3, GCS) instead of local tmp
4. **Monitoring**: Add logging, metrics, and alerting
5. **Security**: Implement authentication and rate limiting

### Docker Deployment

```dockerfile
# Example Dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

- **Issues**: Create a GitHub issue
- **Documentation**: Check the API docs at `/docs`
- **Community**: Join our discussions

## 🙏 Acknowledgments

- **LangChain** for AI orchestration
- **Vertex AI** for Gemini and Imagen
- **OpenAI** for GPT and DALL-E
- **FastAPI** for the robust backend
- **Streamlit** for the beautiful frontend

---

**Built with ❤️ using modern AI technologies**
