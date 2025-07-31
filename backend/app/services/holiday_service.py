from datetime import date, timedelta
from typing import Dict, List, Optional
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
import logging

from app.database.models import Employee, TimeEntry, HolidayConfig, HolidayOverride, Timesheet
from app.schemas.time_attendance import HolidayType

logger = logging.getLogger(__name__)


class HolidayService:
    def __init__(self, db: Session):
        self.db = db

    def allocate_paid_holidays(self, week_start_date: date) -> Dict:
        """
        Allocate paid holidays for a specific week based on eligibility criteria
        Returns summary of allocations made
        """
        try:
            week_end_date = week_start_date + timedelta(days=6)
            allocations = []
            total_allocated = 0
            
            # Get all active employees
            employees = self.db.query(Employee).filter(Employee.status == "active").all()
            
            for employee in employees:
                # Check eligibility for paid holiday
                if self._is_holiday_eligible(employee.employee_id, week_start_date):
                    # Check if holiday already allocated
                    existing_holiday = self._get_existing_holiday_allocation(
                        employee.employee_id, week_start_date
                    )
                    
                    if not existing_holiday:
                        # Allocate 8 hours of paid holiday
                        holiday_hours = Decimal('8.0')
                        
                        # Create or update timesheet with holiday hours
                        timesheet = self._get_or_create_timesheet(
                            employee.employee_id, week_start_date, week_end_date
                        )
                        
                        timesheet.paid_holiday_hours = holiday_hours
                        timesheet.total_hours += holiday_hours
                        
                        self.db.commit()
                        
                        allocations.append({
                            "employee_id": employee.employee_id,
                            "employee_name": f"{employee.first_name} {employee.last_name}",
                            "holiday_hours": holiday_hours,
                            "week_start": week_start_date,
                            "week_end": week_end_date
                        })
                        
                        total_allocated += 1
                        
                        logger.info(f"Allocated {holiday_hours} hours paid holiday for employee {employee.employee_id}")
                    else:
                        logger.info(f"Holiday already allocated for employee {employee.employee_id}")
                else:
                    logger.info(f"Employee {employee.employee_id} not eligible for paid holiday")
            
            return {
                "week_start_date": week_start_date,
                "week_end_date": week_end_date,
                "total_employees_checked": len(employees),
                "total_allocations": total_allocated,
                "allocations": allocations
            }
            
        except Exception as e:
            logger.error(f"Error allocating paid holidays: {str(e)}")
            self.db.rollback()
            raise

    def _is_holiday_eligible(self, employee_id: str, week_start_date: date) -> bool:
        """
        Check if employee is eligible for paid holiday
        Criteria: Must work minimum 4 shifts in the week
        """
        week_end_date = week_start_date + timedelta(days=6)
        
        # Count clock-in entries for the week
        shifts_worked = self.db.query(TimeEntry).filter(
            TimeEntry.employee_id == employee_id,
            TimeEntry.punch_type == "clock_in",
            func.date(TimeEntry.punch_time) >= week_start_date,
            func.date(TimeEntry.punch_time) <= week_end_date
        ).count()
        
        return shifts_worked >= 4

    def _get_existing_holiday_allocation(self, employee_id: str, week_start_date: date) -> Optional[Timesheet]:
        """Check if holiday hours are already allocated for the week"""
        week_end_date = week_start_date + timedelta(days=6)
        
        return self.db.query(Timesheet).filter(
            Timesheet.employee_id == employee_id,
            Timesheet.week_start_date == week_start_date,
            Timesheet.week_end_date == week_end_date,
            Timesheet.paid_holiday_hours > 0
        ).first()

    def _get_or_create_timesheet(self, employee_id: str, week_start_date: date, week_end_date: date) -> Timesheet:
        """Get existing timesheet or create new one for the week"""
        timesheet = self.db.query(Timesheet).filter(
            Timesheet.employee_id == employee_id,
            Timesheet.week_start_date == week_start_date,
            Timesheet.week_end_date == week_end_date
        ).first()
        
        if not timesheet:
            timesheet = Timesheet(
                employee_id=employee_id,
                week_start_date=week_start_date,
                week_end_date=week_end_date,
                total_hours=Decimal('0'),
                regular_hours=Decimal('0'),
                overtime_hours_1_5x=Decimal('0'),
                overtime_hours_2_0x=Decimal('0'),
                overtime_hours_1_6x=Decimal('0'),
                paid_holiday_hours=Decimal('0'),
                status="pending"
            )
            self.db.add(timesheet)
            self.db.commit()
            self.db.refresh(timesheet)
        
        return timesheet

    def create_holiday_override(self, override_request: Dict) -> Dict:
        """
        Create a holiday override for special cases
        """
        try:
            override = HolidayOverride(
                employee_id=override_request["employee_id"],
                week_start_date=override_request["week_start_date"],
                holiday_hours=override_request["holiday_hours"],
                reason=override_request["reason"],
                approved_by=override_request["approved_by"]
            )
            
            self.db.add(override)
            self.db.commit()
            self.db.refresh(override)
            
            # Update timesheet with override hours
            week_end_date = override_request["week_start_date"] + timedelta(days=6)
            timesheet = self._get_or_create_timesheet(
                override_request["employee_id"],
                override_request["week_start_date"],
                week_end_date
            )
            
            timesheet.paid_holiday_hours = override_request["holiday_hours"]
            timesheet.total_hours += override_request["holiday_hours"]
            
            self.db.commit()
            
            return {
                "success": True,
                "message": "Holiday override created successfully",
                "override_id": override.id
            }
            
        except Exception as e:
            logger.error(f"Error creating holiday override: {str(e)}")
            self.db.rollback()
            return {
                "success": False,
                "message": f"Error creating holiday override: {str(e)}"
            }

    def get_holiday_eligibility_report(self, week_start_date: date) -> Dict:
        """
        Generate report of holiday eligibility for all employees
        """
        week_end_date = week_start_date + timedelta(days=6)
        employees = self.db.query(Employee).filter(Employee.status == "active").all()
        
        eligibility_report = []
        
        for employee in employees:
            # Check eligibility
            is_eligible = self._is_holiday_eligible(employee.employee_id, week_start_date)
            
            # Count shifts worked
            shifts_worked = self.db.query(TimeEntry).filter(
                TimeEntry.employee_id == employee.employee_id,
                TimeEntry.punch_type == "clock_in",
                func.date(TimeEntry.punch_time) >= week_start_date,
                func.date(TimeEntry.punch_time) <= week_end_date
            ).count()
            
            # Check if holiday already allocated
            existing_holiday = self._get_existing_holiday_allocation(
                employee.employee_id, week_start_date
            )
            
            eligibility_report.append({
                "employee_id": employee.employee_id,
                "employee_name": f"{employee.first_name} {employee.last_name}",
                "department": employee.department,
                "shifts_worked": shifts_worked,
                "is_eligible": is_eligible,
                "holiday_allocated": existing_holiday is not None,
                "holiday_hours": existing_holiday.paid_holiday_hours if existing_holiday else Decimal('0'),
                "eligibility_threshold": 4
            })
        
        return {
            "week_start_date": week_start_date,
            "week_end_date": week_end_date,
            "total_employees": len(employees),
            "eligible_employees": sum(1 for e in eligibility_report if e["is_eligible"]),
            "allocated_holidays": sum(1 for e in eligibility_report if e["holiday_allocated"]),
            "employee_details": eligibility_report
        }

    def get_holiday_configurations(self, year: Optional[int] = None) -> List[Dict]:
        """
        Get holiday configurations for the system
        """
        query = self.db.query(HolidayConfig).filter(HolidayConfig.is_active == True)
        
        if year:
            query = query.filter(func.extract('year', HolidayConfig.date) == year)
        
        holidays = query.order_by(HolidayConfig.date).all()
        
        return [
            {
                "id": holiday.id,
                "holiday_name": holiday.holiday_name,
                "holiday_type": holiday.holiday_type,
                "date": holiday.date,
                "description": holiday.description,
                "is_active": holiday.is_active
            }
            for holiday in holidays
        ]

    def create_holiday_configuration(self, holiday_data: Dict) -> Dict:
        """
        Create a new holiday configuration
        """
        try:
            holiday = HolidayConfig(
                holiday_name=holiday_data["holiday_name"],
                holiday_type=holiday_data["holiday_type"],
                date=holiday_data["date"],
                description=holiday_data.get("description"),
                is_active=holiday_data.get("is_active", True)
            )
            
            self.db.add(holiday)
            self.db.commit()
            self.db.refresh(holiday)
            
            return {
                "success": True,
                "message": "Holiday configuration created successfully",
                "holiday_id": holiday.id
            }
            
        except Exception as e:
            logger.error(f"Error creating holiday configuration: {str(e)}")
            self.db.rollback()
            return {
                "success": False,
                "message": f"Error creating holiday configuration: {str(e)}"
            }

    def get_holiday_overrides(self, employee_id: Optional[str] = None, 
                            start_date: Optional[date] = None, 
                            end_date: Optional[date] = None) -> List[Dict]:
        """
        Get holiday overrides with optional filtering
        """
        query = self.db.query(HolidayOverride)
        
        if employee_id:
            query = query.filter(HolidayOverride.employee_id == employee_id)
        
        if start_date:
            query = query.filter(HolidayOverride.week_start_date >= start_date)
        
        if end_date:
            query = query.filter(HolidayOverride.week_start_date <= end_date)
        
        overrides = query.order_by(HolidayOverride.week_start_date.desc()).all()
        
        return [
            {
                "id": override.id,
                "employee_id": override.employee_id,
                "week_start_date": override.week_start_date,
                "holiday_hours": override.holiday_hours,
                "reason": override.reason,
                "approved_by": override.approved_by,
                "created_at": override.created_at
            }
            for override in overrides
        ]

    def calculate_holiday_pay(self, employee_id: str, week_start_date: date) -> Dict:
        """
        Calculate holiday pay for an employee for a specific week
        """
        try:
            # Get employee info
            employee = self.db.query(Employee).filter(Employee.employee_id == employee_id).first()
            if not employee:
                raise ValueError("Employee not found")
            
            # Get timesheet for the week
            week_end_date = week_start_date + timedelta(days=6)
            timesheet = self.db.query(Timesheet).filter(
                Timesheet.employee_id == employee_id,
                Timesheet.week_start_date == week_start_date,
                Timesheet.week_end_date == week_end_date
            ).first()
            
            if not timesheet:
                return {
                    "employee_id": employee_id,
                    "week_start_date": week_start_date,
                    "holiday_hours": Decimal('0'),
                    "holiday_pay": Decimal('0'),
                    "hourly_rate": employee.hourly_rate,
                    "is_eligible": False
                }
            
            # Calculate holiday pay
            holiday_pay = timesheet.paid_holiday_hours * employee.hourly_rate
            
            return {
                "employee_id": employee_id,
                "employee_name": f"{employee.first_name} {employee.last_name}",
                "week_start_date": week_start_date,
                "holiday_hours": timesheet.paid_holiday_hours,
                "holiday_pay": holiday_pay,
                "hourly_rate": employee.hourly_rate,
                "is_eligible": timesheet.paid_holiday_hours > 0
            }
            
        except Exception as e:
            logger.error(f"Error calculating holiday pay: {str(e)}")
            raise

    def get_holiday_summary_report(self, start_date: date, end_date: date, 
                                 department: Optional[str] = None) -> Dict:
        """
        Generate summary report of holiday allocations and pay
        """
        query = self.db.query(Employee)
        if department:
            query = query.filter(Employee.department == department)
        
        employees = query.all()
        
        total_holiday_hours = Decimal('0')
        total_holiday_pay = Decimal('0')
        employee_reports = []
        
        current_date = start_date
        while current_date <= end_date:
            week_start = current_date - timedelta(days=current_date.weekday())
            week_end = week_start + timedelta(days=6)
            
            for employee in employees:
                try:
                    holiday_calculation = self.calculate_holiday_pay(
                        employee.employee_id, week_start
                    )
                    
                    if holiday_calculation["is_eligible"]:
                        total_holiday_hours += holiday_calculation["holiday_hours"]
                        total_holiday_pay += holiday_calculation["holiday_pay"]
                        
                        employee_reports.append({
                            "employee_id": employee.employee_id,
                            "employee_name": holiday_calculation["employee_name"],
                            "department": employee.department,
                            "week_start": week_start,
                            "holiday_hours": holiday_calculation["holiday_hours"],
                            "holiday_pay": holiday_calculation["holiday_pay"]
                        })
                        
                except Exception as e:
                    logger.error(f"Error calculating holiday pay for employee {employee.employee_id}: {str(e)}")
                    continue
            
            current_date += timedelta(days=7)
        
        return {
            "period_start": start_date,
            "period_end": end_date,
            "department": department,
            "total_employees": len(employees),
            "total_holiday_hours": total_holiday_hours,
            "total_holiday_pay": total_holiday_pay,
            "employee_reports": employee_reports
        }