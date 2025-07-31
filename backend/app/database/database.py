"""
Database configuration and session management
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# Create database engine
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
    echo=settings.DEBUG
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()

def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def init_db():
    """Initialize database tables"""
    # Import all models to ensure they are registered
    from app.database.models import User, Partner, Region, Capability, Feedback, Document, Engagement, Analytics
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Create initial data if database is empty
    db = SessionLocal()
    try:
        # Check if we have any users
        user_count = db.query(User).count()
        if user_count == 0:
            # Create default admin user
            from app.core.auth import get_password_hash
            from app.database.models import UserRole
            
            admin_user = User(
                email="admin@bayer.com",
                hashed_password=get_password_hash("admin123"),
                first_name="System",
                last_name="Administrator",
                role=UserRole.SUPER_ADMIN,
                is_active=True
            )
            db.add(admin_user)
            
            # Create some default regions
            default_regions = [
                Region(name="North America", code="NA", description="United States and Canada"),
                Region(name="Europe", code="EU", description="European Union countries"),
                Region(name="Asia Pacific", code="APAC", description="Asia Pacific region"),
                Region(name="Latin America", code="LATAM", description="Latin American countries"),
                Region(name="Middle East & Africa", code="MEA", description="Middle East and African countries")
            ]
            
            for region in default_regions:
                db.add(region)
            
            # Create some default capabilities
            default_capabilities = [
                # Technology capabilities
                Capability(name="Java Development", category="Technology", description="Java and J2EE development"),
                Capability(name="Python Development", category="Technology", description="Python development"),
                Capability(name="React Development", category="Technology", description="React and frontend development"),
                Capability(name="DevOps", category="Technology", description="DevOps and infrastructure"),
                Capability(name="Data Science", category="Technology", description="Data science and analytics"),
                Capability(name="Cloud Computing", category="Technology", description="AWS, Azure, GCP"),
                
                # Domain capabilities
                Capability(name="Pharmaceutical", category="Domain", description="Pharmaceutical industry experience"),
                Capability(name="Healthcare", category="Domain", description="Healthcare industry experience"),
                Capability(name="Manufacturing", category="Domain", description="Manufacturing industry experience"),
                Capability(name="Finance", category="Domain", description="Financial services experience"),
                
                # Tools and platforms
                Capability(name="Salesforce", category="Platform", description="Salesforce platform expertise"),
                Capability(name="SAP", category="Platform", description="SAP platform expertise"),
                Capability(name="ServiceNow", category="Platform", description="ServiceNow platform expertise"),
                Capability(name="Microsoft Dynamics", category="Platform", description="Microsoft Dynamics expertise")
            ]
            
            for capability in default_capabilities:
                db.add(capability)
            
            db.commit()
            print("Database initialized with default data")
        else:
            print("Database already contains data, skipping initialization")
            
    except Exception as e:
        print(f"Error initializing database: {e}")
        db.rollback()
    finally:
        db.close()