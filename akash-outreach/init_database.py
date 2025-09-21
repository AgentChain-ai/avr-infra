#!/usr/bin/env python3
"""
Database initialization script for Akash Institute Outreach System
Run this to create the database and populate with initial data
"""

import sys
import os

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

def main():
    print("=== Akash Institute Outreach System ===")
    print("🔧 Initializing database...")
    
    try:
        # Import after adding to path
        from app.database import init_db
        from app.config import validate_environment, settings
        
        print("✅ Modules imported successfully")
        
        # Validate environment
        print("🔍 Validating environment...")
        validate_environment()
        print("✅ Environment validation passed")
        
        # Show configuration
        print("\n📋 Configuration Summary:")
        print(f"  Database URL: {settings.database_url}")
        print(f"  API Port: {settings.port}")
        print(f"  Debug Mode: {settings.debug}")
        print(f"  Upload Dir: {settings.upload_dir}")
        print(f"  OpenAI API Key: {'✅ Set' if settings.openai_api_key else '❌ Missing'}")
        print(f"  AVR Core URL: {settings.avr_core_url}")
        
        # Initialize database
        print("\n🔧 Creating database tables and initial data...")
        init_db()
        
        print("\n✅ Database initialization completed successfully!")
        print("\n🚀 Next steps:")
        print("  1. Run the FastAPI backend: uvicorn app.main:app --reload --port 8000")
        print("  2. Run the Streamlit dashboard: streamlit run app/streamlit_app.py --server.port 8501")
        print("  3. Access the API docs at: http://localhost:8000/docs")
        print("  4. Access the admin dashboard at: http://localhost:8501")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Make sure you've installed all dependencies: pip install -r requirements.txt")
        return 1
    
    except Exception as e:
        print(f"❌ Error during initialization: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
