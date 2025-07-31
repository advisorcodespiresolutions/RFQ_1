from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date, timedelta
import pytz

from ..database import get_db
from ..models.time_attendance import *
from ..schemas.time_attendance import *
from ..services.california_compliance import CaliforniaComplianceEngine
from ..core.auth import get_current_user

router = APIRouter(prefix="/api/time-attendance", tags=["Time & Attendance"])

# Time Entry Endpoints
@router.post("/punch", response_model=TimeEntryResponse)
async def punch_in_out(
    punch_data: PunchValidation,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Employee = Depends(get_current_user)
):
    """
    Clock in/out endpoint with geofencing and grace period validation
    """
    # Validate employee exists and is active
    employee = db.query(Employee).filter(
        and_(Employee.id == punch_data.employee_id, Employee.is_active == True)
    ).first()
    
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found or inactive")
    
    # Create time entry
    time_entry = TimeEntry(
        employee_id=punch_data.employee_id,
        punch_type=punch_data.punch_type,
        punch_time=datetime.utcnow(),
        location_id=employee.location_id,
        latitude=punch_data.latitude,
        longitude=punch_data.longitude,
        device_type=punch_data.device_type,
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent")
    )
    
    # Check grace period compliance
    compliance_engine = CaliforniaComplianceEngine(db)
    schedule = db.query(Schedule).filter(
        and_(
            Schedule.employee_id == punch_data.employee_id,
            Schedule.date == date.today()
        )
    ).first()
    
    grace_check = compliance_engine.check_grace_period_compliance(time_entry, schedule)
    time_entry.is_within_grace_period = grace_check["within_grace"]
    
    # Check geofence compliance if location has coordinates
    if employee.location_id and punch_data.latitude and punch_data.longitude:
        geofence_check = compliance_engine.check_geofence_compliance(time_entry, employee.location_id)
        if geofence_check["violation"]:
            # Create compliance audit for geofence violation
            compliance_engine.create_compliance_audit(
                employee_id=punch_data.employee_id,
                violation_type="geofence_violation",
                description=f"Punch outside geofence: {geofence_check['distance_meters']:.1f}m from {geofence_check['location_name']}",
                severity="medium"
            )
    
    # Create compliance audit for grace period violation
    if grace_check["violation"]:
        compliance_engine.create_compliance_audit(
            employee_id=punch_data.employee_id,
            violation_type="grace_period_violation",
            description=f"Punch {grace_check['minutes_off']:.1f} minutes outside grace period",
            severity="low"
        )
    
    db.add(time_entry)
    db.commit()
    db.refresh(time_entry)
    
    warnings = []
    if grace_check["violation"]:
        warnings.append(f"Punch {grace_check['minutes_off']:.1f} minutes outside grace period")
    if not time_entry.is_within_grace_period:
        warnings.append("Punch outside grace period")
    
    return TimeEntryResponse(
        success=True,
        message="Punch recorded successfully",
        time_entry=time_entry,
        warnings=warnings
    )

@router.get("/time-entries/{employee_id}", response_model=List[TimeEntry])
async def get_employee_time_entries(
    employee_id: int,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: Employee = Depends(get_current_user)
):
    """Get time entries for an employee within date range"""
    query = db.query(TimeEntry).filter(TimeEntry.employee_id == employee_id)
    
    if start_date:
        query = query.filter(TimeEntry.punch_time >= datetime.combine(start_date, datetime.min.time()))
    if end_date:
        query = query.filter(TimeEntry.punch_time <= datetime.combine(end_date, datetime.max.time()))
    
    return query.order_by(TimeEntry.punch_time.desc()).all()

@router.put("/time-entries/{time_entry_id}", response_model=TimeEntry)
async def update_time_entry(
    time_entry_id: int,
    time_entry_update: TimeEntryUpdate,
    db: Session = Depends(get_db),
    current_user: Employee = Depends(get_current_user)
):
    """Update time entry (requires approval workflow)"""
    time_entry = db.query(TimeEntry).filter(TimeEntry.id == time_entry_id).first()
    if not time_entry:
        raise HTTPException(status_code=404, detail="Time entry not found")
    
    # Only allow updates if status is pending
    if time_entry.status != TimeEntryStatus.PENDING:
        raise HTTPException(status_code=400, detail="Can only update pending time entries")
    
    for field, value in time_entry_update.dict(exclude_unset=True).items():
        setattr(time_entry, field, value)
    
    db.commit()
    db.refresh(time_entry)
    return time_entry

