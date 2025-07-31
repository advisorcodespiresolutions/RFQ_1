from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float, ForeignKey, Text, Enum, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import enum

Base = declarative_base()

class PunchType(enum.Enum):
    CLOCK_IN = "clock_in"
    CLOCK_OUT = "clock_out"
    BREAK_START = "break_start"
    BREAK_END = "break_end"

class TimeEntryStatus(enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    ADJUSTED = "adjusted"

class OvertimeType(enum.Enum):
    DAILY_8H = "daily_8h"  # >8 hours/day
    DAILY_12H = "daily_12h"  # >12 hours/day
    WEEKLY_40H = "weekly_40h"  # >40 hours/week
    SEVENTH_DAY = "seventh_day"  # 7th consecutive day
    SIXTEEN_PLUS = "sixteen_plus"  # >16 hours in single shift

class Employee(Base):
    __tablename__ = "employees"
    
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(String(50), unique=True, index=True, nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    phone = Column(String(20))
    hire_date = Column(DateTime, nullable=False)
    termination_date = Column(DateTime)
    is_active = Column(Boolean, default=True)
    manager_id = Column(Integer, ForeignKey("employees.id"))
    hourly_rate = Column(Float, nullable=False)
    location_id = Column(Integer, ForeignKey("locations.id"))
    
    # Relationships
    time_entries = relationship("TimeEntry", back_populates="employee")
    schedules = relationship("Schedule", back_populates="employee")
    holidays = relationship("PaidHoliday", back_populates="employee")
    manager = relationship("Employee", remote_side=[id])
    subordinates = relationship("Employee", back_populates="manager")

class Location(Base):
    __tablename__ = "locations"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    address = Column(Text, nullable=False)
    latitude = Column(Float)
    longitude = Column(Float)
    geofence_radius = Column(Float, default=100.0)  # meters
    is_active = Column(Boolean, default=True)

class TimeEntry(Base):
    __tablename__ = "time_entries"
    
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    punch_type = Column(Enum(PunchType), nullable=False)
    punch_time = Column(DateTime, nullable=False)
    location_id = Column(Integer, ForeignKey("locations.id"))
    latitude = Column(Float)
    longitude = Column(Float)
    device_type = Column(String(50))  # web, mobile, biometric
    ip_address = Column(String(45))
    user_agent = Column(Text)
    is_within_grace_period = Column(Boolean, default=False)
    status = Column(Enum(TimeEntryStatus), default=TimeEntryStatus.PENDING)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    employee = relationship("Employee", back_populates="time_entries")
    location = relationship("Location")
    adjustments = relationship("TimeEntryAdjustment", back_populates="time_entry")

class TimeEntryAdjustment(Base):
    __tablename__ = "time_entry_adjustments"
    
    id = Column(Integer, primary_key=True, index=True)
    time_entry_id = Column(Integer, ForeignKey("time_entries.id"), nullable=False)
    adjusted_by_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    original_time = Column(DateTime, nullable=False)
    adjusted_time = Column(DateTime, nullable=False)
    reason = Column(Text, nullable=False)
    approved_by_id = Column(Integer, ForeignKey("employees.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    time_entry = relationship("TimeEntry", back_populates="adjustments")
    adjusted_by = relationship("Employee", foreign_keys=[adjusted_by_id])
    approved_by = relationship("Employee", foreign_keys=[approved_by_id])

class Schedule(Base):
    __tablename__ = "schedules"
    
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    date = Column(DateTime, nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    break_duration = Column(Integer, default=30)  # minutes
    is_holiday = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    employee = relationship("Employee", back_populates="schedules")

class PaidHoliday(Base):
    __tablename__ = "paid_holidays"
    
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    date = Column(DateTime, nullable=False)
    hours_paid = Column(Float, default=8.0)
    is_auto_allocated = Column(Boolean, default=True)
    allocated_by_id = Column(Integer, ForeignKey("employees.id"))
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    employee = relationship("Employee", back_populates="holidays")
    allocated_by = relationship("Employee", foreign_keys=[allocated_by_id])

class OvertimeCalculation(Base):
    __tablename__ = "overtime_calculations"
    
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    date = Column(DateTime, nullable=False)
    overtime_type = Column(Enum(OvertimeType), nullable=False)
    hours_worked = Column(Float, nullable=False)
    overtime_hours = Column(Float, nullable=False)
    overtime_rate = Column(Float, nullable=False)  # 1.5, 2.0, 1.6
    base_hourly_rate = Column(Float, nullable=False)
    overtime_pay = Column(Float, nullable=False)
    calculation_details = Column(JSON)  # Store detailed breakdown
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    employee = relationship("Employee")

class ComplianceAudit(Base):
    __tablename__ = "compliance_audits"
    
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    audit_date = Column(DateTime, nullable=False)
    violation_type = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    severity = Column(String(20))  # low, medium, high, critical
    resolved = Column(Boolean, default=False)
    resolved_by_id = Column(Integer, ForeignKey("employees.id"))
    resolved_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    employee = relationship("Employee", foreign_keys=[employee_id])
    resolved_by = relationship("Employee", foreign_keys=[resolved_by_id])

class MissedPunchAlert(Base):
    __tablename__ = "missed_punch_alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    date = Column(DateTime, nullable=False)
    expected_punch_type = Column(Enum(PunchType), nullable=False)
    alert_sent_at = Column(DateTime, default=datetime.utcnow)
    resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime)
    
    # Relationships
    employee = relationship("Employee")