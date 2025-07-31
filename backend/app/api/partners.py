from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from sqlalchemy import and_, or_

from app.core.auth import get_current_user, require_admin_or_manager
from app.database.database import get_db
from app.database.models import Partner as PartnerModel, Region, Capability, User
from app.schemas.partner import Partner, PartnerCreate, PartnerUpdate, PartnerList, PartnerFilter, Region as RegionSchema, Capability as CapabilitySchema

router = APIRouter()

@router.get("/", response_model=List[PartnerList])
async def get_partners(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    tier: Optional[str] = None,
    partner_type: Optional[str] = None,
    region_id: Optional[int] = None,
    capability_id: Optional[int] = None,
    search: Optional[str] = None,
    profile_complete: Optional[bool] = None,
    current_user: User = Depends(require_admin_or_manager),
    db: Session = Depends(get_db)
):
    """Get list of partners with filtering options"""
    query = db.query(PartnerModel)
    
    # Apply filters
    if tier:
        query = query.filter(PartnerModel.tier == tier)
    if partner_type:
        query = query.filter(PartnerModel.partner_type == partner_type)
    if region_id:
        query = query.join(PartnerModel.regions).filter(Region.id == region_id)
    if capability_id:
        query = query.join(PartnerModel.capabilities).filter(Capability.id == capability_id)
    if profile_complete is not None:
        query = query.filter(PartnerModel.profile_complete == profile_complete)
    if search:
        search_filter = or_(
            PartnerModel.company_name.ilike(f"%{search}%"),
            PartnerModel.description.ilike(f"%{search}%"),
            PartnerModel.primary_contact_name.ilike(f"%{search}%")
        )
        query = query.filter(search_filter)
    
    # Apply pagination
    partners = query.offset(skip).limit(limit).all()
    
    return [PartnerList.from_orm(partner) for partner in partners]

@router.get("/{partner_id}", response_model=Partner)
async def get_partner(
    partner_id: int,
    current_user: User = Depends(require_admin_or_manager),
    db: Session = Depends(get_db)
):
    """Get detailed partner information"""
    partner = db.query(PartnerModel).filter(PartnerModel.id == partner_id).first()
    if not partner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Partner not found"
        )
    
    return Partner.from_orm(partner)

@router.post("/", response_model=Partner)
async def create_partner(
    partner_data: PartnerCreate,
    current_user: User = Depends(require_admin_or_manager),
    db: Session = Depends(get_db)
):
    """Create a new partner"""
    # Check if user already has a partner profile
    existing_partner = db.query(PartnerModel).filter(PartnerModel.user_id == partner_data.user_id).first()
    if existing_partner:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already has a partner profile"
        )
    
    # Create partner
    db_partner = PartnerModel(**partner_data.dict(exclude={'region_ids', 'capability_ids'}))
    
    # Add regions if specified
    if partner_data.region_ids:
        regions = db.query(Region).filter(Region.id.in_(partner_data.region_ids)).all()
        db_partner.regions = regions
    
    # Add capabilities if specified
    if partner_data.capability_ids:
        capabilities = db.query(Capability).filter(Capability.id.in_(partner_data.capability_ids)).all()
        db_partner.capabilities = capabilities
    
    db.add(db_partner)
    db.commit()
    db.refresh(db_partner)
    
    return Partner.from_orm(db_partner)

@router.put("/{partner_id}", response_model=Partner)
async def update_partner(
    partner_id: int,
    partner_data: PartnerUpdate,
    current_user: User = Depends(require_admin_or_manager),
    db: Session = Depends(get_db)
):
    """Update partner information"""
    partner = db.query(PartnerModel).filter(PartnerModel.id == partner_id).first()
    if not partner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Partner not found"
        )
    
    # Update fields
    update_data = partner_data.dict(exclude_unset=True, exclude={'region_ids', 'capability_ids'})
    for field, value in update_data.items():
        setattr(partner, field, value)
    
    # Update regions if specified
    if partner_data.region_ids is not None:
        regions = db.query(Region).filter(Region.id.in_(partner_data.region_ids)).all()
        partner.regions = regions
    
    # Update capabilities if specified
    if partner_data.capability_ids is not None:
        capabilities = db.query(Capability).filter(Capability.id.in_(partner_data.capability_ids)).all()
        partner.capabilities = capabilities
    
    # Update profile version and timestamp
    from sqlalchemy.sql import func
    partner.profile_version += 1
    partner.last_profile_update = func.now()
    
    db.commit()
    db.refresh(partner)
    
    return Partner.from_orm(partner)

@router.delete("/{partner_id}")
async def delete_partner(
    partner_id: int,
    current_user: User = Depends(require_admin_or_manager),
    db: Session = Depends(get_db)
):
    """Delete a partner (admin only)"""
    partner = db.query(PartnerModel).filter(PartnerModel.id == partner_id).first()
    if not partner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Partner not found"
        )
    
    db.delete(partner)
    db.commit()
    
    return {"message": "Partner deleted successfully"}

@router.get("/regions/", response_model=List[RegionSchema])
async def get_regions(
    current_user: User = Depends(require_admin_or_manager),
    db: Session = Depends(get_db)
):
    """Get all available regions"""
    regions = db.query(Region).all()
    return [RegionSchema.from_orm(region) for region in regions]

@router.get("/capabilities/", response_model=List[CapabilitySchema])
async def get_capabilities(
    category: Optional[str] = None,
    current_user: User = Depends(require_admin_or_manager),
    db: Session = Depends(get_db)
):
    """Get all available capabilities"""
    query = db.query(Capability)
    if category:
        query = query.filter(Capability.category == category)
    
    capabilities = query.all()
    return [CapabilitySchema.from_orm(capability) for capability in capabilities]

@router.get("/tiers/summary")
async def get_tier_summary(
    current_user: User = Depends(require_admin_or_manager),
    db: Session = Depends(get_db)
):
    """Get summary of partners by tier"""
    from sqlalchemy import func
    
    tier_counts = db.query(
        PartnerModel.tier,
        func.count(PartnerModel.id).label('count')
    ).group_by(PartnerModel.tier).all()
    
    return {
        "tier_summary": [
            {"tier": tier, "count": count} for tier, count in tier_counts
        ]
    }