# Overtime Calculation Endpoints
@router.post("/overtime/calculate/{employee_id}", response_model=OvertimeCalculationResponse)
async def calculate_overtime(
    employee_id: int,
    work_date: date,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: Employee = Depends(get_current_user)
):
    """Calculate California-compliant overtime for an employee on a specific date"""
    compliance_engine = CaliforniaComplianceEngine(db)
    
    # Calculate daily overtime
    daily_calculations = compliance_engine.calculate_daily_overtime(employee_id, work_date)
    
    # Calculate 16+ hour overtime
    sixteen_plus_calculation = compliance_engine.calculate_sixteen_plus_overtime(employee_id, work_date)
    
    # Calculate weekly overtime
    week_start = work_date - timedelta(days=work_date.weekday())
    weekly_calculations = compliance_engine.calculate_weekly_overtime(employee_id, week_start)
    
    all_calculations = daily_calculations + weekly_calculations
    if sixteen_plus_calculation:
        all_calculations.append(sixteen_plus_calculation)
    
    # Save calculations to database
    saved_calculations = []
    total_overtime_pay = 0
    
    for calc in all_calculations:
        db_calc = OvertimeCalculation(**calc.dict())
        db.add(db_calc)
        saved_calculations.append(db_calc)
        total_overtime_pay += calc.overtime_pay
    
    db.commit()
    
    # Check for compliance violations
    compliance_violations = []
    if any(calc.overtime_hours > 8 for calc in all_calculations):
        compliance_violations.append("Daily overtime exceeds 8 hours")
    if any(calc.overtime_hours > 12 for calc in all_calculations):
        compliance_violations.append("Daily overtime exceeds 12 hours")
    
    return OvertimeCalculationResponse(
        success=True,
        message="Overtime calculated successfully",
        calculations=saved_calculations,
        total_overtime_pay=total_overtime_pay,
        compliance_violations=compliance_violations
    )

@router.get("/overtime/summary/{employee_id}")
async def get_overtime_summary(
    employee_id: int,
    start_date: date,
    end_date: date,
    db: Session = Depends(get_db),
    current_user: Employee = Depends(get_current_user)
):
    """Get overtime summary for an employee within date range"""
    calculations = db.query(OvertimeCalculation).filter(
        and_(
            OvertimeCalculation.employee_id == employee_id,
            OvertimeCalculation.date >= start_date,
            OvertimeCalculation.date <= end_date
        )
    ).all()
    
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    
    overtime_breakdown = {}
    total_overtime_pay = 0
    base_pay = 0
    
    for calc in calculations:
        ot_type = calc.overtime_type.value
        if ot_type not in overtime_breakdown:
            overtime_breakdown[ot_type] = 0
        overtime_breakdown[ot_type] += calc.overtime_hours
        total_overtime_pay += calc.overtime_pay
        base_pay += (calc.hours_worked - calc.overtime_hours) * calc.base_hourly_rate
    
    return OvertimeSummary(
        employee_id=employee_id,
        employee_name=f"{employee.first_name} {employee.last_name}",
        date=start_date,
        total_hours=sum(calc.hours_worked for calc in calculations),
        overtime_breakdown=overtime_breakdown,
        total_overtime_pay=total_overtime_pay,
        base_pay=base_pay
    )

# Holiday Management Endpoints
@router.post("/holidays/allocate", response_model=HolidayAllocationResponse)
async def allocate_paid_holidays(
    week_start: date,
    db: Session = Depends(get_db),
    current_user: Employee = Depends(get_current_user)
):
    """Automatically allocate paid holidays for eligible employees"""
    compliance_engine = CaliforniaComplianceEngine(db)
    result = compliance_engine.allocate_paid_holidays(week_start)
    
    return HolidayAllocationResponse(
        success=True,
        message=f"Allocated {len(result['holidays_allocated'])} paid holidays",
        holidays_allocated=result['holidays_allocated'],
        employees_eligible=result['eligible_count'],
        employees_ineligible=result['ineligible_count']
    )

