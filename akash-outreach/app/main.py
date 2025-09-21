"""
FastAPI backend for Akash Institute Outreach System
Main application entry point
"""
from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import uvicorn

from .config import settings, validate_environment
from .database import get_db, create_tables
from .models import Student, FieldConfiguration, CallLog, ContextInfo

# Import API routers
from .api import auth, students, fields, calls, context, analytics, voice, campaigns

app = FastAPI(
    title=settings.app_name,
    description="API for managing student outreach calls and context information",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Application startup"""
    print("🚀 Starting Akash Institute Outreach System...")
    
    try:
        # Validate environment
        validate_environment()
        print("✅ Environment validation passed")
        
        # Ensure database tables exist
        create_tables()
        print("✅ Database tables verified")
        
        # Initialize voice service
        from .services.voice_service import init_voice_service
        voice_config = {
            "avr_base_url": settings.avr_core_url,
            "avr_api_key": settings.openai_api_key,  # Using OpenAI key as placeholder
            "webhook_url": f"http://{settings.host}:{settings.port}/api/v1/voice/webhooks/call-events",
            "default_script_id": "scholarship_notification"
        }
        init_voice_service(voice_config)
        print("✅ Voice service initialized")
        
        print(f"✅ API server starting on http://{settings.host}:{settings.port}")
        print(f"📚 API Documentation: http://{settings.host}:{settings.port}/docs")
        
    except Exception as e:
        print(f"❌ Startup error: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown"""
    print("🛑 Shutting down Akash Institute Outreach System...")


# Exception handlers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    print(f"❌ Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


# Health check endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "app_name": settings.app_name,
        "version": "1.0.0"
    }


@app.get("/")
async def root():
    """Root endpoint with basic info"""
    return {
        "message": "Welcome to Akash Institute Outreach System API",
        "docs": "/docs",
        "health": "/health",
        "version": "1.0.0"
    }


# Database status endpoint
@app.get("/status/database")
async def database_status(db: Session = Depends(get_db)):
    """Check database status and counts"""
    try:
        student_count = db.query(Student).count()
        field_count = db.query(FieldConfiguration).count()
        call_count = db.query(CallLog).count()
        context_count = db.query(ContextInfo).count()
        
        return {
            "status": "connected",
            "students": student_count,
            "field_configurations": field_count,
            "call_logs": call_count,
            "context_info": context_count
        }
    except Exception as e:
        return {
            "status": "error", 
            "error": str(e)
        }


# AVR integration status
@app.get("/status/avr")
async def avr_status():
    """Check AVR services status"""
    import httpx
    
    status = {
        "avr_core": {"url": settings.avr_core_url, "status": "unknown"},
        "avr_ami": {"url": settings.avr_ami_url, "status": "unknown"}
    }
    
    # Check AVR Core
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{settings.avr_core_url}/health")
            status["avr_core"]["status"] = "healthy" if response.status_code == 200 else "unhealthy"
    except Exception as e:
        status["avr_core"]["status"] = f"error: {str(e)}"
    
    # Check AVR AMI
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{settings.avr_ami_url}/health")
            status["avr_ami"]["status"] = "healthy" if response.status_code == 200 else "unhealthy"
    except Exception as e:
        status["avr_ami"]["status"] = f"error: {str(e)}"
    
    return status


# Include API routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(students.router, prefix="/api/v1/students", tags=["Students"])
app.include_router(fields.router, prefix="/api/v1/fields", tags=["Field Configuration"])
app.include_router(calls.router, prefix="/api/v1/calls", tags=["Calls"])
app.include_router(context.router, prefix="/api/v1/context", tags=["Context"])
app.include_router(campaigns.router, prefix="/api/v1/campaigns", tags=["Campaigns"])
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["Analytics"])
app.include_router(voice.router, prefix="/api/v1/voice", tags=["Voice Integration"])


def run_server():
    """Run the FastAPI server"""
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )


if __name__ == "__main__":
    run_server()
