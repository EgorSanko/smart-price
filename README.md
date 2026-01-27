# 🛒 Smart Price

AI-powered price comparison and shopping assistant for Russian marketplaces.

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## Features

- 🔍 **Meta-search** across Ozon, Wildberries, Yandex.Market, AliExpress
- 💰 **Price comparison** for the same product across marketplaces
- 📈 **Price history** with trends and analytics
- 🤖 **AI assistant** powered by Claude for smart shopping
- 📸 **Image search** using CLIP embeddings
- 🔔 **Price alerts** when prices drop
- 📊 **Analytics dashboard** with insights

## Tech Stack

| Layer | Technology |
|-------|------------|
| **API** | FastAPI, Pydantic v2 |
| **Database** | PostgreSQL 16, SQLAlchemy 2.0 |
| **Cache** | Redis 7 |
| **Vector Search** | Qdrant |
| **Analytics** | ClickHouse |
| **Background Jobs** | Celery |
| **AI/ML** | Claude API, Sentence Transformers, CLIP |
| **Frontend** | Next.js 14, TailwindCSS, shadcn/ui |

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.11+ (for local development)
- Node.js 20+ (for frontend)

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/smart-price.git
cd smart-price
```

### 2. Set up environment variables

```bash
# Backend
cp backend/.env.example backend/.env

# Docker
cp docker/.env.example docker/.env

# Edit the files with your settings
```

### 3. Start with Docker Compose

```bash
# Start all services
cd docker
docker-compose -f docker-compose.dev.yml up -d

# Check status
docker-compose -f docker-compose.dev.yml ps

# View logs
docker-compose -f docker-compose.dev.yml logs -f backend
```

### 4. Access the services

| Service | URL | Description |
|---------|-----|-------------|
| API | http://localhost:8000 | FastAPI backend |
| API Docs | http://localhost:8000/docs | Swagger UI |
| Frontend | http://localhost:3000 | Next.js app |
| Adminer | http://localhost:8080 | Database UI |
| Redis Commander | http://localhost:8081 | Redis UI |

## Development

### Backend

```bash
cd backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# or
.venv\Scripts\activate  # Windows

# Install dependencies
pip install -e ".[dev]"

# Run migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Linting & Formatting

```bash
# Format code
ruff format .

# Check linting
ruff check .

# Type checking
mypy app
```

### Testing

```bash
# Run all tests
pytest

# With coverage
pytest --cov=app --cov-report=html

# Specific test file
pytest tests/test_api/test_products.py -v
```

### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build
```

## Project Structure

```
smart-price/
├── backend/              # FastAPI backend
│   ├── app/
│   │   ├── api/          # API endpoints
│   │   ├── core/         # Core utilities
│   │   ├── db/           # Database models
│   │   ├── schemas/      # Pydantic schemas
│   │   ├── services/     # Business logic
│   │   ├── scrapers/     # Marketplace scrapers
│   │   ├── ml/           # ML components
│   │   └── agents/       # AI agents
│   ├── tests/
│   └── alembic/          # Migrations
├── frontend/             # Next.js frontend
├── docker/               # Docker configuration
├── ml-experiments/       # Jupyter notebooks
└── docs/                 # Documentation
```

## API Documentation

Full API documentation is available at `/docs` (Swagger UI) or `/redoc` when the server is running.

### Key Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/products` | List products |
| GET | `/api/v1/products/{id}` | Get product details |
| GET | `/api/v1/search` | Search products |
| POST | `/api/v1/chat` | Chat with AI assistant |
| GET | `/api/v1/analytics/trends` | Price trends |

## Environment Variables

See `.env.example` files for all available configuration options.

Key variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `DEBUG` | Enable debug mode | `false` |
| `DATABASE_URL` | PostgreSQL connection | - |
| `REDIS_URL` | Redis connection | - |
| `ANTHROPIC_API_KEY` | Claude API key | - |
| `SECRET_KEY` | JWT secret | - |

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'feat: add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/)
- [Anthropic Claude](https://www.anthropic.com/)
- [Qdrant](https://qdrant.tech/)
- [shadcn/ui](https://ui.shadcn.com/)
