"""
File upload and processing endpoints
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
import os
import shutil
from pathlib import Path

from app.database.database import get_db
from app.schemas.files import FileUploadResponse, FileListResponse
from app.services.file_service import FileService
from app.services.ai_service import AIService
from app.core.deps import get_current_user
from app.core.config import settings
from app.database.models import User

router = APIRouter()


@router.post("/upload", response_model=List[FileUploadResponse])
async def upload_files(
    quote_id: int = Form(...),
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Upload files for a quote (CAD drawings, documents, etc.)
    """
    file_service = FileService(db)
    ai_service = AIService()
    
    # Validate file count
    if len(files) > 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 10 files allowed per upload"
        )
    
    uploaded_files = []
    
    for file in files:
        # Validate file
        validation_result = file_service.validate_file(file)
        if not validation_result["valid"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file {file.filename}: {validation_result['error']}"
            )
        
        # Save file
        try:
            file_record = await file_service.save_file(
                file=file,
                quote_id=quote_id,
                uploaded_by=current_user.id
            )
            
            # Start async processing
            await ai_service.process_file_async(file_record.id)
            
            uploaded_files.append(FileUploadResponse.from_orm(file_record))
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload file {file.filename}: {str(e)}"
            )
    
    return uploaded_files


@router.get("/quote/{quote_id}", response_model=FileListResponse)
async def get_quote_files(
    quote_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all files for a specific quote
    """
    file_service = FileService(db)
    
    files = file_service.get_quote_files(quote_id)
    
    return FileListResponse(
        files=[FileUploadResponse.from_orm(f) for f in files],
        total=len(files)
    )


@router.get("/{file_id}")
async def get_file(
    file_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get file information
    """
    file_service = FileService(db)
    
    file_record = file_service.get_file_by_id(file_id)
    if not file_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    return FileUploadResponse.from_orm(file_record)


@router.get("/{file_id}/download")
async def download_file(
    file_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Download a file
    """
    file_service = FileService(db)
    
    file_record = file_service.get_file_by_id(file_id)
    if not file_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    file_path = Path(file_record.file_path)
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Physical file not found"
        )
    
    from fastapi.responses import FileResponse
    return FileResponse(
        path=file_path,
        filename=file_record.original_filename,
        media_type=file_record.mime_type or "application/octet-stream"
    )


@router.delete("/{file_id}")
async def delete_file(
    file_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a file
    """
    file_service = FileService(db)
    
    file_record = file_service.get_file_by_id(file_id)
    if not file_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    # Check permissions - admin or quote owner
    if not current_user.is_admin:
        quote = file_record.quote
        if quote.created_by != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this file"
            )
    
    # Delete file
    file_service.delete_file(file_id)
    
    return {"message": "File deleted successfully"}


@router.post("/{file_id}/process")
async def process_file(
    file_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Manually trigger file processing
    """
    file_service = FileService(db)
    ai_service = AIService()
    
    file_record = file_service.get_file_by_id(file_id)
    if not file_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    # Check permissions
    if not current_user.is_admin:
        quote = file_record.quote
        if quote.created_by != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to process this file"
            )
    
    # Process file
    try:
        processing_result = await ai_service.process_file(file_record)
        
        # Update file record
        file_service.update_processing_result(file_id, processing_result)
        
        return {
            "message": "File processed successfully",
            "extracted_data": processing_result.get("extracted_data", {}),
            "confidence_score": processing_result.get("confidence_score", 0.0)
        }
        
    except Exception as e:
        # Update error status
        file_service.update_processing_error(file_id, str(e))
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"File processing failed: {str(e)}"
        )


@router.get("/{file_id}/preview")
async def get_file_preview(
    file_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get file preview (thumbnail, metadata, etc.)
    """
    file_service = FileService(db)
    
    file_record = file_service.get_file_by_id(file_id)
    if not file_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    preview_data = file_service.generate_preview(file_record)
    
    return preview_data