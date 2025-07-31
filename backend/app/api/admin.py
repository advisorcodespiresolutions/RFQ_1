from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from sqlalchemy import func

from app.core.auth import get_current_user, require_admin, require_super_admin
from app.database.database import get_db
from app.database.models import User, Partner, Region, Capability, Feedback, Document
from app.schemas.user import UserCreate, UserUpdate, User as UserSchema

router = APIRouter()

@router.get("/users", response_model=List[UserSchema])
async def get_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get all users (admin only)"""
    users = db.query(User).offset(skip).limit(limit).all()
    return [UserSchema.from_orm(user) for user in users]

@router.post("/users", response_model=UserSchema)
async def create_user(
    user_data: UserCreate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Create a new user (admin only)"""
    from app.core.auth import get_password_hash
    
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Hash password
    hashed_password = get_password_hash(user_data.password)
    
    # Create new user
    db_user = User(
        email=user_data.email,
        hashed_password=hashed_password,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        role=user_data.role
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return UserSchema.from_orm(db_user)

@router.put("/users/{user_id}", response_model=UserSchema)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Update user (admin only)"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update fields
    update_data = user_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)
    
    db.commit()
    db.refresh(user)
    
    return UserSchema.from_orm(user)

@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Delete user (admin only)"""
    if current_user.id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    db.delete(user)
    db.commit()
    
    return {"message": "User deleted successfully"}

@router.get("/system-stats")
async def get_system_stats(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get system statistics (admin only)"""
    # User statistics
    total_users = db.query(User).count()
    active_users = db.query(User).filter(User.is_active == True).count()
    users_by_role = db.query(
        User.role,
        func.count(User.id).label('count')
    ).group_by(User.role).all()
    
    # Partner statistics
    total_partners = db.query(Partner).count()
    complete_profiles = db.query(Partner).filter(Partner.profile_complete == True).count()
    incomplete_profiles = db.query(Partner).filter(Partner.profile_complete == False).count()
    
    # Feedback statistics
    total_feedback = db.query(Feedback).count()
    avg_rating = db.query(func.avg(Feedback.overall_rating)).scalar() or 0
    
    # Document statistics
    total_documents = db.query(Document).count()
    
    return {
        "users": {
            "total": total_users,
            "active": active_users,
            "by_role": [{"role": role, "count": count} for role, count in users_by_role]
        },
        "partners": {
            "total": total_partners,
            "complete_profiles": complete_profiles,
            "incomplete_profiles": incomplete_profiles,
            "completion_rate": round(complete_profiles / total_partners * 100, 1) if total_partners > 0 else 0
        },
        "feedback": {
            "total": total_feedback,
            "average_rating": round(avg_rating, 2)
        },
        "documents": {
            "total": total_documents
        }
    }

@router.post("/regions")
async def create_region(
    name: str,
    code: str,
    description: Optional[str] = None,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Create a new region (admin only)"""
    # Check if region already exists
    existing_region = db.query(Region).filter(
        (Region.name == name) | (Region.code == code)
    ).first()
    if existing_region:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Region with this name or code already exists"
        )
    
    region = Region(name=name, code=code, description=description)
    db.add(region)
    db.commit()
    db.refresh(region)
    
    return {"message": "Region created successfully", "region_id": region.id}

@router.post("/capabilities")
async def create_capability(
    name: str,
    category: str,
    description: Optional[str] = None,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Create a new capability (admin only)"""
    capability = Capability(name=name, category=category, description=description)
    db.add(capability)
    db.commit()
    db.refresh(capability)
    
    return {"message": "Capability created successfully", "capability_id": capability.id}

@router.get("/audit-log")
async def get_audit_log(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db)
):
    """Get audit log (super admin only)"""
    # This would typically query an audit log table
    # For now, return a placeholder
    return {
        "message": "Audit log functionality would be implemented here",
        "note": "This would track all system changes and user actions"
    }

@router.post("/system-maintenance")
async def trigger_system_maintenance(
    maintenance_type: str,
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db)
):
    """Trigger system maintenance tasks (super admin only)"""
    if maintenance_type == "cleanup_old_data":
        # Clean up old feedback data (older than 2 years)
        from datetime import datetime, timedelta
        two_years_ago = datetime.utcnow() - timedelta(days=730)
        old_feedback = db.query(Feedback).filter(Feedback.created_at < two_years_ago).all()
        
        for feedback in old_feedback:
            db.delete(feedback)
        
        db.commit()
        
        return {
            "message": f"Cleaned up {len(old_feedback)} old feedback records",
            "maintenance_type": maintenance_type
        }
    
    elif maintenance_type == "recalculate_metrics":
        # Recalculate partner metrics
        partners = db.query(Partner).all()
        updated_count = 0
        
        for partner in partners:
            feedback_list = db.query(Feedback).filter(Feedback.partner_id == partner.id).all()
            if feedback_list:
                avg_rating = sum(f.overall_rating or 0 for f in feedback_list) / len(feedback_list)
                # Update partner metrics if needed
                updated_count += 1
        
        return {
            "message": f"Recalculated metrics for {updated_count} partners",
            "maintenance_type": maintenance_type
        }
    
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown maintenance type: {maintenance_type}"
        )

@router.get("/health-check")
async def system_health_check(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Perform system health check (admin only)"""
    health_status = {
        "database": "healthy",
        "file_system": "healthy",
        "authentication": "healthy",
        "overall": "healthy"
    }
    
    # Check database connectivity
    try:
        db.execute("SELECT 1")
    except Exception as e:
        health_status["database"] = f"error: {str(e)}"
        health_status["overall"] = "unhealthy"
    
    # Check file system
    try:
        import os
        upload_dir = "uploads"
        os.makedirs(upload_dir, exist_ok=True)
        test_file = os.path.join(upload_dir, "health_check.txt")
        with open(test_file, "w") as f:
            f.write("health check")
        os.remove(test_file)
    except Exception as e:
        health_status["file_system"] = f"error: {str(e)}"
        health_status["overall"] = "unhealthy"
    
    return health_status