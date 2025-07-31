from datetime import date, datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from decimal import Decimal

from app.database.database import get_db
from app.schemas.time_attendance import (
    Employee, EmployeeCreate, EmployeeUpdate,
    TimeEntry, TimeEntryCreate, TimeEntryUpdate,
    WorkSchedule, WorkScheduleCreate, WorkScheduleUpdate,
    OvertimeConfig, OvertimeConfigCreate, OvertimeConfigUpdate,
    HolidayConfig, HolidayConfigCreate, HolidayConfigUpdate,
    Timesheet, TimesheetCreate, TimesheetUpdate,
    PunchRequest, PunchResponse, TimesheetSummary, OvertimeReport,
    ComplianceReport, TimesheetApprovalRequest, HolidayOverrideRequest
)
from app.services.time_tracking_service import TimeTrackingService
from app.services.overtime_service import OvertimeService
from app.services.holiday_service import HolidayService

router = APIRouter(prefix="/time-attendance", tags=["Time & Attendance"])


# Employee Management Endpoints
@router.post("/employees/", response_model=Employee)
def create_employee(employee: EmployeeCreate, db: Session = Depends(get_db)):
    """Create a new employee"""
    from app.database.models import Employee as EmployeeModel
    
    # Check if employee_id already exists
    existing_employee = db.query(EmployeeModel).filter(
        EmployeeModel.employee_id == employee.employee_id
    ).first()
    
    if existing_employee:
        raise HTTPException(status_code=400, detail="Employee ID already exists")
    
    db_employee = EmployeeModel(**employee.dict())
    db.add(db_employee)
    db.commit()
    db.refresh(db_employee)
    return db_employee


