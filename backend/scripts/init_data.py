#!/usr/bin/env python3
"""
Data initialization script for California Retail Time & Attendance System
Creates sample employees, work schedules, overtime configurations, and holiday settings
"""

import sys
import os
from datetime import date, time, timedelta
from decimal import Decimal

# Add the parent directory to the path so we can import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.database import SessionLocal
from app.database.models import (
    Employee, WorkSchedule, OvertimeConfig, HolidayConfig
)


def init_database():
    """Initialize the database with sample data"""
    db = SessionLocal()
    
    try:
        print("Initializing California Retail Time & Attendance System...")
        
        # Create sample employees
        employees = create_sample_employees(db)
        print(f"✅ Created {len(employees)} sample employees")
        
        # Create work schedules
        schedules = create_work_schedules(db, employees)
        print(f"✅ Created {len(schedules)} work schedules")
        
        # Create overtime configurations
        overtime_configs = create_overtime_configurations(db)
        print(f"✅ Created {len(overtime_configs)} overtime configurations")
        
        # Create holiday configurations
        holidays = create_holiday_configurations(db)
        print(f"✅ Created {len(holidays)} holiday configurations")
        
        print("\n🎉 Database initialization completed successfully!")
        print("\nSample data created:")
        print("- 5 retail employees with different schedules")
        print("- California-compliant overtime rules")
        print("- 2024 holiday calendar")
        print("\nYou can now test the API endpoints at http://localhost:8000/docs")
        
    except Exception as e:
        print(f"❌ Error initializing database: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()


def create_sample_employees(db):
    """Create sample retail employees"""
    employees_data = [
        {
            "employee_id": "EMP001",
            "first_name": "Sarah",
            "last_name": "Johnson",
            "email": "sarah.johnson@retailstore.com",
            "phone": "555-0101",
            "hire_date": date(2023, 1, 15),
            "status": "active",
            "hourly_rate": Decimal("18.50"),
            "department": "Sales",
            "location": "Downtown Store",
            "geo_fence_enabled": True,
            "geo_fence_coordinates": [
                {"lat": 37.7749, "lng": -122.4194},
                {"lat": 37.7849, "lng": -122.4094}
            ]
        },
        {
            "employee_id": "EMP002",
            "first_name": "Michael",
            "last_name": "Chen",
            "email": "michael.chen@retailstore.com",
            "phone": "555-0102",
            "hire_date": date(2023, 3, 10),
            "status": "active",
            "hourly_rate": Decimal("17.75"),
            "department": "Inventory",
            "location": "Downtown Store",
            "geo_fence_enabled": True,
            "geo_fence_coordinates": [
                {"lat": 37.7749, "lng": -122.4194},
                {"lat": 37.7849, "lng": -122.4094}
            ]
        },
        {
            "employee_id": "EMP003",
            "first_name": "Maria",
            "last_name": "Garcia",
            "email": "maria.garcia@retailstore.com",
            "phone": "555-0103",
            "hire_date": date(2023, 2, 20),
            "status": "active",
            "hourly_rate": Decimal("19.25"),
            "department": "Sales",
            "location": "Mall Location",
            "geo_fence_enabled": True,
            "geo_fence_coordinates": [
                {"lat": 37.7849, "lng": -122.4094},
                {"lat": 37.7949, "lng": -122.3994}
            ]
        },
        {
            "employee_id": "EMP004",
            "first_name": "David",
            "last_name": "Thompson",
            "email": "david.thompson@retailstore.com",
            "phone": "555-0104",
            "hire_date": date(2023, 4, 5),
            "status": "active",
            "hourly_rate": Decimal("16.50"),
            "department": "Customer Service",
            "location": "Mall Location",
            "geo_fence_enabled": False
        },
        {
            "employee_id": "EMP005",
            "first_name": "Lisa",
            "last_name": "Wang",
            "email": "lisa.wang@retailstore.com",
            "phone": "555-0105",
            "hire_date": date(2023, 1, 30),
            "status": "active",
            "hourly_rate": Decimal("20.00"),
            "department": "Management",
            "location": "Downtown Store",
            "manager_id": "EMP001",
            "geo_fence_enabled": True,
            "geo_fence_coordinates": [
                {"lat": 37.7749, "lng": -122.4194},
                {"lat": 37.7849, "lng": -122.4094}
            ]
        }
    ]
    
    employees = []
    for emp_data in employees_data:
        # Check if employee already exists
        existing = db.query(Employee).filter(Employee.employee_id == emp_data["employee_id"]).first()
        if not existing:
            employee = Employee(**emp_data)
            db.add(employee)
            employees.append(employee)
        else:
            employees.append(existing)
    
    db.commit()
    return employees


def create_work_schedules(db, employees):
    """Create work schedules for employees"""
    schedules = []
    
    # Standard retail schedule: 4 days per week, 8 hours per day
    standard_schedule = [
        # Monday
        {"day_of_week": 0, "start_time": time(9, 0), "end_time": time(17, 30), "break_duration_minutes": 30},
        # Tuesday
        {"day_of_week": 1, "start_time": time(9, 0), "end_time": time(17, 30), "break_duration_minutes": 30},
        # Wednesday
        {"day_of_week": 2, "start_time": time(9, 0), "end_time": time(17, 30), "break_duration_minutes": 30},
        # Thursday
        {"day_of_week": 3, "start_time": time(9, 0), "end_time": time(17, 30), "break_duration_minutes": 30},
    ]
    
    # Evening shift schedule
    evening_schedule = [
        # Monday
        {"day_of_week": 0, "start_time": time(14, 0), "end_time": time(22, 30), "break_duration_minutes": 30},
        # Tuesday
        {"day_of_week": 1, "start_time": time(14, 0), "end_time": time(22, 30), "break_duration_minutes": 30},
        # Wednesday
        {"day_of_week": 2, "start_time": time(14, 0), "end_time": time(22, 30), "break_duration_minutes": 30},
        # Thursday
        {"day_of_week": 3, "start_time": time(14, 0), "end_time": time(22, 30), "break_duration_minutes": 30},
    ]
    
    # Weekend schedule
    weekend_schedule = [
        # Friday
        {"day_of_week": 4, "start_time": time(10, 0), "end_time": time(18, 30), "break_duration_minutes": 30},
        # Saturday
        {"day_of_week": 5, "start_time": time(10, 0), "end_time": time(18, 30), "break_duration_minutes": 30},
        # Sunday
        {"day_of_week": 6, "start_time": time(11, 0), "end_time": time(19, 30), "break_duration_minutes": 30},
    ]
    
    # Assign schedules to employees
    schedule_assignments = [
        (employees[0], standard_schedule),      # Sarah - Standard schedule
        (employees[1], evening_schedule),       # Michael - Evening shift
        (employees[2], standard_schedule),      # Maria - Standard schedule
        (employees[3], weekend_schedule),       # David - Weekend shift
        (employees[4], standard_schedule),      # Lisa - Standard schedule (Manager)
    ]
    
    for employee, schedule_data in schedule_assignments:
        for day_schedule in schedule_data:
            # Check if schedule already exists
            existing = db.query(WorkSchedule).filter(
                WorkSchedule.employee_id == employee.employee_id,
                WorkSchedule.day_of_week == day_schedule["day_of_week"]
            ).first()
            
            if not existing:
                schedule = WorkSchedule(
                    employee_id=employee.employee_id,
                    **day_schedule
                )
                db.add(schedule)
                schedules.append(schedule)
    
    db.commit()
    return schedules


def create_overtime_configurations(db):
    """Create California-compliant overtime configurations"""
    overtime_configs = [
        {
            "rule_name": "Daily 8 Hours Overtime",
            "rule_type": "daily_8_hours",
            "threshold_hours": Decimal("8.0"),
            "multiplier": Decimal("1.5"),
            "description": "California Labor Code §510: Daily overtime for hours worked beyond 8 hours"
        },
        {
            "rule_name": "Daily 12 Hours Double Time",
            "rule_type": "daily_12_hours",
            "threshold_hours": Decimal("12.0"),
            "multiplier": Decimal("2.0"),
            "description": "California Labor Code §510: Double time for hours worked beyond 12 hours"
        },
        {
            "rule_name": "7th Consecutive Day Double Time",
            "rule_type": "weekly_7th_day",
            "threshold_hours": Decimal("8.0"),
            "multiplier": Decimal("2.0"),
            "description": "California Labor Code §510: Double time for 7th consecutive day beyond 8 hours"
        },
        {
            "rule_name": "16-Hour Shift Special Rule",
            "rule_type": "shift_16_hours",
            "threshold_hours": Decimal("16.0"),
            "multiplier": Decimal("1.6"),
            "description": "Special rule: 1.6x pay for hours worked beyond 16 hours in a single shift"
        }
    ]
    
    configs = []
    for config_data in overtime_configs:
        # Check if config already exists
        existing = db.query(OvertimeConfig).filter(
            OvertimeConfig.rule_type == config_data["rule_type"]
        ).first()
        
        if not existing:
            config = OvertimeConfig(**config_data)
            db.add(config)
            configs.append(config)
        else:
            configs.append(existing)
    
    db.commit()
    return configs


def create_holiday_configurations(db):
    """Create 2024 holiday configurations"""
    holidays_2024 = [
        {
            "holiday_name": "New Year's Day",
            "holiday_type": "paid_holiday",
            "date": date(2024, 1, 1),
            "description": "New Year's Day - Paid holiday"
        },
        {
            "holiday_name": "Martin Luther King Jr. Day",
            "holiday_type": "paid_holiday",
            "date": date(2024, 1, 15),
            "description": "Martin Luther King Jr. Day - Paid holiday"
        },
        {
            "holiday_name": "Presidents' Day",
            "holiday_type": "paid_holiday",
            "date": date(2024, 2, 19),
            "description": "Presidents' Day - Paid holiday"
        },
        {
            "holiday_name": "Memorial Day",
            "holiday_type": "paid_holiday",
            "date": date(2024, 5, 27),
            "description": "Memorial Day - Paid holiday"
        },
        {
            "holiday_name": "Independence Day",
            "holiday_type": "paid_holiday",
            "date": date(2024, 7, 4),
            "description": "Independence Day - Paid holiday"
        },
        {
            "holiday_name": "Labor Day",
            "holiday_type": "paid_holiday",
            "date": date(2024, 9, 2),
            "description": "Labor Day - Paid holiday"
        },
        {
            "holiday_name": "Columbus Day",
            "holiday_type": "paid_holiday",
            "date": date(2024, 10, 14),
            "description": "Columbus Day - Paid holiday"
        },
        {
            "holiday_name": "Veterans Day",
            "holiday_type": "paid_holiday",
            "date": date(2024, 11, 11),
            "description": "Veterans Day - Paid holiday"
        },
        {
            "holiday_name": "Thanksgiving Day",
            "holiday_type": "paid_holiday",
            "date": date(2024, 11, 28),
            "description": "Thanksgiving Day - Paid holiday"
        },
        {
            "holiday_name": "Christmas Day",
            "holiday_type": "paid_holiday",
            "date": date(2024, 12, 25),
            "description": "Christmas Day - Paid holiday"
        }
    ]
    
    holidays = []
    for holiday_data in holidays_2024:
        # Check if holiday already exists
        existing = db.query(HolidayConfig).filter(
            HolidayConfig.date == holiday_data["date"]
        ).first()
        
        if not existing:
            holiday = HolidayConfig(**holiday_data)
            db.add(holiday)
            holidays.append(holiday)
        else:
            holidays.append(existing)
    
    db.commit()
    return holidays


if __name__ == "__main__":
    init_database()