@router.get("/holidays/{employee_id}", response_model=List[PaidHoliday])
async def get_employee_holidays(
    employee_id: int,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: Employee = Depends(get_current_user)
):
    """Get paid holidays for an employee"""
    query = db.query(PaidHoliday).filter(PaidHoliday.employee_id == employee_id)
    
    if start_date:
        query = query.filter(PaidHoliday.date >= start_date)
    if end_date:
        query = query.filter(PaidHoliday.date <= end_date)
    
    return query.order_by(PaidHoliday.date.desc()).all()

@router.post("/holidays/manual", response_model=PaidHoliday)
async def create_manual_holiday(
    holiday_data: PaidHolidayCreate,
    db: Session = Depends(get_db),
    current_user: Employee = Depends(get_current_user)
):
    """Manually create a paid holiday (admin override)"""
    holiday = PaidHoliday(
        **holiday_data.dict(),
        allocated_by_id=current_user.id,
        is_auto_allocated=False
    )
    
    db.add(holiday)
    db.commit()
    db.refresh(holiday)
    return holiday

# Schedule Management Endpoints
@router.post("/schedules", response_model=Schedule)
async def create_schedule(
    schedule_data: ScheduleCreate,
    db: Session = Depends(get_db),
    current_user: Employee = Depends(get_current_user)
):
    """Create work schedule for an employee"""
    schedule = Schedule(**schedule_data.dict())
    db.add(schedule)
    db.commit()
    db.refresh(schedule)
    return schedule

@router.get("/schedules/{employee_id}", response_model=List[Schedule])
async def get_employee_schedules(
    employee_id: int,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: Employee = Depends(get_current_user)
):
    """Get schedules for an employee"""
    query = db.query(Schedule).filter(Schedule.employee_id == employee_id)
    
    if start_date:
        query = query.filter(Schedule.date >= start_date)
    if end_date:
        query = query.filter(Schedule.date <= end_date)
    
    return query.order_by(Schedule.date).all()

# Compliance and Reporting Endpoints
@router.get("/compliance/report")
async def generate_compliance_report(
    start_date: date,
    end_date: date,
    db: Session = Depends(get_db),
    current_user: Employee = Depends(get_current_user)
):
    """Generate comprehensive compliance report"""
    compliance_engine = CaliforniaComplianceEngine(db)
    return compliance_engine.generate_compliance_report(start_date, end_date)

@router.get("/reports/weekly-summary")
async def get_weekly_hours_summary(
    week_start: date,
    db: Session = Depends(get_db),
    current_user: Employee = Depends(get_current_user)
):
    """Get weekly hours summary for all employees"""
    week_end = week_start + timedelta(days=6)
    compliance_engine = CaliforniaComplianceEngine(db)
    
    employees = db.query(Employee).filter(Employee.is_active == True).all()
    summaries = []
    
    for employee in employees:
        # Calculate hours worked in the week
        start_datetime = datetime.combine(week_start, datetime.min.time())
        end_datetime = datetime.combine(week_end, datetime.max.time())
        
        time_entries = db.query(TimeEntry).filter(
            and_(
                TimeEntry.employee_id == employee.id,
                TimeEntry.punch_time >= start_datetime,
                TimeEntry.punch_time <= end_datetime,
                TimeEntry.status.in_(['approved', 'pending'])
            )
        ).order_by(TimeEntry.punch_time).all()
        
        total_hours = compliance_engine._calculate_hours_from_entries(time_entries)
        shifts_worked = compliance_engine._count_shifts_in_week(employee.id, week_start, week_end)
        
        # Check holiday eligibility
        holiday_eligible = shifts_worked >= 4
        
        # Get holiday hours
        holiday_hours = 0
        holiday = db.query(PaidHoliday).filter(
            and_(
                PaidHoliday.employee_id == employee.id,
                PaidHoliday.date >= week_start,
                PaidHoliday.date <= week_end
            )
        ).first()
        if holiday:
            holiday_hours = holiday.hours_paid
        
        # Calculate overtime hours
        overtime_calculations = db.query(OvertimeCalculation).filter(
            and_(
                OvertimeCalculation.employee_id == employee.id,
                OvertimeCalculation.date >= week_start,
                OvertimeCalculation.date <= week_end
            )
        ).all()
        overtime_hours = sum(calc.overtime_hours for calc in overtime_calculations)
        regular_hours = total_hours - overtime_hours
        
        summaries.append(WeeklyHoursSummary(
            employee_id=employee.id,
            employee_name=f"{employee.first_name} {employee.last_name}",
            week_start=week_start,
            week_end=week_end,
            total_hours=total_hours,
            regular_hours=regular_hours,
            overtime_hours=overtime_hours,
            holiday_hours=holiday_hours,
            shifts_worked=shifts_worked,
            holiday_eligible=holiday_eligible
        ))
    
    return summaries

