from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime, date, time
from enum import Enum

class PunchType(str, Enum):
    CLOCK_IN = "clock_in"
    CLOCK_OUT = "clock_out"
    BREAK_START = "break_start"
    BREAK_END = "break_end"

class TimeEntryStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    ADJUSTED = "adjusted"

class OvertimeType(str, Enum):
    DAILY_8H = "daily_8h"
    DAILY_12H = "daily_12h"
    WEEKLY_40H = "weekly_40h"
    SEVENTH_DAY = "seventh_day"
    SIXTEEN_PLUS = "sixteen_plus"

# Employee Schemas
class EmployeeBase(BaseModel):
    employee_id: str = Field(..., min_length=1, max_length=50)
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    email: str = Field(..., regex=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
    phone: Optional[str] = Field(None, max_length=20)
    hire_date: datetime
    hourly_rate: float = Field(..., gt=0)
    location_id: int = Field(..., gt=0)

class EmployeeCreate(EmployeeBase):
    manager_id: Optional[int] = None

class EmployeeUpdate(BaseModel):
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[str] = Field(None, regex=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
    phone: Optional[str] = Field(None, max_length=20)
    hourly_rate: Optional[float] = Field(None, gt=0)
    location_id: Optional[int] = Field(None, gt=0)
    manager_id: Optional[int] = None
    is_active: Optional[bool] = None

class Employee(EmployeeBase):
    id: int
    termination_date: Optional[datetime] = None
    is_active: bool
    manager_id: Optional[int] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

# Time Entry Schemas
class TimeEntryBase(BaseModel):
    punch_type: PunchType
    punch_time: datetime
    location_id: Optional[int] = None
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    device_type: Optional[str] = Field(None, max_length=50)
    notes: Optional[str] = None

class TimeEntryCreate(TimeEntryBase):
    employee_id: int = Field(..., gt=0)

class TimeEntryUpdate(BaseModel):
    punch_time: Optional[datetime] = None
    notes: Optional[str] = None
    status: Optional[TimeEntryStatus] = None

class TimeEntry(TimeEntryBase):
    id: int
    employee_id: int
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    is_within_grace_period: bool
    status: TimeEntryStatus
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# Schedule Schemas
class ScheduleBase(BaseModel):
    date: date
    start_time: time
    end_time: time
    break_duration: int = Field(default=30, ge=0, le=480)  # 0-8 hours in minutes
    is_holiday: bool = False

class ScheduleCreate(ScheduleBase):
    employee_id: int = Field(..., gt=0)

class ScheduleUpdate(BaseModel):
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    break_duration: Optional[int] = Field(None, ge=0, le=480)
    is_holiday: Optional[bool] = None

class Schedule(ScheduleBase):
    id: int
    employee_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# Overtime Calculation Schemas
class OvertimeCalculationBase(BaseModel):
    date: date
    overtime_type: OvertimeType
    hours_worked: float = Field(..., ge=0)
    overtime_hours: float = Field(..., ge=0)
    overtime_rate: float = Field(..., gt=1)
    base_hourly_rate: float = Field(..., gt=0)
    overtime_pay: float = Field(..., ge=0)
    calculation_details: Dict[str, Any] = {}

class OvertimeCalculationCreate(OvertimeCalculationBase):
    employee_id: int = Field(..., gt=0)

class OvertimeCalculation(OvertimeCalculationBase):
    id: int
    employee_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# Paid Holiday Schemas
class PaidHolidayBase(BaseModel):
    date: date
    hours_paid: float = Field(default=8.0, gt=0, le=24)
    is_auto_allocated: bool = True
    notes: Optional[str] = None

class PaidHolidayCreate(PaidHolidayBase):
    employee_id: int = Field(..., gt=0)
    allocated_by_id: Optional[int] = None

class PaidHolidayUpdate(BaseModel):
    hours_paid: Optional[float] = Field(None, gt=0, le=24)
    notes: Optional[str] = None

class PaidHoliday(PaidHolidayBase):
    id: int
    employee_id: int
    allocated_by_id: Optional[int] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

# Time Entry Adjustment Schemas
class TimeEntryAdjustmentBase(BaseModel):
    original_time: datetime
    adjusted_time: datetime
    reason: str = Field(..., min_length=1)

class TimeEntryAdjustmentCreate(TimeEntryAdjustmentBase):
    time_entry_id: int = Field(..., gt=0)
    adjusted_by_id: int = Field(..., gt=0)

class TimeEntryAdjustment(TimeEntryAdjustmentBase):
    id: int
    time_entry_id: int
    adjusted_by_id: int
    approved_by_id: Optional[int] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

# Compliance Audit Schemas
class ComplianceAuditBase(BaseModel):
    audit_date: date
    violation_type: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., min_length=1)
    severity: str = Field(..., regex=r"^(low|medium|high|critical)$")

class ComplianceAuditCreate(ComplianceAuditBase):
    employee_id: int = Field(..., gt=0)

class ComplianceAuditUpdate(BaseModel):
    resolved: Optional[bool] = None
    resolved_by_id: Optional[int] = None

class ComplianceAudit(ComplianceAuditBase):
    id: int
    employee_id: int
    resolved: bool
    resolved_by_id: Optional[int] = None
    resolved_at: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

# Report Schemas
class WeeklyHoursSummary(BaseModel):
    employee_id: int
    employee_name: str
    week_start: date
    week_end: date
    total_hours: float
    regular_hours: float
    overtime_hours: float
    holiday_hours: float
    shifts_worked: int
    holiday_eligible: bool

class OvertimeSummary(BaseModel):
    employee_id: int
    employee_name: str
    date: date
    total_hours: float
    overtime_breakdown: Dict[str, float]  # overtime_type: hours
    total_overtime_pay: float
    base_pay: float

class HolidayEligibilityReport(BaseModel):
    employee_id: int
    employee_name: str
    week_start: date
    week_end: date
    shifts_worked: int
    hours_worked: float
    holiday_allocated: bool
    holiday_date: Optional[date] = None
    holiday_hours: Optional[float] = None

# API Response Schemas
class TimeEntryResponse(BaseModel):
    success: bool
    message: str
    time_entry: Optional[TimeEntry] = None
    warnings: List[str] = []

class OvertimeCalculationResponse(BaseModel):
    success: bool
    message: str
    calculations: List[OvertimeCalculation]
    total_overtime_pay: float
    compliance_violations: List[str] = []

class HolidayAllocationResponse(BaseModel):
    success: bool
    message: str
    holidays_allocated: List[PaidHoliday]
    employees_eligible: int
    employees_ineligible: int

# Validation Schemas
class PunchValidation(BaseModel):
    employee_id: int
    punch_type: PunchType
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    device_type: str = Field(..., max_length=50)
    
    @validator('latitude')
    def validate_latitude(cls, v):
        if v is not None and (v < -90 or v > 90):
            raise ValueError('Latitude must be between -90 and 90')
        return v
    
    @validator('longitude')
    def validate_longitude(cls, v):
        if v is not None and (v < -180 or v > 180):
            raise ValueError('Longitude must be between -180 and 180')
        return v