# FastAPI AI Chat Platform

A full-stack **AI-powered chat application** built with **FastAPI** and **React**, focusing on real-world backend architecture, security, scalability, and clean code practices.

This project demonstrates advanced backend concepts such as authentication, real-time communication, rate limiting, AI integrations, and full test coverage.

---

## ✨ Key Features

### 🔐 Authentication & Security

* User **signup & signin** using **JWT-based authentication**
* Secure password hashing with **Argon2**
* **Google reCAPTCHA** validation on both frontend and backend
* CORS configuration to safely connect frontend and backend

### 🤖 AI Chat System

* Multiple AI providers with a unified interface:

  * **Google Gemini**
  * **Groq**
  * **OpenAI** (code implemented, currently disabled due to API key limitations)
* Clean abstraction layer for AI providers using a base AI interface
* System prompt support via markdown file

### ⚡ Real-Time Chat

* **WebSocket-based real-time chat**
* Chat stays synchronized across multiple browser tabs without refreshing
* Persistent chat history stored in the database

### 🚦 Rate Limiting

* Request rate limiting using **FastAPI-Limiter**
* **Redis** used as the rate-limiting backend
* Protects AI endpoints from abuse

### 🗄️ Database & Migrations

* Database modeling using **SQLModel**
* Data validation using **Pydantic**
* Database migrations handled with **Alembic**
* PostgreSQL as the main database

### 🧱 Clean Architecture

* Repository pattern for separating business logic from API layers
* Modular project structure
* Clear separation of concerns (API, models, schemas, repositories, core utilities)

### 🧪 Testing

* Comprehensive test suite using **pytest**
* Unit tests and integration tests
* Async testing support with `pytest-asyncio`

### 🎨 Frontend

* Built with **React + Tailwind CSS**
* Generated and customized using **Lovable**
* Communicates with backend via REST APIs .

### Containerization & DevOps

* Full-stack Orchestration: Entire ecosystem managed via Docker Compose.
* Isolated Environments: Consistent development across any machine.
* Network Security: Containers communicate over a private Docker bridge network.
* Multi-stage Builds: Optimized images for both Frontend (Vite) and Backend (FastAPI).

---

## 🏗️ Project Structure

```
multiai-chat-platform/
├── backend/
│   ├── alembic/
│   ├── src/
│   │   ├── ai/                 # AI providers (Gemini, Groq, OpenAI)
│   │   ├── api/                # API routes (auth, chat)
│   │   ├── core/               # Config, auth, security, helpers
│   │   ├── models/             # Database models
│   │   ├── prompts/            # System prompts
│   │   ├── repositories/       # Data access layer
│   │   ├── schemas/            # Pydantic schemas
│   │   └── tests/              # Unit & integration tests
│   ├── Dockerfile              # Backend Dockerfile
│   ├── main.py
│   ├── alembic.ini
│   ├── .env
│   └── .env.example
├── frontend/                   # React + Tailwind frontend
│   └── Dockerfile              # Frontend Dockerfile
├── requirements.txt
├── docker-compose.yml          # Docker Compose config
├── .env                        # Project Root environment variables
├── .env.example                # Example for Root env variables
├── .gitignore
└── README.md
```

---

## 🛠️ Tech Stack

### Backend

* **FastAPI**
* **SQLModel & SQLAlchemy**
* **PostgreSQL**
* **Alembic**
* **Redis**
* **JWT Authentication**
* **WebSockets**
* **FastAPI-Limiter**
* **Pytest**

### AI Integrations

* Google Gemini
* Groq
* OpenAI (optional / disabled)

### Frontend

* React
* Tailwind CSS

### Containerization & DevOps

* Docker

---

## 🚀 Setup & Run


```bash
# From the root directory, run:
docker-compose up --build

# This will start both the backend and frontend services.
# Backend will automatically run migrations on start.
# Access backend at http://localhost:8000/docs
# Access frontend at http://localhost:5173
# Database (External): localhost:5433 (mapped from container 5432)


# Run the migrations inside the running backend container:
docker compose exec backend alembic upgrade head

# Run tests
docker compose exec backend pytest

# To stop the services:
docker-compose down
```

---

## 📄 License

This project is for learning and portfolio purposes.
