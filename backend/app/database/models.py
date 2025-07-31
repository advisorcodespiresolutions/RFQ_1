"""
Database models for the RFQ platform
"""

from sqlalchemy import Column, Integer, String, DateTime, Date, Time, Boolean, Text, Numeric, ForeignKey, JSON, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime

Base = declarative_base()


class Employee(Base):
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(String(50), unique=True, index=True, nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    phone = Column(String(20))
    hire_date = Column(Date, nullable=False)
    status = Column(String(20), default="active", nullable=False)
    hourly_rate = Column(Numeric(10, 2), nullable=False)
    manager_id = Column(String(50), ForeignKey("employees.employee_id"))
    department = Column(String(100))
    location = Column(String(100))
    geo_fence_enabled = Column(Boolean, default=False)
    geo_fence_coordinates = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    time_entries = relationship("TimeEntry", back_populates="employee")
    work_schedules = relationship("WorkSchedule", back_populates="employee")
    timesheets = relationship("Timesheet", back_populates="employee")
    managed_employees = relationship("Employee", backref="manager")

    __table_args__ = (
        Index('idx_employee_status', 'status'),
        Index('idx_employee_department', 'department'),
        Index('idx_employee_location', 'location'),
    )


class TimeEntry(Base):
    __tablename__ = "time_entries"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(String(50), ForeignKey("employees.employee_id"), nullable=False)
    punch_type = Column(String(20), nullable=False)  # clock_in, clock_out, break_start, break_end
    punch_time = Column(DateTime(timezone=True), nullable=False)
    location = Column(String(100))
    latitude = Column(Numeric(10, 8))
    longitude = Column(Numeric(11, 8))
    device_type = Column(String(20))  # web, mobile, biometric
    notes = Column(Text)
    status = Column(String(20), default="pending", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    adjusted_at = Column(DateTime(timezone=True))
    adjustment_reason = Column(Text)
    adjusted_by = Column(String(50))

    # Relationships
    employee = relationship("Employee", back_populates="time_entries")

    __table_args__ = (
        Index('idx_time_entry_employee_date', 'employee_id', 'punch_time'),
        Index('idx_time_entry_punch_type', 'punch_type'),
        Index('idx_time_entry_status', 'status'),
        Index('idx_time_entry_device', 'device_type'),
    )


class WorkSchedule(Base):
    __tablename__ = "work_schedules"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(String(50), ForeignKey("employees.employee_id"), nullable=False)
    day_of_week = Column(Integer, nullable=False)  # 0=Monday, 6=Sunday
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    break_duration_minutes = Column(Integer, default=30)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    employee = relationship("Employee", back_populates="work_schedules")

    __table_args__ = (
        Index('idx_work_schedule_employee_day', 'employee_id', 'day_of_week'),
        Index('idx_work_schedule_active', 'is_active'),
    )


class OvertimeConfig(Base):
    __tablename__ = "overtime_configs"

    id = Column(Integer, primary_key=True, index=True)
    rule_name = Column(String(100), nullable=False)
    rule_type = Column(String(50), nullable=False)  # daily_8_hours, daily_12_hours, weekly_7th_day, shift_16_hours
    threshold_hours = Column(Numeric(5, 2), nullable=False)
    multiplier = Column(Numeric(3, 2), nullable=False)
    is_active = Column(Boolean, default=True)
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index('idx_overtime_config_type', 'rule_type'),
        Index('idx_overtime_config_active', 'is_active'),
    )


class HolidayConfig(Base):
    __tablename__ = "holiday_configs"

    id = Column(Integer, primary_key=True, index=True)
    holiday_name = Column(String(100), nullable=False)
    holiday_type = Column(String(20), nullable=False)  # paid_holiday, unpaid_holiday, floating_holiday
    date = Column(Date, nullable=False)
    is_active = Column(Boolean, default=True)
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index('idx_holiday_config_date', 'date'),
        Index('idx_holiday_config_type', 'holiday_type'),
        Index('idx_holiday_config_active', 'is_active'),
    )


