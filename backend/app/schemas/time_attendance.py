from datetime import datetime, time, date
from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field, validator
from decimal import Decimal


class PunchType(str, Enum):
    CLOCK_IN = "clock_in"
    CLOCK_OUT = "clock_out"
    BREAK_START = "break_start"
    BREAK_END = "break_end"


class OvertimeRule(str, Enum):
    DAILY_8_HOURS = "daily_8_hours"  # >8 hours/day = 1.5x
    DAILY_12_HOURS = "daily_12_hours"  # >12 hours/day = 2.0x
    WEEKLY_7TH_DAY = "weekly_7th_day"  # 7th consecutive day = 2.0x beyond 8 hours
    SHIFT_16_HOURS = "shift_16_hours"  # >16 hours in single shift = 1.6x


class EmployeeStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    TERMINATED = "terminated"


class TimeEntryStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    ADJUSTED = "adjusted"


class HolidayType(str, Enum):
    PAID_HOLIDAY = "paid_holiday"
    UNPAID_HOLIDAY = "unpaid_holiday"
    FLOATING_HOLIDAY = "floating_holiday"


# Base Models
class EmployeeBase(BaseModel):
    employee_id: str = Field(..., description="Unique employee identifier")
    first_name: str
    last_name: str
    email: str
    phone: Optional[str] = None
    hire_date: date
    status: EmployeeStatus = EmployeeStatus.ACTIVE
    hourly_rate: Decimal = Field(..., ge=0, description="Base hourly rate")
    manager_id: Optional[str] = None
    department: Optional[str] = None
    location: Optional[str] = None
    geo_fence_enabled: bool = False
    geo_fence_coordinates: Optional[List[Dict[str, float]]] = None


class EmployeeCreate(EmployeeBase):
    pass


class EmployeeUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    status: Optional[EmployeeStatus] = None
    hourly_rate: Optional[Decimal] = None
    manager_id: Optional[str] = None
    department: Optional[str] = None
    location: Optional[str] = None
    geo_fence_enabled: Optional[bool] = None
    geo_fence_coordinates: Optional[List[Dict[str, float]]] = None