@router.get("/employees/", response_model=List[Employee])
def get_employees(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    department: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get list of employees with optional filtering"""
    from app.database.models import Employee as EmployeeModel
    
    query = db.query(EmployeeModel)
    
    if status:
        query = query.filter(EmployeeModel.status == status)
    if department:
        query = query.filter(EmployeeModel.department == department)
    
    employees = query.offset(skip).limit(limit).all()
    return employees


@router.get("/employees/{employee_id}", response_model=Employee)
def get_employee(employee_id: str, db: Session = Depends(get_db)):
    """Get employee by ID"""
    from app.database.models import Employee as EmployeeModel
    
    employee = db.query(EmployeeModel).filter(
        EmployeeModel.employee_id == employee_id
    ).first()
    
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    return employee


@router.put("/employees/{employee_id}", response_model=Employee)
def update_employee(employee_id: str, employee_update: EmployeeUpdate, db: Session = Depends(get_db)):
    """Update employee information"""
    from app.database.models import Employee as EmployeeModel
    
    employee = db.query(EmployeeModel).filter(
        EmployeeModel.employee_id == employee_id
    ).first()
    
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    update_data = employee_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(employee, field, value)
    
    db.commit()
    db.refresh(employee)
    return employee


# Time Tracking Endpoints
@router.post("/punch/", response_model=PunchResponse)
def process_punch(punch_request: PunchRequest, db: Session = Depends(get_db)):
    """Process a time punch (clock in/out)"""
    time_service = TimeTrackingService(db)
    return time_service.process_punch(punch_request)


@router.get("/time-entries/", response_model=List[TimeEntry])
def get_time_entries(
    employee_id: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    punch_type: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get time entries with optional filtering"""
    from app.database.models import TimeEntry as TimeEntryModel
    from sqlalchemy import func
    
    query = db.query(TimeEntryModel)
    
    if employee_id:
        query = query.filter(TimeEntryModel.employee_id == employee_id)
    if start_date:
        query = query.filter(func.date(TimeEntryModel.punch_time) >= start_date)
    if end_date:
        query = query.filter(func.date(TimeEntryModel.punch_time) <= end_date)
    if punch_type:
        query = query.filter(TimeEntryModel.punch_type == punch_type)
    
    time_entries = query.order_by(TimeEntryModel.punch_time.desc()).offset(skip).limit(limit).all()
    return time_entries


@router.put("/time-entries/{entry_id}", response_model=TimeEntry)
def update_time_entry(entry_id: int, entry_update: TimeEntryUpdate, db: Session = Depends(get_db)):
    """Update a time entry (for adjustments)"""
    from app.database.models import TimeEntry as TimeEntryModel
    
    time_entry = db.query(TimeEntryModel).filter(TimeEntryModel.id == entry_id).first()
    
    if not time_entry:
        raise HTTPException(status_code=404, detail="Time entry not found")
    
    update_data = entry_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(time_entry, field, value)
    
    time_entry.adjusted_at = datetime.now()
    db.commit()
    db.refresh(time_entry)
    return time_entry


# Work Schedule Endpoints
@router.post("/work-schedules/", response_model=WorkSchedule)
def create_work_schedule(schedule: WorkScheduleCreate, db: Session = Depends(get_db)):
    """Create a work schedule for an employee"""
    from app.database.models import WorkSchedule as WorkScheduleModel
    
    db_schedule = WorkScheduleModel(**schedule.dict())
    db.add(db_schedule)
    db.commit()
    db.refresh(db_schedule)
    return db_schedule


@router.get("/work-schedules/", response_model=List[WorkSchedule])
def get_work_schedules(
    employee_id: Optional[str] = None,
    day_of_week: Optional[int] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """Get work schedules with optional filtering"""
    from app.database.models import WorkSchedule as WorkScheduleModel
    
    query = db.query(WorkScheduleModel)
    
    if employee_id:
        query = query.filter(WorkScheduleModel.employee_id == employee_id)
    if day_of_week is not None:
        query = query.filter(WorkScheduleModel.day_of_week == day_of_week)
    if is_active is not None:
        query = query.filter(WorkScheduleModel.is_active == is_active)
    
    schedules = query.all()
    return schedules


# Timesheet Endpoints
@router.get("/timesheets/{employee_id}", response_model=TimesheetSummary)
def get_employee_timesheet(
    employee_id: str,
    week_start_date: date = Query(..., description="Week start date (Monday)"),
    db: Session = Depends(get_db)
):
    """Get timesheet summary for an employee for a specific week"""
    time_service = TimeTrackingService(db)
    timesheet_data = time_service.get_employee_timesheet(employee_id, week_start_date)
    
    # Get employee info
    from app.database.models import Employee as EmployeeModel
    employee = db.query(EmployeeModel).filter(EmployeeModel.employee_id == employee_id).first()
    
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    # Calculate total pay
    hourly_rate = employee.hourly_rate
    total_pay = (
        timesheet_data["regular_hours"] * hourly_rate +
        timesheet_data["overtime_hours_1_5x"] * hourly_rate * Decimal('1.5') +
        timesheet_data["overtime_hours_2_0x"] * hourly_rate * Decimal('2.0') +
        timesheet_data["overtime_hours_1_6x"] * hourly_rate * Decimal('1.6')
    )
    
    return TimesheetSummary(
        employee_id=employee_id,
        employee_name=f"{employee.first_name} {employee.last_name}",
        week_start_date=week_start_date,
        week_end_date=week_start_date + timedelta(days=6),
        total_hours=timesheet_data["total_hours"],
        regular_hours=timesheet_data["regular_hours"],
        overtime_hours_1_5x=timesheet_data["overtime_hours_1_5x"],
        overtime_hours_2_0x=timesheet_data["overtime_hours_2_0x"],
        overtime_hours_1_6x=timesheet_data["overtime_hours_1_6x"],
        paid_holiday_hours=Decimal('0'),  # Will be calculated separately
        total_pay=total_pay,
        status="pending",
        shifts_worked=len([d for d, h in timesheet_data["daily_hours"].items() if h > 0]),
        holiday_eligible=timesheet_data["holiday_eligible"]
    )


@router.post("/timesheets/approve", response_model=dict)
def approve_timesheet(approval_request: TimesheetApprovalRequest, db: Session = Depends(get_db)):
    """Approve or reject a timesheet"""
    from app.database.models import Timesheet as TimesheetModel
    
    timesheet = db.query(TimesheetModel).filter(TimesheetModel.id == approval_request.timesheet_id).first()
    
    if not timesheet:
        raise HTTPException(status_code=404, detail="Timesheet not found")
    
    timesheet.status = approval_request.action.lower()
    timesheet.notes = approval_request.notes
    
    if approval_request.action.lower() == "approve":
        timesheet.approved_at = datetime.now()
        timesheet.approved_by = "system"  # Should come from authentication
    
    db.commit()
    db.refresh(timesheet)
    
    return {"message": f"Timesheet {approval_request.action.lower()} successfully"}


# Overtime Endpoints
@router.get("/overtime/report/{employee_id}", response_model=OvertimeReport)
def get_overtime_report(
    employee_id: str,
    report_date: date = Query(..., description="Date for overtime report"),
    db: Session = Depends(get_db)
):
    """Get detailed overtime report for an employee"""
    overtime_service = OvertimeService(db)
    return overtime_service.get_overtime_report(employee_id, report_date)


@router.get("/overtime/summary", response_model=dict)
def get_overtime_summary(
    start_date: date = Query(..., description="Start date for overtime summary"),
    end_date: date = Query(..., description="End date for overtime summary"),
    department: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get overtime summary for all employees or department"""
    overtime_service = OvertimeService(db)
    return overtime_service.get_overtime_summary_for_period(start_date, end_date, department)


# Holiday Management Endpoints
@router.post("/holidays/allocate", response_model=dict)
def allocate_paid_holidays(
    week_start_date: date = Query(..., description="Week start date for holiday allocation"),
    db: Session = Depends(get_db)
):
    """Allocate paid holidays for a specific week"""
    holiday_service = HolidayService(db)
    return holiday_service.allocate_paid_holidays(week_start_date)


@router.get("/holidays/eligibility", response_model=dict)
def get_holiday_eligibility_report(
    week_start_date: date = Query(..., description="Week start date for eligibility report"),
    db: Session = Depends(get_db)
):
    """Get holiday eligibility report for all employees"""
    holiday_service = HolidayService(db)
    return holiday_service.get_holiday_eligibility_report(week_start_date)


@router.post("/holidays/override", response_model=dict)
def create_holiday_override(override_request: HolidayOverrideRequest, db: Session = Depends(get_db)):
    """Create a holiday override for special cases"""
    holiday_service = HolidayService(db)
    return holiday_service.create_holiday_override(override_request.dict())


@router.get("/holidays/config", response_model=List[HolidayConfig])
def get_holiday_configurations(
    year: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Get holiday configurations"""
    holiday_service = HolidayService(db)
    return holiday_service.get_holiday_configurations(year)


@router.post("/holidays/config", response_model=dict)
def create_holiday_configuration(holiday_data: HolidayConfigCreate, db: Session = Depends(get_db)):
    """Create a new holiday configuration"""
    holiday_service = HolidayService(db)
    return holiday_service.create_holiday_configuration(holiday_data.dict())


# Compliance and Reporting Endpoints
@router.get("/compliance/report", response_model=ComplianceReport)
def get_compliance_report(
    report_date: date = Query(..., description="Date for compliance report"),
    db: Session = Depends(get_db)
):
    """Get compliance report for California labor law violations"""
    from app.database.models import Employee as EmployeeModel, MissedPunchAlert, OvertimeViolation
    from sqlalchemy import func
    
    # Get total employees
    total_employees = db.query(EmployeeModel).filter(EmployeeModel.status == "active").count()
    
    # Get missed punch alerts for the date
    missed_punches = db.query(MissedPunchAlert).filter(
        MissedPunchAlert.alert_date == report_date,
        MissedPunchAlert.resolved == False
    ).count()
    
    # Get overtime violations for the date
    overtime_violations = db.query(OvertimeViolation).filter(
        OvertimeViolation.violation_date == report_date,
        OvertimeViolation.resolved == False
    ).count()
    
    # Get grace period violations (missed punches that used grace period)
    grace_period_violations = db.query(MissedPunchAlert).filter(
        MissedPunchAlert.alert_date == report_date,
        MissedPunchAlert.grace_period_used == True,
        MissedPunchAlert.resolved == False
    ).count()
    
    total_violations = missed_punches + overtime_violations + grace_period_violations
    
    return ComplianceReport(
        report_date=report_date,
        total_employees=total_employees,
        compliance_violations=total_violations,
        overtime_violations=overtime_violations,
        missed_punches=missed_punches,
        grace_period_violations=grace_period_violations,
        details=[
            {
                "violation_type": "missed_punch",
                "count": missed_punches,
                "description": "Employees with missed clock in/out punches"
            },
            {
                "violation_type": "overtime",
                "count": overtime_violations,
                "description": "Overtime violations exceeding California limits"
            },
            {
                "violation_type": "grace_period",
                "count": grace_period_violations,
                "description": "Employees using grace period for punches"
            }
        ]
    )


# Overtime Configuration Endpoints
@router.post("/overtime/config", response_model=OvertimeConfig)
def create_overtime_config(config: OvertimeConfigCreate, db: Session = Depends(get_db)):
    """Create overtime configuration"""
    from app.database.models import OvertimeConfig as OvertimeConfigModel
    
    db_config = OvertimeConfigModel(**config.dict())
    db.add(db_config)
    db.commit()
    db.refresh(db_config)
    return db_config


@router.get("/overtime/config", response_model=List[OvertimeConfig])
def get_overtime_configs(
    is_active: Optional[bool] = None,
    rule_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get overtime configurations"""
    from app.database.models import OvertimeConfig as OvertimeConfigModel
    
    query = db.query(OvertimeConfigModel)
    
    if is_active is not None:
        query = query.filter(OvertimeConfigModel.is_active == is_active)
    if rule_type:
        query = query.filter(OvertimeConfigModel.rule_type == rule_type)
    
    configs = query.all()
    return configs


@router.put("/overtime/config/{config_id}", response_model=OvertimeConfig)
def update_overtime_config(config_id: int, config_update: OvertimeConfigUpdate, db: Session = Depends(get_db)):
    """Update overtime configuration"""
    from app.database.models import OvertimeConfig as OvertimeConfigModel
    
    config = db.query(OvertimeConfigModel).filter(OvertimeConfigModel.id == config_id).first()
    
    if not config:
        raise HTTPException(status_code=404, detail="Overtime configuration not found")
    
    update_data = config_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(config, field, value)
    
    db.commit()
    db.refresh(config)
    return config


# Missing import
from datetime import timedelta