#!/usr/bin/env python3
"""
Test script for California Retail Time & Attendance System
Demonstrates key functionality including punch operations, overtime calculations, and holiday management
"""

import sys
import os
from datetime import datetime, date, time, timedelta
from decimal import Decimal

# Add the current directory to the path so we can import from app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database.database import SessionLocal
from app.services.time_tracking_service import TimeTrackingService
from app.services.overtime_service import OvertimeService
from app.services.holiday_service import HolidayService
from app.schemas.time_attendance import PunchRequest, PunchType


def test_time_tracking():
    """Test time tracking functionality"""
    print("🕐 Testing Time Tracking System...")
    
    db = SessionLocal()
    time_service = TimeTrackingService(db)
    
    try:
        # Test 1: Clock in
        print("\n1. Testing Clock In...")
        punch_request = PunchRequest(
            employee_id="EMP001",
            punch_type=PunchType.CLOCK_IN,
            location="Downtown Store",
            device_type="web",
            notes="Morning shift start"
        )
        
        response = time_service.process_punch(punch_request)
        print(f"✅ Clock In Result: {response.message}")
        print(f"   Grace Period Used: {response.grace_period_used}")
        
        # Test 2: Break start
        print("\n2. Testing Break Start...")
        break_start_request = PunchRequest(
            employee_id="EMP001",
            punch_type=PunchType.BREAK_START,
            location="Downtown Store",
            device_type="web"
        )
        
        response = time_service.process_punch(break_start_request)
        print(f"✅ Break Start Result: {response.message}")
        
        # Test 3: Break end
        print("\n3. Testing Break End...")
        break_end_request = PunchRequest(
            employee_id="EMP001",
            punch_type=PunchType.BREAK_END,
            location="Downtown Store",
            device_type="web"
        )
        
        response = time_service.process_punch(break_end_request)
        print(f"✅ Break End Result: {response.message}")
        
        # Test 4: Clock out
        print("\n4. Testing Clock Out...")
        clock_out_request = PunchRequest(
            employee_id="EMP001",
            punch_type=PunchType.CLOCK_OUT,
            location="Downtown Store",
            device_type="web",
            notes="End of shift"
        )
        
        response = time_service.process_punch(clock_out_request)
        print(f"✅ Clock Out Result: {response.message}")
        
    except Exception as e:
        print(f"❌ Error in time tracking test: {str(e)}")
    finally:
        db.close()


def test_overtime_calculation():
    """Test overtime calculation functionality"""
    print("\n💰 Testing Overtime Calculation System...")
    
    db = SessionLocal()
    overtime_service = OvertimeService(db)
    
    try:
        # Test overtime calculation for a week
        week_start = date.today() - timedelta(days=date.today().weekday())
        employee_id = "EMP001"
        
        print(f"\nCalculating overtime for employee {employee_id} for week starting {week_start}")
        
        overtime_result = overtime_service.calculate_overtime_for_period(
            employee_id, week_start, week_start + timedelta(days=6)
        )
        
        print("✅ Overtime Calculation Results:")
        print(f"   Regular Hours: {overtime_result['regular_hours']}")
        print(f"   Overtime 1.5x: {overtime_result['overtime_1_5x']}")
        print(f"   Overtime 2.0x: {overtime_result['overtime_2_0x']}")
        print(f"   Overtime 1.6x: {overtime_result['overtime_1_6x']}")
        print(f"   Total Hours: {overtime_result['total_hours']}")
        
        # Test overtime report
        print(f"\nGenerating overtime report for {employee_id}...")
        overtime_report = overtime_service.get_overtime_report(employee_id, date.today())
        
        print("✅ Overtime Report:")
        print(f"   Employee: {overtime_report['employee_name']}")
        print(f"   Total Pay: ${overtime_report['total_pay']:.2f}")
        print(f"   Overtime Pay: ${overtime_report['overtime_pay']:.2f}")
        print(f"   Rules Applied: {', '.join(overtime_report['rules_applied'])}")
        
    except Exception as e:
        print(f"❌ Error in overtime calculation test: {str(e)}")
    finally:
        db.close()