class Employee(EmployeeBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Time Entry Models
class TimeEntryBase(BaseModel):
    employee_id: str
    punch_type: PunchType
    punch_time: datetime
    location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    device_type: Optional[str] = None  # web, mobile, biometric
    notes: Optional[str] = None


class TimeEntryCreate(TimeEntryBase):
    pass


class TimeEntryUpdate(BaseModel):
    punch_time: Optional[datetime] = None
    location: Optional[str] = None
    notes: Optional[str] = None
    adjustment_reason: Optional[str] = None
    adjusted_by: Optional[str] = None


class TimeEntry(TimeEntryBase):
    id: int
    status: TimeEntryStatus = TimeEntryStatus.PENDING
    created_at: datetime
    updated_at: datetime
    adjusted_at: Optional[datetime] = None
    adjustment_reason: Optional[str] = None
    adjusted_by: Optional[str] = None

    class Config:
        from_attributes = True


# Work Schedule Models
class WorkScheduleBase(BaseModel):
    employee_id: str
    day_of_week: int = Field(..., ge=0, le=6, description="0=Monday, 6=Sunday")
    start_time: time
    end_time: time
    break_duration_minutes: int = Field(default=30, ge=0)
    is_active: bool = True


class WorkScheduleCreate(WorkScheduleBase):
    pass


class WorkScheduleUpdate(BaseModel):
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    break_duration_minutes: Optional[int] = None
    is_active: Optional[bool] = None


class WorkSchedule(WorkScheduleBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Overtime Configuration Models
class OvertimeConfigBase(BaseModel):
    rule_name: str
    rule_type: OvertimeRule
    threshold_hours: Decimal
    multiplier: Decimal = Field(..., ge=1.0)
    is_active: bool = True
    description: Optional[str] = None


class OvertimeConfigCreate(OvertimeConfigBase):
    pass


class OvertimeConfigUpdate(BaseModel):
    threshold_hours: Optional[Decimal] = None
    multiplier: Optional[Decimal] = None
    is_active: Optional[bool] = None
    description: Optional[str] = None


class OvertimeConfig(OvertimeConfigBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Holiday Configuration Models
class HolidayConfigBase(BaseModel):
    holiday_name: str
    holiday_type: HolidayType
    date: date
    is_active: bool = True
    description: Optional[str] = None


class HolidayConfigCreate(HolidayConfigBase):
    pass


class HolidayConfigUpdate(BaseModel):
    holiday_name: Optional[str] = None
    holiday_type: Optional[HolidayType] = None
    date: Optional[date] = None
    is_active: Optional[bool] = None
    description: Optional[str] = None


class HolidayConfig(HolidayConfigBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Timesheet Models
class TimesheetBase(BaseModel):
    employee_id: str
    week_start_date: date
    week_end_date: date
    total_hours: Decimal = Field(default=0, ge=0)
    regular_hours: Decimal = Field(default=0, ge=0)
    overtime_hours_1_5x: Decimal = Field(default=0, ge=0)
    overtime_hours_2_0x: Decimal = Field(default=0, ge=0)
    overtime_hours_1_6x: Decimal = Field(default=0, ge=0)
    paid_holiday_hours: Decimal = Field(default=0, ge=0)
    status: TimeEntryStatus = TimeEntryStatus.PENDING
    notes: Optional[str] = None


class TimesheetCreate(TimesheetBase):
    pass


class TimesheetUpdate(BaseModel):
    total_hours: Optional[Decimal] = None
    regular_hours: Optional[Decimal] = None
    overtime_hours_1_5x: Optional[Decimal] = None
    overtime_hours_2_0x: Optional[Decimal] = None
    overtime_hours_1_6x: Optional[Decimal] = None
    paid_holiday_hours: Optional[Decimal] = None
    status: Optional[TimeEntryStatus] = None
    notes: Optional[str] = None


class Timesheet(TimesheetBase):
    id: int
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Audit Log Models
class AuditLogBase(BaseModel):
    table_name: str
    record_id: int
    action: str  # CREATE, UPDATE, DELETE, APPROVE, REJECT
    old_values: Optional[Dict[str, Any]] = None
    new_values: Optional[Dict[str, Any]] = None
    user_id: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


class AuditLogCreate(AuditLogBase):
    pass


class AuditLog(AuditLogBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# API Response Models
class PunchResponse(BaseModel):
    success: bool
    message: str
    time_entry: Optional[TimeEntry] = None
    grace_period_used: bool = False


class TimesheetSummary(BaseModel):
    employee_id: str
    employee_name: str
    week_start_date: date
    week_end_date: date
    total_hours: Decimal
    regular_hours: Decimal
    overtime_hours_1_5x: Decimal
    overtime_hours_2_0x: Decimal
    overtime_hours_1_6x: Decimal
    paid_holiday_hours: Decimal
    total_pay: Decimal
    status: TimeEntryStatus
    shifts_worked: int
    holiday_eligible: bool


class OvertimeReport(BaseModel):
    employee_id: str
    employee_name: str
    date: date
    total_hours: Decimal
    regular_hours: Decimal
    overtime_hours: Dict[str, Decimal]  # rate_code: hours
    overtime_pay: Decimal
    rules_applied: List[str]


class ComplianceReport(BaseModel):
    report_date: date
    total_employees: int
    compliance_violations: int
    overtime_violations: int
    missed_punches: int
    grace_period_violations: int
    details: List[Dict[str, Any]]


# Request Models
class PunchRequest(BaseModel):
    employee_id: str
    punch_type: PunchType
    location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    device_type: Optional[str] = None
    notes: Optional[str] = None

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


class TimesheetApprovalRequest(BaseModel):
    timesheet_id: int
    action: str  # APPROVE or REJECT
    notes: Optional[str] = None


class HolidayOverrideRequest(BaseModel):
    employee_id: str
    week_start_date: date
    holiday_hours: Decimal
    reason: str
    approved_by: str