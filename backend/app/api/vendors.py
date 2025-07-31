from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import shutil
from datetime import datetime

from app.core.auth import get_current_user, require_admin_or_vendor
from app.core.config import settings
from app.database.database import get_db
from app.database.models import Partner as PartnerModel, Document, User
from app.schemas.partner import Partner, PartnerUpdate

router = APIRouter()

@router.get("/my-profile", response_model=Partner)
async def get_my_profile(
    current_user: User = Depends(require_admin_or_vendor),
    db: Session = Depends(get_db)
):
    """Get current vendor's profile"""
    partner = db.query(PartnerModel).filter(PartnerModel.user_id == current_user.id).first()
    if not partner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Partner profile not found"
        )
    
    return Partner.from_orm(partner)

@router.put("/my-profile", response_model=Partner)
async def update_my_profile(
    partner_data: PartnerUpdate,
    current_user: User = Depends(require_admin_or_vendor),
    db: Session = Depends(get_db)
):
    """Update current vendor's profile"""
    partner = db.query(PartnerModel).filter(PartnerModel.user_id == current_user.id).first()
    if not partner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Partner profile not found"
        )
    
    # Update fields
    update_data = partner_data.dict(exclude_unset=True, exclude={'region_ids', 'capability_ids'})
    for field, value in update_data.items():
        setattr(partner, field, value)
    
    # Update profile version and timestamp
    from sqlalchemy.sql import func
    partner.profile_version += 1
    partner.last_profile_update = func.now()
    partner.profile_complete = True  # Mark as complete when updated
    
    db.commit()
    db.refresh(partner)
    
    return Partner.from_orm(partner)

@router.post("/upload-document")
async def upload_document(
    file: UploadFile = File(...),
    document_type: str = "profile",
    current_user: User = Depends(require_admin_or_vendor),
    db: Session = Depends(get_db)
):
    """Upload a document for the vendor's profile"""
    # Validate file type
    file_extension = os.path.splitext(file.filename)[1].lower()
    if file_extension not in settings.ALLOWED_FILE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type {file_extension} not allowed. Allowed types: {settings.ALLOWED_FILE_TYPES}"
        )
    
    # Check file size
    if file.size and file.size > settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Maximum size: {settings.MAX_FILE_SIZE} bytes"
        )
    
    # Get partner profile
    partner = db.query(PartnerModel).filter(PartnerModel.user_id == current_user.id).first()
    if not partner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Partner profile not found"
        )
    
    # Create upload directory if it doesn't exist
    upload_dir = os.path.join(settings.UPLOAD_DIR, str(partner.id))
    os.makedirs(upload_dir, exist_ok=True)
    
    # Generate unique filename
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"{document_type}_{timestamp}{file_extension}"
    file_path = os.path.join(upload_dir, filename)
    
    # Save file
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error saving file: {str(e)}"
        )
    
    # Create document record
    db_document = Document(
        partner_id=partner.id,
        filename=filename,
        original_filename=file.filename,
        file_path=file_path,
        file_size=file.size or 0,
        file_type=file_extension,
        document_type=document_type
    )
    
    db.add(db_document)
    db.commit()
    db.refresh(db_document)
    
    return {
        "message": "Document uploaded successfully",
        "document_id": db_document.id,
        "filename": filename
    }

@router.get("/my-documents")
async def get_my_documents(
    current_user: User = Depends(require_admin_or_vendor),
    db: Session = Depends(get_db)
):
    """Get current vendor's uploaded documents"""
    partner = db.query(PartnerModel).filter(PartnerModel.user_id == current_user.id).first()
    if not partner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Partner profile not found"
        )
    
    documents = db.query(Document).filter(Document.partner_id == partner.id).all()
    
    return [
        {
            "id": doc.id,
            "original_filename": doc.original_filename,
            "document_type": doc.document_type,
            "file_size": doc.file_size,
            "uploaded_at": doc.uploaded_at
        }
        for doc in documents
    ]

@router.delete("/documents/{document_id}")
async def delete_document(
    document_id: int,
    current_user: User = Depends(require_admin_or_vendor),
    db: Session = Depends(get_db)
):
    """Delete a document (only own documents)"""
    # Get partner profile
    partner = db.query(PartnerModel).filter(PartnerModel.user_id == current_user.id).first()
    if not partner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Partner profile not found"
        )
    
    # Get document
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.partner_id == partner.id
    ).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Delete file from filesystem
    try:
        if os.path.exists(document.file_path):
            os.remove(document.file_path)
    except Exception as e:
        # Log error but continue with database deletion
        print(f"Error deleting file {document.file_path}: {e}")
    
    # Delete from database
    db.delete(document)
    db.commit()
    
    return {"message": "Document deleted successfully"}

@router.get("/profile-completion-status")
async def get_profile_completion_status(
    current_user: User = Depends(require_admin_or_vendor),
    db: Session = Depends(get_db)
):
    """Get profile completion status and missing fields"""
    partner = db.query(PartnerModel).filter(PartnerModel.user_id == current_user.id).first()
    if not partner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Partner profile not found"
        )
    
    # Check required fields
    required_fields = [
        "company_name", "description", "primary_contact_name",
        "primary_contact_email", "primary_contact_phone"
    ]
    
    missing_fields = []
    for field in required_fields:
        if not getattr(partner, field):
            missing_fields.append(field)
    
    completion_percentage = max(0, (len(required_fields) - len(missing_fields)) / len(required_fields) * 100)
    
    return {
        "profile_complete": partner.profile_complete,
        "completion_percentage": round(completion_percentage, 1),
        "missing_fields": missing_fields,
        "last_updated": partner.last_profile_update,
        "profile_version": partner.profile_version
    }