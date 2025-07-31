from datetime import date, timedelta
from typing import Dict, List, Optional, Tuple
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
import logging

from app.database.models import TimeEntry, Employee, OvertimeConfig, OvertimeViolation
from app.schemas.time_attendance import OvertimeRule

logger = logging.getLogger(__name__)


class OvertimeService:
    def __init__(self, db: Session):
        self.db = db

    def calculate_overtime_for_period(self, employee_id: str, start_date: date, end_date: date) -> Dict:
        """
        Calculate overtime for an employee for a specific period
        Returns detailed breakdown of regular hours and overtime at different rates
        """
        try:
            # Get all time entries for the period
            time_entries = self.db.query(TimeEntry).filter(
                TimeEntry.employee_id == employee_id,
                func.date(TimeEntry.punch_time) >= start_date,
                func.date(TimeEntry.punch_time) <= end_date
            ).order_by(TimeEntry.punch_time).all()

            # Calculate daily hours
            daily_hours = self._calculate_daily_hours(time_entries)
            
            # Calculate weekly hours
            weekly_hours = self._calculate_weekly_hours(daily_hours)
            
            # Apply California overtime rules
            overtime_result = self._apply_california_overtime_rules(daily_hours, weekly_hours)
            
            # Check for violations and create alerts
            self._check_overtime_violations(employee_id, daily_hours, weekly_hours)
            
            return overtime_result

        except Exception as e:
            logger.error(f"Error calculating overtime for employee {employee_id}: {str(e)}")
            raise

    def _calculate_daily_hours(self, time_entries: List[TimeEntry]) -> Dict[date, Decimal]:
        """Calculate hours worked per day from time entries"""
        daily_hours = {}
        current_date = None
        clock_in_time = None
        break_start_time = None
        
        for entry in time_entries:
            entry_date = entry.punch_time.date()
            
            if entry.punch_type == "clock_in":
                if current_date == entry_date and clock_in_time:
                    # Multiple clock-ins on same day, use the latest
                    clock_in_time = entry.punch_time
                else:
                    clock_in_time = entry.punch_time
                    current_date = entry_date
                    
            elif entry.punch_type == "clock_out" and clock_in_time and current_date == entry_date:
                # Calculate hours for this shift
                shift_hours = (entry.punch_time - clock_in_time).total_seconds() / 3600
                
                # Subtract break time if any
                if break_start_time:
                    break_end_entry = next((e for e in time_entries if e.punch_type == "break_end" and e.punch_time > break_start_time), None)
                    if break_end_entry:
                        break_hours = (break_end_entry.punch_time - break_start_time).total_seconds() / 3600
                        shift_hours -= break_hours
                        break_start_time = None
                
                daily_hours[entry_date] = daily_hours.get(entry_date, 0) + Decimal(str(shift_hours))
                clock_in_time = None
                
            elif entry.punch_type == "break_start":
                break_start_time = entry.punch_time
                
        return daily_hours

    def _calculate_weekly_hours(self, daily_hours: Dict[date, Decimal]) -> Dict[int, Decimal]:
        """Calculate hours worked per week (week number)"""
        weekly_hours = {}
        
        for work_date, hours in daily_hours.items():
            week_number = work_date.isocalendar()[1]  # ISO week number
            weekly_hours[week_number] = weekly_hours.get(week_number, 0) + hours
            
        return weekly_hours

    def _apply_california_overtime_rules(self, daily_hours: Dict[date, Decimal], weekly_hours: Dict[int, Decimal]) -> Dict:
        """
        Apply California overtime rules:
        - >8 hours/day = 1.5x
        - >12 hours/day = 2.0x
        - 7th consecutive day = 2.0x beyond 8 hours
        - >16 hours in single shift = 1.6x (special rule)
        """
        regular_hours = Decimal('0')
        overtime_1_5x = Decimal('0')
        overtime_2_0x = Decimal('0')
        overtime_1_6x = Decimal('0')
        
        # Track consecutive work days for 7th day rule
        consecutive_days = self._get_consecutive_work_days(daily_hours)
        
        for work_date, hours in daily_hours.items():
            is_7th_consecutive_day = consecutive_days.get(work_date, 0) >= 7
            
            if hours <= 8:
                regular_hours += hours
            else:
                regular_hours += Decimal('8')
                
                # Daily overtime rules
                if hours > 8:
                    daily_overtime_1_5x = min(hours - 8, 4)  # Up to 12 hours
                    overtime_1_5x += daily_overtime_1_5x
                    
                if hours > 12:
                    daily_overtime_2_0x = hours - 12
                    overtime_2_0x += daily_overtime_2_0x
                    overtime_1_5x -= daily_overtime_2_0x  # Adjust 1.5x hours
                
                # Special 16-hour rule (highest priority)
                if hours > 16:
                    special_overtime = hours - 16
                    overtime_1_6x += special_overtime
                    
                    # Adjust other overtime rates
                    if special_overtime <= daily_overtime_2_0x:
                        overtime_2_0x -= special_overtime
                    else:
                        remaining = special_overtime - daily_overtime_2_0x
                        overtime_2_0x = Decimal('0')
                        if remaining <= daily_overtime_1_5x:
                            overtime_1_5x -= remaining
                        else:
                            overtime_1_5x = Decimal('0')
                
                # 7th consecutive day rule
                if is_7th_consecutive_day:
                    # All hours beyond 8 on 7th consecutive day are 2.0x
                    seventh_day_overtime = hours - 8
                    overtime_2_0x += seventh_day_overtime
                    
                    # Adjust other overtime rates
                    if seventh_day_overtime <= daily_overtime_1_5x:
                        overtime_1_5x -= seventh_day_overtime
                    else:
                        overtime_1_5x = Decimal('0')
        
        return {
            "regular_hours": regular_hours,
            "overtime_1_5x": overtime_1_5x,
            "overtime_2_0x": overtime_2_0x,
            "overtime_1_6x": overtime_1_6x,
            "total_hours": regular_hours + overtime_1_5x + overtime_2_0x + overtime_1_6x,
            "daily_breakdown": daily_hours,
            "weekly_breakdown": weekly_hours
        }

    def _get_consecutive_work_days(self, daily_hours: Dict[date, Decimal]) -> Dict[date, int]:
        """Calculate consecutive work days for each date"""
        consecutive_days = {}
        sorted_dates = sorted(daily_hours.keys())
        
        for i, work_date in enumerate(sorted_dates):
            consecutive_count = 1
            
            # Look backwards to count consecutive days
            for j in range(i - 1, -1, -1):
                prev_date = sorted_dates[j]
                if (work_date - prev_date).days == 1:
                    consecutive_count += 1
                else:
                    break
                    
            consecutive_days[work_date] = consecutive_count
            
        return consecutive_days

    def _check_overtime_violations(self, employee_id: str, daily_hours: Dict[date, Decimal], weekly_hours: Dict[int, Decimal]):
        """Check for overtime violations and create alerts"""
        for work_date, hours in daily_hours.items():
            # Check daily overtime violations
            if hours > 8:
                self._create_overtime_violation(
                    employee_id, work_date, "daily_8_hours", hours, 8, hours - 8, Decimal('1.5')
                )
                
            if hours > 12:
                self._create_overtime_violation(
                    employee_id, work_date, "daily_12_hours", hours, 12, hours - 12, Decimal('2.0')
                )
                
            if hours > 16:
                self._create_overtime_violation(
                    employee_id, work_date, "shift_16_hours", hours, 16, hours - 16, Decimal('1.6')
                )

    def _create_overtime_violation(self, employee_id: str, violation_date: date, violation_type: str, 
                                 hours_worked: Decimal, threshold_hours: Decimal, overtime_hours: Decimal, 
                                 multiplier: Decimal):
        """Create an overtime violation record"""
        # Check if violation already exists
        existing_violation = self.db.query(OvertimeViolation).filter(
            OvertimeViolation.employee_id == employee_id,
            OvertimeViolation.violation_date == violation_date,
            OvertimeViolation.violation_type == violation_type
        ).first()
        
        if not existing_violation:
            violation = OvertimeViolation(
                employee_id=employee_id,
                violation_date=violation_date,
                violation_type=violation_type,
                hours_worked=hours_worked,
                threshold_hours=threshold_hours,
                overtime_hours=overtime_hours,
                multiplier_applied=multiplier
            )
            self.db.add(violation)
            self.db.commit()

    def get_overtime_report(self, employee_id: str, report_date: date) -> Dict:
        """Generate detailed overtime report for an employee"""
        # Get employee info
        employee = self.db.query(Employee).filter(Employee.employee_id == employee_id).first()
        if not employee:
            raise ValueError("Employee not found")
            
        # Calculate overtime for the week containing the report date
        week_start = report_date - timedelta(days=report_date.weekday())
        week_end = week_start + timedelta(days=6)
        
        overtime_result = self.calculate_overtime_for_period(employee_id, week_start, week_end)
        
        # Calculate total pay
        hourly_rate = employee.hourly_rate
        total_pay = (
            overtime_result["regular_hours"] * hourly_rate +
            overtime_result["overtime_1_5x"] * hourly_rate * Decimal('1.5') +
            overtime_result["overtime_2_0x"] * hourly_rate * Decimal('2.0') +
            overtime_result["overtime_1_6x"] * hourly_rate * Decimal('1.6')
        )
        
        return {
            "employee_id": employee_id,
            "employee_name": f"{employee.first_name} {employee.last_name}",
            "report_date": report_date,
            "week_start": week_start,
            "week_end": week_end,
            "total_hours": overtime_result["total_hours"],
            "regular_hours": overtime_result["regular_hours"],
            "overtime_hours": {
                "1.5x": overtime_result["overtime_1_5x"],
                "2.0x": overtime_result["overtime_2_0x"],
                "1.6x": overtime_result["overtime_1_6x"]
            },
            "overtime_pay": total_pay - (overtime_result["regular_hours"] * hourly_rate),
            "total_pay": total_pay,
            "hourly_rate": hourly_rate,
            "rules_applied": self._get_applied_rules(overtime_result),
            "daily_breakdown": overtime_result["daily_breakdown"]
        }

    def _get_applied_rules(self, overtime_result: Dict) -> List[str]:
        """Get list of overtime rules that were applied"""
        rules = []
        
        if overtime_result["overtime_1_5x"] > 0:
            rules.append("Daily 8+ hours = 1.5x")
        if overtime_result["overtime_2_0x"] > 0:
            rules.append("Daily 12+ hours = 2.0x")
        if overtime_result["overtime_1_6x"] > 0:
            rules.append("Shift 16+ hours = 1.6x")
            
        return rules

    def get_overtime_summary_for_period(self, start_date: date, end_date: date, department: Optional[str] = None) -> Dict:
        """Get overtime summary for all employees or department for a period"""
        query = self.db.query(Employee)
        if department:
            query = query.filter(Employee.department == department)
            
        employees = query.all()
        
        total_regular_hours = Decimal('0')
        total_overtime_1_5x = Decimal('0')
        total_overtime_2_0x = Decimal('0')
        total_overtime_1_6x = Decimal('0')
        total_pay = Decimal('0')
        
        employee_reports = []
        
        for employee in employees:
            try:
                overtime_result = self.calculate_overtime_for_period(
                    employee.employee_id, start_date, end_date
                )
                
                hourly_rate = employee.hourly_rate
                employee_pay = (
                    overtime_result["regular_hours"] * hourly_rate +
                    overtime_result["overtime_1_5x"] * hourly_rate * Decimal('1.5') +
                    overtime_result["overtime_2_0x"] * hourly_rate * Decimal('2.0') +
                    overtime_result["overtime_1_6x"] * hourly_rate * Decimal('1.6')
                )
                
                total_regular_hours += overtime_result["regular_hours"]
                total_overtime_1_5x += overtime_result["overtime_1_5x"]
                total_overtime_2_0x += overtime_result["overtime_2_0x"]
                total_overtime_1_6x += overtime_result["overtime_1_6x"]
                total_pay += employee_pay
                
                employee_reports.append({
                    "employee_id": employee.employee_id,
                    "employee_name": f"{employee.first_name} {employee.last_name}",
                    "department": employee.department,
                    "regular_hours": overtime_result["regular_hours"],
                    "overtime_1_5x": overtime_result["overtime_1_5x"],
                    "overtime_2_0x": overtime_result["overtime_2_0x"],
                    "overtime_1_6x": overtime_result["overtime_1_6x"],
                    "total_pay": employee_pay
                })
                
            except Exception as e:
                logger.error(f"Error calculating overtime for employee {employee.employee_id}: {str(e)}")
                continue
        
        return {
            "period_start": start_date,
            "period_end": end_date,
            "department": department,
            "total_employees": len(employees),
            "total_regular_hours": total_regular_hours,
            "total_overtime_hours": {
                "1.5x": total_overtime_1_5x,
                "2.0x": total_overtime_2_0x,
                "1.6x": total_overtime_1_6x
            },
            "total_pay": total_pay,
            "employee_reports": employee_reports
        }