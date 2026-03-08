<div align="center">

<img src="https://img.shields.io/badge/Hackathon-AI%20for%20Bharat-FF6B00?style=for-the-badge&logo=sparkles&logoColor=white" />
<img src="https://img.shields.io/badge/Team-PibyThree-6C63FF?style=for-the-badge" />
<img src="https://img.shields.io/badge/Status-Prototype-brightgreen?style=for-the-badge" />

# 🛍️ PibyThree ShopSense AI — Intelligent Retail Platform

### *An AI-First E-Commerce Experience, Built for India*

> **Team PibyThree** · Submission for **AI for Bharat Hackathon**

</div>

---

## 📌 Table of Contents

- [🌟 Overview](#-overview)
- [🎯 Problem Statement](#-problem-statement)
- [💡 Our Solution](#-our-solution)
- [🏗️ Architecture](#️-architecture)
- [🤖 AI Agents (Multi-Agent System)](#-ai-agents-multi-agent-system)
- [✨ Key Features](#-key-features)
- [🛠️ Tech Stack](#️-tech-stack)
- [🚀 Getting Started](#-getting-started)
- [📂 Project Structure](#-project-structure)
- [🔑 Environment Variables](#-environment-variables)
- [👥 Team PibyThree](#-team-pibythree)

---

## 🌟 Overview

**ShopSense AI** is a full-stack, AI-powered e-commerce platform that reimagines online retail with a multi-agent conversational AI assistant at its core. Customers don't just browse — they *converse*, discover, and transact in natural language. Admins get intelligent tools for dynamic pricing, demand forecasting, and AI-generated promotions.

Built end-to-end for the **AI for Bharat** hackathon, this prototype showcases how Generative AI and Agentic architectures can transform the retail experience for Indian consumers and businesses.

---

## 🎯 Problem Statement

Traditional e-commerce platforms in India suffer from:

- 🔍 **Poor product discoverability** — customers type keywords, not intentions
- 💸 **Static pricing** — missing revenue opportunities during demand spikes
- 📢 **Generic promotions** — one-size-fits-all, low conversion
- 📊 **Reactive inventory decisions** — no real-time demand signal
- 🤝 **Zero post-purchase engagement** — no intelligent review analysis

---

## 💡 Our Solution

A **multi-agent AI system** layered on top of a robust e-commerce backend that:

1. Understands **natural language shopping intent** and executes complex multi-step tasks
2. **Compares prices** with Amazon & Walmart in real-time before checkout
3. Applies **ML-driven dynamic pricing** approved by admins
4. **Predicts demand** to guide inventory and promotions
5. Generates **AI-written + AI-illustrated promotions** with one click
6. Surfaces **review insights** via RAG (Retrieval-Augmented Generation)
7. Provides **LLM observability** via Langfuse for monitoring every AI call

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    React Frontend (Vite)                  │
│  Home · Products · Cart · Orders · Admin Dashboard        │
│         ↕ REST API          ↕ AI Chat Widget              │
└─────────────────┬───────────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────────┐
│              FastAPI Backend (Python)                     │
│                                                           │
│  ┌─────────────────────────────────────────────────┐    │
│  │          LangGraph Multi-Agent System            │    │
│  │                                                   │    │
│  │  User Query → Planner Agent                      │    │
│  │                    ↓                              │    │
│  │           Orchestrator Agent                     │    │
│  │          ↙    ↓    ↘     ↘                      │    │
│  │  Product  Trans- Review  Chat                    │    │
│  │  Search   action  Agent  Agent                   │    │
│  │  Agent    Agent                                  │    │
│  └─────────────────────────────────────────────────┘    │
│                                                           │
│  REST Routers: Products · Categories · Orders · Cart      │
│                Dynamic Pricing · Demand Prediction        │
│                Promotions · Auth · Uploads                │
│                                                           │
│  ML Layer: Dynamic Pricing Model · Demand Forecast        │
│  RAG Layer: Product Reviews (FAISS Vector Store)          │
│  Observability: Langfuse Tracing                          │
└─────────────────┬───────────────────────────────────────┘
                  │
        ┌─────────▼──────────┐
        │   PostgreSQL DB     │
        │   (Docker)          │
        └────────────────────┘
```

**LLM:** AWS Bedrock — Claude Sonnet  
**Observability:** Langfuse  
**External APIs:** SerpAPI (price comparison), AWS S3 (media)

---

## 🤖 AI Agents (Multi-Agent System)

The AI backbone is a **LangGraph-powered multi-agent pipeline** where every user message flows through a coordinated set of specialised agents:

| Agent | Role | Tools |
|---|---|---|
| 🧠 **Planner Agent** | Analyses intent and creates a multi-step execution plan | LLM reasoning |
| 🎯 **Orchestrator Agent** | Routes each step to the correct agent and aggregates results | — |
| 🔍 **Product Search Agent** | Natural-language → SQL product discovery with category filters | `execute_product_search` |
| 🛒 **Transaction Agent** | Cart management, order placement, and price comparisons | `add_to_cart`, `remove_from_cart`, `place_order`, `view_cart`, `compare_prices` |
| ⭐ **Review Agent** | RAG-based sentiment analysis over customer reviews | `product_reviews_search_tool` |
| 💬 **Chat Agent** | Greetings, help, and general conversation | — |

**Example multi-intent query:**  
*"Search for laptops under ₹50,000, compare the cheapest one with Amazon, then add it to my cart"*  
→ Planner creates a 3-step plan → Orchestrator routes Product Search → Transaction (compare) → Transaction (add) → Aggregated response rendered in UI.

---

## ✨ Key Features

### 🧑‍💻 Customer Experience
- **AI Chat Assistant** — floating widget powered by the multi-agent system; handles search, cart, orders, comparisons, and reviews in one conversation
- **Personalised Promotion Carousel** — shows deals relevant to a logged-in user's purchase history and cart
- **Real-time Price Comparison** — compare any product against Amazon & Walmart before buying
- **Smart Product Search** — natural language queries converted to optimised SQL

### 🛠️ Admin Dashboard
- **Dynamic Pricing** — ML model predicts optimal prices; admin approves/rejects each change
- **Demand Prediction** — forecast demand levels (Low / Medium / High / Very High) per product
- **AI Promotion Generator** — one-click AI-written copy + AI-generated banner image (Google Gemini)
- **Full CRUD** — manage products, categories, and users with role-based access

### 🔒 Security & Observability
- JWT authentication with access + refresh token rotation
- Role-based access control (User / Admin)
- **Langfuse** integration — traces every LLM call, measures latency, monitors costs
- LangSmith tracing support

---

## 🛠️ Tech Stack

### Frontend
| Technology | Purpose |
|---|---|
| React 19 | UI Framework |
| Vite 7 | Build tool & dev server |
| React Router v7 | Client-side routing |
| Axios | HTTP client |
| CSS Modules | Styling |

### Backend
| Technology | Purpose |
|---|---|
| FastAPI | REST API framework |
| SQLAlchemy 2.0 | ORM |
| PostgreSQL 15 | Primary database |
| Alembic | Database migrations |
| LangGraph | Multi-agent orchestration |
| LangChain | LLM tooling & chains |
| AWS Bedrock (Claude Sonnet) | Primary LLM |
| FAISS | Vector store for RAG |
| Google Gemini API | Promotion image generation |
| SerpAPI | Real-time price scraping |
| Langfuse | LLM observability |
| Docker | PostgreSQL containerisation |
| AWS S3 | Media storage |
| python-jose | JWT tokens |
| Passlib / bcrypt | Password hashing |

---

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+
- Docker & Docker Compose
- AWS Account (Bedrock access for Claude Sonnet)
- SerpAPI key (for price comparison)

---

### 1. Clone the Repository

```bash
git clone https://github.com/ganeshannainar/PibyThree-AIforBharat.git
cd PibyThree-AIforBharat
```

---

### 2. Backend Setup (`FastAPI-Ecommerce-API`)

```bash
cd FastAPI-Ecommerce-API

# Copy and configure environment
cp .env.example .env
# Edit .env with your credentials (DB, AWS, SerpAPI, Langfuse, etc.)

# Start PostgreSQL via Docker
docker-compose up -d

# Create virtual environment & install dependencies
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Start the API server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

API docs available at: **http://localhost:8000/docs**

---

### 3. Frontend Setup (`ecommerce-frontend`)

```bash
cd ecommerce-frontend

# Copy and configure environment
cp .env.example .env
# Edit .env — set PROD to your backend URL if deploying

# Install dependencies
npm install

# Start the dev server
npm run dev
```

App available at: **http://localhost:5173**

---

### 4. Default Admin Credentials

After seeding the database, log in with:

```
Email:    admin@example.com
Password: admin123
```

> ⚠️ Change these immediately in any non-development environment.

---

## 📂 Project Structure

```
PibyThree-AIforBharat/
├── ecommerce-frontend/          # React + Vite frontend
│   ├── src/
│   │   ├── components/          # Navbar, AIStylistChat, ProductCard, ChatWidget
│   │   ├── pages/               # Home, Products, Cart, Orders, Login, Signup
│   │   │   └── admin/           # Dashboard, DynamicPricing, DemandPrediction, Promotions
│   │   ├── context/             # AuthContext, CartContext
│   │   └── services/            # Axios API service layer
│   ├── .env.example
│   └── package.json
│
├── FastAPI-Ecommerce-API/       # FastAPI backend
│   ├── app/
│   │   ├── agents/              # Planner, Orchestrator, ProductSearch, Transaction, Review, Chat
│   │   ├── routers/             # FastAPI route handlers
│   │   ├── services/            # Business logic layer
│   │   ├── models/              # SQLAlchemy ORM models
│   │   ├── schemas/             # Pydantic request/response schemas
│   │   ├── tools/               # LangChain tools (cart, price, RAG)
│   │   ├── workflows/           # LangGraph workflow definitions
│   │   ├── core/                # Config, security, LLM init, logging
│   │   └── db/                  # Database session management
│   ├── alembic/                 # Database migration scripts
│   ├── docker-compose.yml       # PostgreSQL container
│   ├── .env.example
│   └── requirements.txt
│
└── README.md
```

---

## 🔑 Environment Variables

### Backend (`FastAPI-Ecommerce-API/.env.example`)

| Variable | Description |
|---|---|
| `db_username` | PostgreSQL username |
| `db_password` | PostgreSQL password |
| `db_hostname` | Database host (default: `localhost`) |
| `db_port` | Database port (default: `5432`) |
| `db_name` | Database name |
| `secret_key` | JWT signing secret |
| `AWS_ACCESS_KEY_ID` | AWS credentials for Bedrock + S3 |
| `AWS_SECRET_ACCESS_KEY` | AWS credentials |
| `AWS_REGION` | AWS region (e.g. `us-east-1`) |
| `LLM_MODEL_ID` | AWS Bedrock model ID |
| `GOOGLE_API_KEY` | Google Gemini API (promotion images) |
| `SERP_API_KEY` | SerpAPI key (price comparison) |
| `LANGFUSE_SECRET_KEY` | Langfuse observability |
| `LANGFUSE_PUBLIC_KEY` | Langfuse observability |
| `LANGCHAIN_API_KEY` | LangSmith tracing (optional) |

### Frontend (`ecommerce-frontend/.env.example`)

| Variable | Description |
|---|---|
| `PROD` | Backend API URL for production builds |

---

## 👥 Team PibyThree

Built with ❤️ for the **AI for Bharat** Hackathon.

| Role | Contribution |
|---|---|
| 🤖 AI / Agents | LangGraph multi-agent system, RAG pipeline, LLM integrations |
| ⚙️ Backend | FastAPI, PostgreSQL, ML models, dynamic pricing & demand prediction |
| 🎨 Frontend | React UI, admin dashboard, AI chat widget |

---

<div align="center">

**⭐ If you find this project interesting, give it a star!**

Made with 🧡 in India · Team PibyThree · AI for Bharat 2025

</div>
