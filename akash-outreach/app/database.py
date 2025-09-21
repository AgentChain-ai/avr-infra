"""
Database setup and connection management for Akash Institute Outreach System
"""
from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.engine import Engine
import sqlite3
import os
from .config import get_database_url


# SQLAlchemy setup
Base = declarative_base()
engine = None
SessionLocal = None


def get_engine():
    """Get SQLAlchemy engine"""
    global engine
    if engine is None:
        database_url = get_database_url()
        
        # Create directory if it doesn't exist
        if database_url.startswith("sqlite:///"):
            db_path = database_url.replace("sqlite:///", "")
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        engine = create_engine(
            database_url,
            connect_args={"check_same_thread": False} if "sqlite" in database_url else {},
            echo=False  # Set to True for SQL debugging
        )
        
        # Enable foreign key constraints for SQLite
        if "sqlite" in database_url:
            @event.listens_for(Engine, "connect")
            def set_sqlite_pragma(dbapi_connection, connection_record):
                if isinstance(dbapi_connection, sqlite3.Connection):
                    cursor = dbapi_connection.cursor()
                    cursor.execute("PRAGMA foreign_keys=ON")
                    cursor.execute("PRAGMA journal_mode=WAL")  # Better concurrency
                    cursor.close()
    
    return engine


def get_session_local():
    """Get SQLAlchemy session factory"""
    global SessionLocal
    if SessionLocal is None:
        engine = get_engine()
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal


def get_db() -> Session:
    """Dependency to get database session"""
    SessionLocal = get_session_local()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """Create all database tables"""
    from .models import student, field_config, call_log, context_info
    
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created successfully")


def init_db():
    """Initialize database with tables and sample data"""
    print("🔧 Initializing Akash Outreach database...")
    
    # Create tables
    create_tables()
    
    # Insert default field configurations
    _insert_default_field_configs()
    
    # Insert sample context information
    _insert_sample_context()
    
    print("✅ Database initialization completed")


def _insert_default_field_configs():
    """Insert default field configurations"""
    from .models.field_config import FieldConfiguration
    
    SessionLocal = get_session_local()
    db = SessionLocal()
    
    # Check if field configs already exist
    if db.query(FieldConfiguration).count() > 0:
        print("📋 Field configurations already exist, skipping...")
        db.close()
        return
    
    default_fields = [
        {
            "field_name": "student_name",
            "field_type": "text",
            "field_label": "Student Name",
            "is_required": True,
            "is_visible_in_list": True,
            "display_order": 1
        },
        {
            "field_name": "parent_name",
            "field_type": "text",
            "field_label": "Parent Name",
            "is_required": False,
            "is_visible_in_list": True,
            "display_order": 2
        },
        {
            "field_name": "scholarship_amount",
            "field_type": "currency",
            "field_label": "Scholarship Amount",
            "is_required": False,
            "is_visible_in_list": True,
            "display_order": 3
        },
        {
            "field_name": "scholarship_percentage",
            "field_type": "number",
            "field_label": "Scholarship Percentage",
            "is_required": False,
            "is_visible_in_list": True,
            "display_order": 4
        },
        {
            "field_name": "test_score",
            "field_type": "number",
            "field_label": "Test Score",
            "is_required": False,
            "is_visible_in_list": True,
            "display_order": 5
        },
        {
            "field_name": "rank_achieved",
            "field_type": "number",
            "field_label": "Rank Achieved",
            "is_required": False,
            "is_visible_in_list": True,
            "display_order": 6
        },
        {
            "field_name": "course_interested",
            "field_type": "select",
            "field_label": "Course Interested",
            "is_required": False,
            "is_visible_in_list": False,
            "display_order": 7,
            "field_options": {
                "options": [
                    "B.Tech Computer Science",
                    "B.Tech Mechanical Engineering",
                    "B.Tech Electrical Engineering",
                    "B.Tech Civil Engineering",
                    "MBBS",
                    "BDS",
                    "B.Pharmacy",
                    "Other"
                ]
            }
        },
        {
            "field_name": "next_steps",
            "field_type": "text",
            "field_label": "Next Steps",
            "is_required": False,
            "is_visible_in_list": False,
            "display_order": 8
        }
    ]
    
    try:
        for field_data in default_fields:
            field_config = FieldConfiguration(**field_data)
            db.add(field_config)
        
        db.commit()
        print(f"📋 Inserted {len(default_fields)} default field configurations")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error inserting field configurations: {e}")
    finally:
        db.close()


def _insert_sample_context():
    """Insert sample context information"""
    from .models.context_info import ContextInfo
    
    SessionLocal = get_session_local()
    db = SessionLocal()
    
    # Check if context info already exists
    if db.query(ContextInfo).count() > 0:
        print("📚 Context information already exists, skipping...")
        db.close()
        return
    
    sample_context = [
        {
            "topic": "Admission Process",
            "information": "Students need to complete the admission form within 30 days of scholarship announcement. Required documents include 10th and 12th mark sheets, entrance test scorecard, and ID proof.",
            "priority": 3,
            "tags": ["admission", "documents", "deadline"]
        },
        {
            "topic": "Fee Structure",
            "information": "Annual fees for B.Tech courses is ₹2,50,000. With scholarship, students pay only the remaining amount. Fees can be paid in 3 installments - admission time, before semester 1, and before semester 2.",
            "priority": 3,
            "tags": ["fees", "payment", "installments"]
        },
        {
            "topic": "Hostel Facilities",
            "information": "Akash Institute provides both AC and non-AC hostel rooms. 4-seater rooms at ₹80,000/year and 2-seater rooms at ₹1,20,000/year. All rooms include Wi-Fi, study table, and wardrobe.",
            "priority": 2,
            "tags": ["hostel", "accommodation", "facilities"]
        },
        {
            "topic": "Course Information",
            "information": "B.Tech program is 4 years with industry internships in 3rd year. Curriculum includes latest technologies, practical labs, and industry projects. Placement support starts from 2nd year.",
            "priority": 2,
            "tags": ["courses", "curriculum", "placements"]
        },
        {
            "topic": "Contact Information",
            "information": "Admission Office: +91-9876543210 | Email: admissions@akashinstitute.edu.in | Address: Akash Institute, Education City, Mumbai - 400001",
            "priority": 1,
            "tags": ["contact", "address", "support"]
        }
    ]
    
    try:
        for context_data in sample_context:
            context_info = ContextInfo(**context_data)
            db.add(context_info)
        
        db.commit()
        print(f"📚 Inserted {len(sample_context)} sample context entries")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error inserting context information: {e}")
    finally:
        db.close()


def reset_database():
    """Reset database (drop and recreate all tables)"""
    print("🗑️  Resetting database...")
    
    engine = get_engine()
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    print("✅ Database reset completed")


if __name__ == "__main__":
    # Test database setup
    print("Testing database setup...")
    init_db()