@router.get("/reports/holiday-eligibility")
async def get_holiday_eligibility_report(
    week_start: date,
    db: Session = Depends(get_db),
    current_user: Employee = Depends(get_current_user)
):
    """Get holiday eligibility report for all employees"""
    week_end = week_start + timedelta(days=6)
    compliance_engine = CaliforniaComplianceEngine(db)
    
    employees = db.query(Employee).filter(Employee.is_active == True).all()
    reports = []
    
    for employee in employees:
        shifts_worked = compliance_engine._count_shifts_in_week(employee.id, week_start, week_end)
        
        # Calculate total hours worked
        start_datetime = datetime.combine(week_start, datetime.min.time())
        end_datetime = datetime.combine(week_end, datetime.max.time())
        
        time_entries = db.query(TimeEntry).filter(
            and_(
                TimeEntry.employee_id == employee.id,
                TimeEntry.punch_time >= start_datetime,
                TimeEntry.punch_time <= end_datetime,
                TimeEntry.status.in_(['approved', 'pending'])
            )
        ).order_by(TimeEntry.punch_time).all()
        
        hours_worked = compliance_engine._calculate_hours_from_entries(time_entries)
        
        # Check if holiday allocated
        holiday = db.query(PaidHoliday).filter(
            and_(
                PaidHoliday.employee_id == employee.id,
                PaidHoliday.date >= week_start,
                PaidHoliday.date <= week_end
            )
        ).first()
        
        reports.append(HolidayEligibilityReport(
            employee_id=employee.id,
            employee_name=f"{employee.first_name} {employee.last_name}",
            week_start=week_start,
            week_end=week_end,
            shifts_worked=shifts_worked,
            hours_worked=hours_worked,
            holiday_allocated=holiday is not None,
            holiday_date=holiday.date if holiday else None,
            holiday_hours=holiday.hours_paid if holiday else None
        ))
    
    return reports

# Manager Approval Endpoints
@router.post("/approve/{time_entry_id}")
async def approve_time_entry(
    time_entry_id: int,
    db: Session = Depends(get_db),
    current_user: Employee = Depends(get_current_user)
):
    """Approve a time entry (manager only)"""
    time_entry = db.query(TimeEntry).filter(TimeEntry.id == time_entry_id).first()
    if not time_entry:
        raise HTTPException(status_code=404, detail="Time entry not found")
    
    # Check if current user is manager of the employee
    employee = db.query(Employee).filter(Employee.id == time_entry.employee_id).first()
    if employee.manager_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to approve this time entry")
    
    time_entry.status = TimeEntryStatus.APPROVED
    db.commit()
    db.refresh(time_entry)
    
    return {"message": "Time entry approved successfully", "time_entry": time_entry}

@router.post("/reject/{time_entry_id}")
async def reject_time_entry(
    time_entry_id: int,
    reason: str,
    db: Session = Depends(get_db),
    current_user: Employee = Depends(get_current_user)
):
    """Reject a time entry with reason (manager only)"""
    time_entry = db.query(TimeEntry).filter(TimeEntry.id == time_entry_id).first()
    if not time_entry:
        raise HTTPException(status_code=404, detail="Time entry not found")
    
    # Check if current user is manager of the employee
    employee = db.query(Employee).filter(Employee.id == time_entry.employee_id).first()
    if employee.manager_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to reject this time entry")
    
    time_entry.status = TimeEntryStatus.REJECTED
    time_entry.notes = f"Rejected by {current_user.first_name} {current_user.last_name}: {reason}"
    db.commit()
    db.refresh(time_entry)
    
    return {"message": "Time entry rejected successfully", "time_entry": time_entry}

# Export Endpoints
@router.get("/export/csv")
async def export_time_data_csv(
    start_date: date,
    end_date: date,
    employee_ids: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Employee = Depends(get_current_user)
):
    """Export time data to CSV format for compliance filings"""
    # Implementation for CSV export
    pass

@router.get("/export/xml")
async def export_time_data_xml(
    start_date: date,
    end_date: date,
    employee_ids: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Employee = Depends(get_current_user)
):
    """Export time data to XML format for compliance filings"""
    # Implementation for XML export
    pass