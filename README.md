# AICES — Adaptive Concept Studio

[![GitHub](https://img.shields.io/badge/GitHub-OMKAR580%2FChatbot--AICES-blue?logo=github)](https://github.com/OMKAR580/Chatbot-AICES)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.9%2B-blue?logo=python)](https://www.python.org/)
[![React](https://img.shields.io/badge/React-18%2B-blue?logo=react)](https://react.dev)

An AI-powered adaptive learning chatbot that dynamically adjusts to each learner's pace and comprehension level.

## 🌐 Live Demo

| Platform | Link | Status |
|----------|------|--------|
| **Frontend** | [Vercel](https://vercel.com) *(Deploy to get link)* | ⏳ Ready to deploy |
| **Backend** | [Render](https://render.com) *(Deploy to get link)* | ⏳ Ready to deploy |

**Quick Deploy:** See [DEPLOYMENT.md](DEPLOYMENT.md) for step-by-step guides

## Features

- 🤖 **AI-Powered Explanations** — Real-time adaptive concept explanations using OpenAI
- 🎯 **Intelligent Quizzes** — Adaptive quiz generation based on learner level
- 📊 **Progress Tracking** — Mastery percentages, weak areas, and learning analytics
- 🎓 **Adaptive Learning Path** — System adjusts difficulty based on performance
- 💬 **Multi-Language Support** — Hinglish and English support
- 🌙 **Dark Neon UI** — Modern, responsive React interface
- 📱 **Real-Time Chat** — Interactive chat with streaming responses
- 💾 **Learning History** — Persistent conversation and quiz history

## Tech Stack

### Backend
- **Framework:** FastAPI (Python)
- **Database:** SQLite (local) / PostgreSQL (production)
- **AI Engine:** OpenAI API (gpt-4o-mini)
- **ORM:** SQLAlchemy

### Frontend
- **Framework:** React 18 + Vite
- **Styling:** Tailwind CSS
- **HTTP Client:** Axios
- **Router:** React Router v6

## Project Structure

```
aices/
├── backend/                    # FastAPI backend
│   ├── main.py                # App entrypoint
│   ├── database.py            # SQLAlchemy setup
│   ├── models.py              # ORM models
│   ├── schemas.py             # Pydantic schemas
│   ├── routes/                # API endpoints
│   │   ├── chat.py
│   │   ├── quiz.py
│   │   ├── history.py
│   │   ├── progress.py
│   │   ├── recommendations.py
│   │   └── user.py
│   └── services/              # Business logic
│       ├── ai_service.py      # OpenAI integration
│       ├── adaptation_engine.py
│       ├── recommendation_engine.py
│       └── topic_utils.py
├── frontend/                   # React + Vite frontend
│   ├── src/
│   │   ├── main.jsx
│   │   ├── App.jsx
│   │   ├── pages/            # Page components
│   │   ├── components/       # Reusable UI components
│   │   ├── services/         # API calls
│   │   └── utils/            # Helpers
│   ├── public/
│   ├── package.json
│   └── vite.config.js
├── data/                       # SQLite databases
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

## Local Setup

### Prerequisites
- Python 3.9+
- Node.js 18+
- pip
- npm

### 1. Backend Setup

```bash
# Clone repository
git clone https://github.com/yourusername/aices.git
cd aices

# Create Python virtual environment
python -m venv .venv

# Activate virtual environment
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env

# Edit .env with your OpenAI API key
nano .env  # or use your preferred editor
```

### 2. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Copy environment file
cp .env.example .env.local

# Optional: Edit if using custom backend URL
nano .env.local
```

## Running Locally

### Start Backend

```bash
# From project root
.venv\Scripts\activate  # or `source .venv/bin/activate` on macOS/Linux
python -m uvicorn backend.main:app --reload
```

Backend will be available at: `http://127.0.0.1:8000`

Health check: `curl http://127.0.0.1:8000/health`

### Start Frontend

```bash
cd frontend
npm run dev
```

Frontend will be available at: `http://localhost:5173`

## Environment Variables

### Backend (.env)

```env
OPENAI_API_KEY=sk-...                    # Your OpenAI API key
OPENAI_MODEL=gpt-4o-mini                 # Model to use
AICES_DB_PATH=./data/aices.db            # Database path
ALLOWED_ORIGINS=http://localhost:5173    # CORS origins (comma-separated)
```

### Frontend (.env.local)

```env
VITE_API_BASE_URL=http://127.0.0.1:8000  # Backend URL
VITE_AICES_USER_ID=user_001              # Demo user ID
```

## API Overview

### Health Check
- `GET /health` — Service health status

### User Management
- `POST /user/create` — Create/register user
- `GET /user/{user_id}` — Get user profile

### Chat
- `POST /chat` — Send chat message and get AI response

### Quiz
- `POST /quiz/generate` — Generate adaptive quiz
- `POST /quiz/submit` — Submit quiz answers

### History
- `GET /history/{user_id}` — Get chat history
- `GET /quiz-results/{user_id}` — Get quiz results

### Progress
- `GET /progress/{user_id}` — Get learner progress
- `GET /progress/{user_id}/{topic}` — Get topic mastery

### Recommendations
- `GET /recommendations/{user_id}` — Get learning recommendations

## Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed deployment instructions.

### Quick Start

**Frontend** → Deploy to [Vercel](https://vercel.com)
- Root directory: `frontend`
- Build: `npm run build`
- Output: `dist`

**Backend** → Deploy to [Render](https://render.com) or [Railway](https://railway.app)
- Build: `pip install -r requirements.txt`
- Start: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`

## Development

### Running Tests

```bash
# Python syntax check
python -B -m compileall backend

# Frontend build check
cd frontend && npm run build
```

### Code Style

- **Backend:** Follow PEP 8 (FastAPI conventions)
- **Frontend:** ESM modules, React best practices

## Future Improvements

- [ ] User authentication (JWT)
- [ ] PostgreSQL migration script
- [ ] Advanced analytics dashboard
- [ ] Spaced repetition algorithm
- [ ] Mobile app (React Native)
- [ ] Real-time collaboration
- [ ] Offline mode with sync
- [ ] Advanced LLM function calling

## License

MIT License — See LICENSE file for details

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Support

For issues, feature requests, or questions:
- Open an issue on GitHub
- Check existing documentation
- Review API endpoint examples

---

**AICES** — Making adaptive learning accessible to everyone.
