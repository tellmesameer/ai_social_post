
# AI Social Post Generator

An intelligent system that transforms any article into engaging LinkedIn posts with AI-generated images. This application uses advanced language models to create compelling social media content complete with custom visuals.

## Features

- **Article Scraping**: Extract content from any URL
- **AI-Powered Summarization**: Generate concise summaries and key points
- **Post Variants**: Create two distinct LinkedIn post options (A/B variants)
- **Image Generation**: Generate custom images for each post variant
- **Content Moderation**: Ensure all content meets professional standards
- **LinkedIn Integration**: Publish posts directly to LinkedIn
- **Regeneration Options**: Regenerate text, images, or both as needed
- **Responsive UI**: Clean, intuitive interface built with Streamlit

## Prerequisites

- Python 3.9+
- Google API key (for Vertex AI) or OpenAI API key
- LinkedIn Developer credentials (for publishing)

## Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/ai-social-post-generator.git
   cd ai-social-post-generator
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r backend/requirements.txt
   pip install -r frontend/requirements.txt
   ```

4. **Set up environment variables**
   Create a `.env` file in the project root:
   ```env
   # Google Vertex AI
   GOOGLE_API_KEY=your_google_api_key
   GOOGLE_APPLICATION_CREDENTIALS=path/to/credentials.json
   VERTEX_PROJECT=your_project_id
   VERTEX_LOCATION=us-central1

   # OpenAI (fallback)
   OPENAI_API_KEY=your_openai_api_key

   # LinkedIn
   LINKEDIN_CLIENT_ID=your_linkedin_client_id
   LINKEDIN_CLIENT_SECRET=your_linkedin_client_secret
   ```

## Usage

### Quick Start

1. **Start the application**
   ```bash
   python run.py
   ```

2. **Open your browser**
   - Frontend: http://localhost:8501
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

### Using the Application

1. **Create a new post**
   - Enter the URL of an article
   - Select your opinion (agree, disagree, neutral, or custom)
   - Choose the tone (professional, conversational, etc.)
   - Configure image generation options

2. **Review generated content**
   - View two post variants (A and B)
   - Check generated images for each variant
   - Edit text as needed

3. **Publish or regenerate**
   - Publish directly to LinkedIn
   - Regenerate text, images, or both if needed

### API Usage

The backend provides a RESTful API with the following endpoints:

- `POST /api/v1/posts` - Create a new post generation job
- `GET /api/v1/posts/{job_id}` - Get job status and results
- `POST /api/v1/posts/{job_id}/regenerate` - Regenerate content
- `POST /api/v1/posts/{job_id}/publish` - Publish to LinkedIn
- `GET /api/v1/health` - Health check endpoint

For detailed API documentation, visit http://localhost:8000/docs when the backend is running.

## Project Structure

```
ai-social-post-generator/
├── backend/                 # FastAPI backend
│   ├── api.py              # API endpoints
│   ├── config.py           # Configuration settings
│   ├── logger_config.py    # Logging configuration
│   ├── main.py             # FastAPI application
│   ├── models.py           # Database models
│   ├── prompts.py          # LangChain prompts
│   ├── providers.py        # AI provider adapters
│   ├── requirements.txt    # Python dependencies
│   ├── services.py         # Business logic
│   ├── storage.py          # File storage utilities
│   └── utils.py            # Utility functions
├── frontend/               # Streamlit frontend
│   ├── api_client.py       # API client
│   ├── config.py           # Frontend configuration
│   ├── image_utils.py      # Image handling utilities
│   ├── main.py             # Main application
│   ├── requirements.txt    # Python dependencies
│   ├── streamlit_app.py    # Streamlit entry point
│   └── ui_components.py    # UI components
├── scripts/                # Helper scripts
│   ├── cleanup_tmp.py      # Clean temporary files
│   └── start_local.sh      # Local development startup
├── tmp/                    # Temporary storage (created at runtime)
├── run.py                  # Application runner
└── README.md               # This file
```

## Configuration

### Backend Configuration

The backend uses environment variables for configuration. Key settings include:

- `GOOGLE_API_KEY`: Google API key for Vertex AI
- `OPENAI_API_KEY`: OpenAI API key (fallback)
- `LINKEDIN_CLIENT_ID`: LinkedIn application client ID
- `LINKEDIN_CLIENT_SECRET`: LinkedIn application client secret
- `DATABASE_URL`: Database connection string (default: SQLite)

### Frontend Configuration

The frontend configuration is in `frontend/config.py`:

- `API_BASE_URL`: Backend API URL (default: http://localhost:8000)
- `MAX_WAIT_TIME`: Maximum time to wait for job completion (default: 120 seconds)
- `POLL_INTERVAL`: Status check interval (default: 2 seconds)

## Development

### Running in Development Mode

1. **Start the backend**
   ```bash
   cd backend
   python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

2. **Start the frontend**
   ```bash
   cd frontend
   streamlit run streamlit_app.py --server.port 8501
   ```

### Testing

To run tests (if implemented):
```bash
pytest
```

### Code Style

This project follows PEP 8 style guidelines. We use tools like `black` and `flake8` for code formatting and linting.

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) for the backend framework
- [Streamlit](https://streamlit.io/) for the frontend framework
- [LangChain](https://langchain.com/) for AI orchestration
- [Google Vertex AI](https://cloud.google.com/vertex-ai) and [OpenAI](https://openai.com/) for AI models
- [LinkedIn API](https://learn.microsoft.com/en-us/linkedin/) for social media integration

## Support

If you encounter any issues or have questions, please open an issue on GitHub.