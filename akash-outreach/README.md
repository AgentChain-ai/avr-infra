# Akash Institute Outreach System

## 🎯 Overview
Intelligent voice-based bot system to automatically contact parents of Akash Institute Anthe test scholarship recipients.

## 🚀 Quick Setup

### 1. Create Virtual Environment
```bash
cd akash-outreach/
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Environment Configuration
Copy the root `.env.example` to `.env` and configure:
```bash
cp ../.env.example ../.env
```

Edit the `.env` file and set at minimum:
```env
OPENAI_API_KEY=sk-your-openai-key-here
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your-secure-password
```

### 4. Initialize Database
```bash
python init_database.py
```

### 5. Run the Application

**Option A: Development Mode (2 terminals)**
```bash
# Terminal 1 - API Backend
uvicorn app.main:app --reload --port 8000

# Terminal 2 - Streamlit Dashboard  
streamlit run app/streamlit_app.py --server.port 8501
```

**Option B: Single Command (when streamlit_app.py is ready)**
```bash
python app/main.py
```

## 🔗 Access Points
- **API Documentation**: http://localhost:8000/docs
- **Admin Dashboard**: http://localhost:8501
- **API Health Check**: http://localhost:8000/health

## 📁 Project Structure
```
akash-outreach/
├── app/
│   ├── main.py              # FastAPI backend
│   ├── config.py            # Configuration management
│   ├── database.py          # SQLite3 setup and models
│   ├── models/              # SQLAlchemy models
│   ├── api/                 # API route handlers
│   ├── services/            # Business logic and AI services
│   └── ui/                  # Streamlit pages
├── data/                    # Data storage
├── requirements.txt         # Python dependencies
├── Dockerfile              # Container setup
└── init_database.py        # Database initialization
```

## ✅ Phase 1 Status
- [x] Project structure created
- [x] SQLite3 database models defined
- [x] Configuration management setup
- [x] Basic FastAPI backend with health checks
- [x] Database initialization script
- [ ] API endpoints implementation (Day 2)
- [ ] AI CSV processing service (Day 2-3)
- [ ] Streamlit dashboard (Phase 2)

## 🧪 Testing
```bash
# Test database initialization
python init_database.py

# Test API server
uvicorn app.main:app --reload --port 8000
# Then visit: http://localhost:8000/docs

# Run tests (when available)
pytest tests/
```

## 🐳 Docker (Alternative)
```bash
# Build and run with Docker
docker build -t akash-outreach .
docker run -p 8000:8000 -p 8501:8501 akash-outreach
```

## 🔧 Environment Variables
Key environment variables (set in root `.env`):
- `OPENAI_API_KEY` - Required for AI services
- `ADMIN_USERNAME/PASSWORD` - Admin credentials
- `AKASH_DATABASE_URL` - SQLite database path
- `AVR_CORE_URL` - AVR Core service URL
- `AKASH_DEBUG` - Debug mode (true/false)

## 📚 Next Steps
1. Install dependencies in your virtual environment
2. Configure environment variables
3. Run database initialization
4. Test the API backend
5. Continue with Phase 1 Day 2 implementation