def test_holiday_management():
    """Test holiday management functionality"""
    print("\n🎉 Testing Holiday Management System...")
    
    db = SessionLocal()
    holiday_service = HolidayService(db)
    
    try:
        # Test holiday eligibility report
        week_start = date.today() - timedelta(days=date.today().weekday())
        
        print(f"\nChecking holiday eligibility for week starting {week_start}")
        
        eligibility_report = holiday_service.get_holiday_eligibility_report(week_start)
        
        print("✅ Holiday Eligibility Report:")
        print(f"   Total Employees: {eligibility_report['total_employees']}")
        print(f"   Eligible Employees: {eligibility_report['eligible_employees']}")
        print(f"   Allocated Holidays: {eligibility_report['allocated_holidays']}")
        
        # Show employee details
        print("\nEmployee Details:")
        for emp in eligibility_report['employee_details'][:3]:  # Show first 3
            print(f"   {emp['employee_name']}: {emp['shifts_worked']} shifts, "
                  f"Eligible: {emp['is_eligible']}, Allocated: {emp['holiday_allocated']}")
        
        # Test holiday allocation
        print(f"\nAllocating paid holidays for week starting {week_start}")
        
        allocation_result = holiday_service.allocate_paid_holidays(week_start)
        
        print("✅ Holiday Allocation Results:")
        print(f"   Total Allocations: {allocation_result['total_allocations']}")
        print(f"   Employees Checked: {allocation_result['total_employees_checked']}")
        
        if allocation_result['allocations']:
            print("\nAllocations Made:")
            for allocation in allocation_result['allocations'][:3]:  # Show first 3
                print(f"   {allocation['employee_name']}: {allocation['holiday_hours']} hours")
        
    except Exception as e:
        print(f"❌ Error in holiday management test: {str(e)}")
    finally:
        db.close()


def test_timesheet_generation():
    """Test timesheet generation functionality"""
    print("\n📋 Testing Timesheet Generation...")
    
    db = SessionLocal()
    time_service = TimeTrackingService(db)
    
    try:
        # Test timesheet generation for a week
        week_start = date.today() - timedelta(days=date.today().weekday())
        employee_id = "EMP001"
        
        print(f"\nGenerating timesheet for employee {employee_id} for week starting {week_start}")
        
        timesheet_data = time_service.get_employee_timesheet(employee_id, week_start)
        
        print("✅ Timesheet Results:")
        print(f"   Total Hours: {timesheet_data['total_hours']}")
        print(f"   Regular Hours: {timesheet_data['regular_hours']}")
        print(f"   Overtime 1.5x: {timesheet_data['overtime_hours_1_5x']}")
        print(f"   Overtime 2.0x: {timesheet_data['overtime_hours_2_0x']}")
        print(f"   Overtime 1.6x: {timesheet_data['overtime_hours_1_6x']}")
        print(f"   Holiday Eligible: {timesheet_data['holiday_eligible']}")
        
        # Show daily breakdown
        if timesheet_data['daily_hours']:
            print("\nDaily Hours Breakdown:")
            for work_date, hours in timesheet_data['daily_hours'].items():
                print(f"   {work_date.strftime('%A, %Y-%m-%d')}: {hours:.2f} hours")
        
    except Exception as e:
        print(f"❌ Error in timesheet generation test: {str(e)}")
    finally:
        db.close()


def test_compliance_features():
    """Test compliance and reporting features"""
    print("\n📊 Testing Compliance & Reporting Features...")
    
    db = SessionLocal()
    
    try:
        from app.database.models import Employee, MissedPunchAlert, OvertimeViolation
        from sqlalchemy import func
        
        # Test employee count
        total_employees = db.query(Employee).filter(Employee.status == "active").count()
        print(f"✅ Active Employees: {total_employees}")
        
        # Test missed punch alerts
        today = date.today()
        missed_punches = db.query(MissedPunchAlert).filter(
            MissedPunchAlert.alert_date == today,
            MissedPunchAlert.resolved == False
        ).count()
        print(f"✅ Unresolved Missed Punches Today: {missed_punches}")
        
        # Test overtime violations
        overtime_violations = db.query(OvertimeViolation).filter(
            OvertimeViolation.violation_date == today,
            OvertimeViolation.resolved == False
        ).count()
        print(f"✅ Unresolved Overtime Violations Today: {overtime_violations}")
        
        # Test work schedules
        schedules = db.query(WorkSchedule).filter(WorkSchedule.is_active == True).count()
        print(f"✅ Active Work Schedules: {schedules}")
        
        # Test overtime configurations
        overtime_configs = db.query(OvertimeConfig).filter(OvertimeConfig.is_active == True).count()
        print(f"✅ Active Overtime Configurations: {overtime_configs}")
        
        # Test holiday configurations
        holidays = db.query(HolidayConfig).filter(HolidayConfig.is_active == True).count()
        print(f"✅ Active Holiday Configurations: {holidays}")
        
    except Exception as e:
        print(f"❌ Error in compliance features test: {str(e)}")
    finally:
        db.close()


def main():
    """Run all tests"""
    print("🚀 California Retail Time & Attendance System - Test Suite")
    print("=" * 60)
    
    # Run all tests
    test_time_tracking()
    test_overtime_calculation()
    test_holiday_management()
    test_timesheet_generation()
    test_compliance_features()
    
    print("\n" + "=" * 60)
    print("🎉 All tests completed!")
    print("\nNext steps:")
    print("1. Access the API documentation at http://localhost:8000/docs")
    print("2. Test the endpoints with the sample data")
    print("3. Explore the compliance reporting features")
    print("4. Configure additional overtime rules and holidays as needed")


if __name__ == "__main__":
    main()