class Timesheet(Base):
    __tablename__ = "timesheets"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(String(50), ForeignKey("employees.employee_id"), nullable=False)
    week_start_date = Column(Date, nullable=False)
    week_end_date = Column(Date, nullable=False)
    total_hours = Column(Numeric(8, 2), default=0)
    regular_hours = Column(Numeric(8, 2), default=0)
    overtime_hours_1_5x = Column(Numeric(8, 2), default=0)
    overtime_hours_2_0x = Column(Numeric(8, 2), default=0)
    overtime_hours_1_6x = Column(Numeric(8, 2), default=0)
    paid_holiday_hours = Column(Numeric(8, 2), default=0)
    status = Column(String(20), default="pending", nullable=False)
    notes = Column(Text)
    approved_by = Column(String(50))
    approved_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    employee = relationship("Employee", back_populates="timesheets")

    __table_args__ = (
        Index('idx_timesheet_employee_week', 'employee_id', 'week_start_date'),
        Index('idx_timesheet_status', 'status'),
        Index('idx_timesheet_approved_by', 'approved_by'),
    )


class HolidayOverride(Base):
    __tablename__ = "holiday_overrides"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(String(50), ForeignKey("employees.employee_id"), nullable=False)
    week_start_date = Column(Date, nullable=False)
    holiday_hours = Column(Numeric(8, 2), nullable=False)
    reason = Column(Text, nullable=False)
    approved_by = Column(String(50), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index('idx_holiday_override_employee_week', 'employee_id', 'week_start_date'),
        Index('idx_holiday_override_approved_by', 'approved_by'),
    )


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    table_name = Column(String(50), nullable=False)
    record_id = Column(Integer, nullable=False)
    action = Column(String(20), nullable=False)  # CREATE, UPDATE, DELETE, APPROVE, REJECT
    old_values = Column(JSON)
    new_values = Column(JSON)
    user_id = Column(String(50), nullable=False)
    ip_address = Column(String(45))
    user_agent = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index('idx_audit_log_table_record', 'table_name', 'record_id'),
        Index('idx_audit_log_action', 'action'),
        Index('idx_audit_log_user', 'user_id'),
        Index('idx_audit_log_created', 'created_at'),
    )


class MissedPunchAlert(Base):
    __tablename__ = "missed_punch_alerts"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(String(50), ForeignKey("employees.employee_id"), nullable=False)
    alert_date = Column(Date, nullable=False)
    alert_type = Column(String(20), nullable=False)  # clock_in, clock_out, break_start, break_end
    expected_time = Column(Time, nullable=False)
    actual_time = Column(Time)
    grace_period_used = Column(Boolean, default=False)
    resolved = Column(Boolean, default=False)
    resolved_by = Column(String(50))
    resolved_at = Column(DateTime(timezone=True))
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index('idx_missed_punch_employee_date', 'employee_id', 'alert_date'),
        Index('idx_missed_punch_resolved', 'resolved'),
        Index('idx_missed_punch_type', 'alert_type'),
    )


class OvertimeViolation(Base):
    __tablename__ = "overtime_violations"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(String(50), ForeignKey("employees.employee_id"), nullable=False)
    violation_date = Column(Date, nullable=False)
    violation_type = Column(String(50), nullable=False)  # daily_8_hours, daily_12_hours, weekly_7th_day, shift_16_hours
    hours_worked = Column(Numeric(8, 2), nullable=False)
    threshold_hours = Column(Numeric(8, 2), nullable=False)
    overtime_hours = Column(Numeric(8, 2), nullable=False)
    multiplier_applied = Column(Numeric(3, 2), nullable=False)
    resolved = Column(Boolean, default=False)
    resolved_by = Column(String(50))
    resolved_at = Column(DateTime(timezone=True))
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index('idx_overtime_violation_employee_date', 'employee_id', 'violation_date'),
        Index('idx_overtime_violation_type', 'violation_type'),
        Index('idx_overtime_violation_resolved', 'resolved'),
    )


class PayrollExport(Base):
    __tablename__ = "payroll_exports"

    id = Column(Integer, primary_key=True, index=True)
    export_date = Column(Date, nullable=False)
    pay_period_start = Column(Date, nullable=False)
    pay_period_end = Column(Date, nullable=False)
    export_format = Column(String(10), nullable=False)  # CSV, XML, JSON
    file_path = Column(String(255))
    total_employees = Column(Integer, default=0)
    total_hours = Column(Numeric(10, 2), default=0)
    total_pay = Column(Numeric(12, 2), default=0)
    exported_by = Column(String(50), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index('idx_payroll_export_date', 'export_date'),
        Index('idx_payroll_export_period', 'pay_period_start', 'pay_period_end'),
        Index('idx_payroll_export_format', 'export_format'),
    )