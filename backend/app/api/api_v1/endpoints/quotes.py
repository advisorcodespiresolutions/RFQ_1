"""
Quote management endpoints
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.database.database import get_db
from app.database.models import Quote, QuoteStatus
from app.schemas.quotes import (
    QuoteCreate, QuoteUpdate, QuoteResponse, 
    QuoteListResponse, QuoteDetailResponse
)
from app.services.quote_service import QuoteService
from app.services.ai_service import AIService
from app.core.deps import get_current_user
from app.database.models import User

router = APIRouter()


@router.get("/", response_model=QuoteListResponse)
async def list_quotes(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status: Optional[QuoteStatus] = None,
    client_id: Optional[int] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get list of quotes with filtering and pagination
    """
    quote_service = QuoteService(db)
    
    filters = {}
    if status:
        filters["status"] = status
    if client_id:
        filters["client_id"] = client_id
    if search:
        filters["search"] = search
    
    quotes, total = quote_service.get_quotes(
        skip=skip, 
        limit=limit, 
        filters=filters,
        user_id=current_user.id if not current_user.is_admin else None
    )
    
    return QuoteListResponse(
        quotes=[QuoteResponse.from_orm(q) for q in quotes],
        total=total,
        skip=skip,
        limit=limit
    )


@router.get("/{quote_id}", response_model=QuoteDetailResponse)
async def get_quote(
    quote_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get detailed quote information including parts and files
    """
    quote_service = QuoteService(db)
    quote = quote_service.get_quote_detail(quote_id)
    
    if not quote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quote not found"
        )
    
    # Check permissions
    if not current_user.is_admin and quote.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this quote"
        )
    
    return QuoteDetailResponse.from_orm(quote)


@router.post("/", response_model=QuoteResponse, status_code=status.HTTP_201_CREATED)
async def create_quote(
    quote_data: QuoteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new quote
    """
    quote_service = QuoteService(db)
    
    # Generate quote number
    quote_number = quote_service.generate_quote_number()
    
    # Create quote
    quote = quote_service.create_quote(
        quote_data=quote_data,
        quote_number=quote_number,
        created_by=current_user.id
    )
    
    return QuoteResponse.from_orm(quote)


@router.put("/{quote_id}", response_model=QuoteResponse)
async def update_quote(
    quote_id: int,
    quote_data: QuoteUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update an existing quote
    """
    quote_service = QuoteService(db)
    
    # Get existing quote
    quote = quote_service.get_quote_by_id(quote_id)
    if not quote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quote not found"
        )
    
    # Check permissions
    if not current_user.is_admin and quote.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this quote"
        )
    
    # Update quote
    updated_quote = quote_service.update_quote(quote_id, quote_data)
    
    return QuoteResponse.from_orm(updated_quote)


@router.delete("/{quote_id}")
async def delete_quote(
    quote_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a quote (soft delete)
    """
    quote_service = QuoteService(db)
    
    # Get existing quote
    quote = quote_service.get_quote_by_id(quote_id)
    if not quote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quote not found"
        )
    
    # Check permissions
    if not current_user.is_admin and quote.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this quote"
        )
    
    quote_service.delete_quote(quote_id)
    
    return {"message": "Quote deleted successfully"}


@router.post("/{quote_id}/analyze")
async def analyze_quote(
    quote_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Run AI analysis on quote parts
    """
    quote_service = QuoteService(db)
    ai_service = AIService()
    
    # Get quote
    quote = quote_service.get_quote_detail(quote_id)
    if not quote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quote not found"
        )
    
    # Check permissions
    if not current_user.is_admin and quote.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to analyze this quote"
        )
    
    # Run AI analysis
    analysis_results = await ai_service.analyze_quote_parts(quote.parts)
    
    # Update quote with AI results
    quote_service.update_ai_analysis(quote_id, analysis_results)
    
    return {
        "message": "AI analysis completed",
        "confidence_score": analysis_results.get("overall_confidence", 0.0),
        "parts_analyzed": len(quote.parts)
    }


@router.post("/{quote_id}/approve")
async def approve_quote(
    quote_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Approve a quote
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can approve quotes"
        )
    
    quote_service = QuoteService(db)
    
    # Get quote
    quote = quote_service.get_quote_by_id(quote_id)
    if not quote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quote not found"
        )
    
    # Update status
    updated_quote = quote_service.update_quote_status(
        quote_id, 
        QuoteStatus.APPROVED,
        approved_by=current_user.id
    )
    
    return QuoteResponse.from_orm(updated_quote)


@router.post("/{quote_id}/duplicate")
async def duplicate_quote(
    quote_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a duplicate of an existing quote
    """
    quote_service = QuoteService(db)
    
    # Get original quote
    original_quote = quote_service.get_quote_detail(quote_id)
    if not original_quote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quote not found"
        )
    
    # Check permissions
    if not current_user.is_admin and original_quote.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to duplicate this quote"
        )
    
    # Create duplicate
    new_quote = quote_service.duplicate_quote(quote_id, current_user.id)
    
    return QuoteResponse.from_orm(new_quote)


@router.get("/{quote_id}/export")
async def export_quote(
    quote_id: int,
    format: str = Query("pdf", regex="^(pdf|excel)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Export quote as PDF or Excel
    """
    quote_service = QuoteService(db)
    
    # Get quote
    quote = quote_service.get_quote_detail(quote_id)
    if not quote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quote not found"
        )
    
    # Check permissions
    if not current_user.is_admin and quote.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to export this quote"
        )
    
    # Generate export
    if format == "pdf":
        file_path = quote_service.export_to_pdf(quote)
    else:
        file_path = quote_service.export_to_excel(quote)
    
    from fastapi.responses import FileResponse
    return FileResponse(
        file_path,
        media_type="application/octet-stream",
        filename=f"quote_{quote.quote_number}.{format}"
    )