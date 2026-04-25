# AICES - Adaptive Concept Studio

[![Live Demo](https://img.shields.io/badge/Live%20Demo-chatbot--aices.vercel.app-0f766e?logo=vercel&logoColor=white)](https://chatbot-aices.vercel.app)
[![React](https://img.shields.io/badge/React-18%2B-61DAFB?logo=react&logoColor=061a1c)](https://react.dev/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Vercel](https://img.shields.io/badge/Vercel-Frontend-000000?logo=vercel&logoColor=white)](https://vercel.com/)
[![Render](https://img.shields.io/badge/Render-Backend-5A67D8?logo=render&logoColor=white)](https://render.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-16a34a.svg)](LICENSE)

AICES is an AI-powered adaptive learning tutor that combines conversational teaching, multilingual support, quiz generation, and learner progress tracking in one full-stack experience.

Live demo: https://chatbot-aices.vercel.app

Backend note: the production frontend is deployed on Vercel and connects to a FastAPI backend deployed separately on Render.

## Features

- AI tutor chat for guided concept explanations
- English, Hindi, and Hinglish support
- Topic detection for focused tutoring responses
- Quiz generation and answer evaluation
- Learning dashboard with mastery and weak-topic tracking
- Recent chat memory for continuity
- Adaptive recommendations based on learner activity

## Tech Stack

### Frontend

- React 18
- Vite
- React Router
- Axios
- Tailwind CSS
- Vercel deployment

### Backend

- FastAPI
- Python
- SQLAlchemy
- SQLite for local/demo persistence
- OpenRouter for AI responses and quiz generation
- Render deployment

## Project Structure

```text
.
|-- backend/
|   |-- routes/
|   |-- services/
|   |-- database.py
|   |-- main.py
|   |-- models.py
|   `-- schemas.py
|-- frontend/
|   |-- src/
|   |-- .env.example
|   |-- package.json
|   `-- vercel.json
|-- docs/
|   `-- index.html
|-- .env.example
|-- DEPLOYMENT.md
|-- render.yaml
|-- requirements.txt
`-- README.md
```

## Local Setup

### Prerequisites

- Python 3.9+
- Node.js 18+
- npm

### 1. Clone and install backend

```bash
git clone https://github.com/OMKAR580/Chatbot-AICES.git
cd Chatbot-AICES

python -m venv .venv

# Windows PowerShell
.venv\Scripts\Activate.ps1

# macOS / Linux
# source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
```

Update `.env` with your actual API credentials before running the backend.

### 2. Install frontend

```bash
cd frontend
npm install
cp .env.example .env.local
cd ..
```

### 3. Run the app locally

Start the FastAPI backend from the project root:

```bash
uvicorn backend.main:app --reload
```

Start the React frontend in a second terminal:

```bash
cd frontend
npm run dev
```

Default local URLs:

- Frontend: `http://localhost:5173`
- Backend: `http://127.0.0.1:8000`
- Health check: `http://127.0.0.1:8000/health`

## Environment Variables

### Backend `.env`

```env
OPENROUTER_API_KEY=your_openrouter_api_key_here
OPENROUTER_MODEL=mistralai/mistral-7b-instruct
OPENROUTER_TIMEOUT_SECONDS=8
AICES_DB_PATH=./data/aices.db
ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173,https://chatbot-aices.vercel.app
```

Optional production database:

```env
# DATABASE_URL=postgresql+psycopg://user:password@host:5432/aices
```

### Frontend `frontend/.env.local`

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
VITE_AICES_USER_ID=user_001
```

## Deployment

### Vercel frontend

1. Import the repository into Vercel.
2. Set the root directory to `frontend`.
3. Build command: `npm run build`
4. Output directory: `dist`
5. Add `VITE_API_BASE_URL` pointing to your Render backend URL.

### Render backend

1. Create a new Render web service from this repository.
2. Use the included [`render.yaml`](render.yaml) or configure manually:
   - Build command: `pip install -r requirements.txt`
   - Start command: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
3. Set required environment variables:
   - `OPENROUTER_API_KEY`
   - `OPENROUTER_MODEL`
   - `OPENROUTER_TIMEOUT_SECONDS`
   - `ALLOWED_ORIGINS`
   - `AICES_DB_PATH` or `DATABASE_URL`

See [DEPLOYMENT.md](DEPLOYMENT.md) for the longer deployment walkthrough.

## Screenshots

Screenshot placeholders for a portfolio-ready repo:

- Chat experience
- Quiz flow
- Learning dashboard

Add captured product images to `docs/` or a future `docs/assets/` folder and link them here.

## Author

Omkar

- GitHub: [OMKAR580](https://github.com/OMKAR580)
- Repository: [OMKAR580/Chatbot-AICES](https://github.com/OMKAR580/Chatbot-AICES)

## License

This project is released under the [MIT License](LICENSE).
