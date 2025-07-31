from datetime import datetime, time, date, timedelta
from typing import List, Dict, Optional, Tuple
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
import logging

from app.database.models import Employee, TimeEntry, WorkSchedule, OvertimeConfig, MissedPunchAlert
from app.schemas.time_attendance import PunchType, TimeEntryStatus, PunchRequest, PunchResponse

logger = logging.getLogger(__name__)


class TimeTrackingService:
    def __init__(self, db: Session):
        self.db = db
        self.grace_period_minutes = 5

    def process_punch(self, punch_request: PunchRequest) -> PunchResponse:
        """
        Process a time punch (clock in/out) with grace period validation
        """
        try:
            # Validate employee exists and is active
            employee = self.db.query(Employee).filter(
                Employee.employee_id == punch_request.employee_id,
                Employee.status == "active"
            ).first()
            
            if not employee:
                return PunchResponse(
                    success=False,
                    message="Employee not found or inactive"
                )

            # Check for duplicate punches
            if self._has_duplicate_punch(punch_request):
                return PunchResponse(
                    success=False,
                    message="Duplicate punch detected"
                )

            # Validate punch sequence
            if not self._validate_punch_sequence(punch_request):
                return PunchResponse(
                    success=False,
                    message="Invalid punch sequence"
                )

            # Check grace period
            grace_period_used = self._check_grace_period(punch_request)

            # Create time entry
            time_entry = TimeEntry(
                employee_id=punch_request.employee_id,
                punch_type=punch_request.punch_type.value,
                punch_time=datetime.now(),
                location=punch_request.location,
                latitude=punch_request.latitude,
                longitude=punch_request.longitude,
                device_type=punch_request.device_type,
                notes=punch_request.notes,
                status=TimeEntryStatus.PENDING.value
            )

            self.db.add(time_entry)
            self.db.commit()
            self.db.refresh(time_entry)

            # Check for missed punches and create alerts
            self._check_missed_punches(punch_request.employee_id, punch_request.punch_type)

            return PunchResponse(
                success=True,
                message="Punch recorded successfully",
                time_entry=time_entry,
                grace_period_used=grace_period_used
            )

        except Exception as e:
            logger.error(f"Error processing punch: {str(e)}")
            self.db.rollback()
            return PunchResponse(
                success=False,
                message=f"Error processing punch: {str(e)}"
            )

    def _has_duplicate_punch(self, punch_request: PunchRequest) -> bool:
        """Check for duplicate punches within a short time window"""
        recent_punch = self.db.query(TimeEntry).filter(
            TimeEntry.employee_id == punch_request.employee_id,
            TimeEntry.punch_type == punch_request.punch_type.value,
            TimeEntry.punch_time >= datetime.now() - timedelta(minutes=1)
        ).first()
        
        return recent_punch is not None

    def _validate_punch_sequence(self, punch_request: PunchRequest) -> bool:
        """Validate that punch sequence makes sense (e.g., can't clock out if not clocked in)"""
        if punch_request.punch_type == PunchType.CLOCK_IN:
            # Check if already clocked in
            last_punch = self._get_last_punch(punch_request.employee_id)
            if last_punch and last_punch.punch_type in ["clock_in", "break_start"]:
                return False
        elif punch_request.punch_type == PunchType.CLOCK_OUT:
            # Check if clocked in
            last_punch = self._get_last_punch(punch_request.employee_id)
            if not last_punch or last_punch.punch_type not in ["clock_in", "break_end"]:
                return False
        elif punch_request.punch_type == PunchType.BREAK_START:
            # Check if clocked in and not already on break
            last_punch = self._get_last_punch(punch_request.employee_id)
            if not last_punch or last_punch.punch_type not in ["clock_in", "break_end"]:
                return False
        elif punch_request.punch_type == PunchType.BREAK_END:
            # Check if on break
            last_punch = self._get_last_punch(punch_request.employee_id)
            if not last_punch or last_punch.punch_type != "break_start":
                return False

        return True

    def _get_last_punch(self, employee_id: str) -> Optional[TimeEntry]:
        """Get the last punch for an employee"""
        return self.db.query(TimeEntry).filter(
            TimeEntry.employee_id == employee_id
        ).order_by(TimeEntry.punch_time.desc()).first()

    def _check_grace_period(self, punch_request: PunchRequest) -> bool:
        """Check if punch is within grace period of scheduled time"""
        if punch_request.punch_type not in [PunchType.CLOCK_IN, PunchType.CLOCK_OUT]:
            return False

        today = date.today()
        day_of_week = today.weekday()  # 0=Monday, 6=Sunday
        
        # Get scheduled time for today
        schedule = self.db.query(WorkSchedule).filter(
            WorkSchedule.employee_id == punch_request.employee_id,
            WorkSchedule.day_of_week == day_of_week,
            WorkSchedule.is_active == True
        ).first()

        if not schedule:
            return False

        current_time = datetime.now().time()
        scheduled_time = schedule.start_time if punch_request.punch_type == PunchType.CLOCK_IN else schedule.end_time
        
        # Calculate grace period
        grace_start = self._subtract_minutes(scheduled_time, self.grace_period_minutes)
        grace_end = self._add_minutes(scheduled_time, self.grace_period_minutes)
        
        return grace_start <= current_time <= grace_end

    def _subtract_minutes(self, t: time, minutes: int) -> time:
        """Subtract minutes from a time object"""
        total_minutes = t.hour * 60 + t.minute - minutes
        if total_minutes < 0:
            total_minutes += 24 * 60
        return time(hour=total_minutes // 60, minute=total_minutes % 60)

    def _add_minutes(self, t: time, minutes: int) -> time:
        """Add minutes to a time object"""
        total_minutes = t.hour * 60 + t.minute + minutes
        return time(hour=(total_minutes // 60) % 24, minute=total_minutes % 60)

    def _check_missed_punches(self, employee_id: str, current_punch_type: PunchType):
        """Check for missed punches and create alerts"""
        today = date.today()
        
        # Get expected punches for today
        expected_punches = self._get_expected_punches(employee_id, today)
        
        for expected_punch in expected_punches:
            if expected_punch["type"] != current_punch_type.value:
                # Check if this punch was missed
                actual_punch = self.db.query(TimeEntry).filter(
                    TimeEntry.employee_id == employee_id,
                    TimeEntry.punch_type == expected_punch["type"],
                    func.date(TimeEntry.punch_time) == today
                ).first()
                
                if not actual_punch:
                    # Create missed punch alert
                    alert = MissedPunchAlert(
                        employee_id=employee_id,
                        alert_date=today,
                        alert_type=expected_punch["type"],
                        expected_time=expected_punch["time"],
                        grace_period_used=False
                    )
                    self.db.add(alert)

    def _get_expected_punches(self, employee_id: str, punch_date: date) -> List[Dict]:
        """Get expected punches for a given date based on work schedule"""
        day_of_week = punch_date.weekday()
        
        schedule = self.db.query(WorkSchedule).filter(
            WorkSchedule.employee_id == employee_id,
            WorkSchedule.day_of_week == day_of_week,
            WorkSchedule.is_active == True
        ).first()
        
        if not schedule:
            return []
        
        expected_punches = [
            {"type": "clock_in", "time": schedule.start_time},
            {"type": "clock_out", "time": schedule.end_time}
        ]
        
        # Add break punches if break duration > 0
        if schedule.break_duration_minutes > 0:
            break_start = self._add_minutes(schedule.start_time, 4 * 60)  # 4 hours after start
            break_end = self._add_minutes(break_start, schedule.break_duration_minutes)
            expected_punches.extend([
                {"type": "break_start", "time": break_start},
                {"type": "break_end", "time": break_end}
            ])
        
        return expected_punches

    def get_employee_timesheet(self, employee_id: str, week_start_date: date) -> Dict:
        """Get timesheet summary for an employee for a specific week"""
        week_end_date = week_start_date + timedelta(days=6)
        
        # Get all time entries for the week
        time_entries = self.db.query(TimeEntry).filter(
            TimeEntry.employee_id == employee_id,
            func.date(TimeEntry.punch_time) >= week_start_date,
            func.date(TimeEntry.punch_time) <= week_end_date
        ).order_by(TimeEntry.punch_time).all()
        
        # Calculate daily hours
        daily_hours = self._calculate_daily_hours(time_entries)
        
        # Calculate overtime
        overtime_calculation = self._calculate_overtime(daily_hours)
        
        # Calculate holiday eligibility
        holiday_eligible = self._check_holiday_eligibility(employee_id, week_start_date)
        
        return {
            "employee_id": employee_id,
            "week_start_date": week_start_date,
            "week_end_date": week_end_date,
            "daily_hours": daily_hours,
            "overtime": overtime_calculation,
            "holiday_eligible": holiday_eligible,
            "total_hours": sum(daily_hours.values()),
            "regular_hours": overtime_calculation["regular_hours"],
            "overtime_hours_1_5x": overtime_calculation["overtime_1_5x"],
            "overtime_hours_2_0x": overtime_calculation["overtime_2_0x"],
            "overtime_hours_1_6x": overtime_calculation["overtime_1_6x"]
        }

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

    def _calculate_overtime(self, daily_hours: Dict[date, Decimal]) -> Dict:
        """Calculate overtime based on California rules"""
        overtime_1_5x = Decimal('0')
        overtime_2_0x = Decimal('0')
        overtime_1_6x = Decimal('0')
        regular_hours = Decimal('0')
        
        # Get overtime configurations
        overtime_configs = self.db.query(OvertimeConfig).filter(
            OvertimeConfig.is_active == True
        ).all()
        
        for work_date, hours in daily_hours.items():
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
                
                # Special 16-hour rule
                if hours > 16:
                    special_overtime = hours - 16
                    overtime_1_6x += special_overtime
                    # Adjust other overtime rates
                    if special_overtime <= daily_overtime_2_0x:
                        overtime_2_0x -= special_overtime
                    else:
                        remaining = special_overtime - daily_overtime_2_0x
                        overtime_2_0x = Decimal('0')
                        overtime_1_5x -= remaining
        
        return {
            "regular_hours": regular_hours,
            "overtime_1_5x": overtime_1_5x,
            "overtime_2_0x": overtime_2_0x,
            "overtime_1_6x": overtime_1_6x
        }

    def _check_holiday_eligibility(self, employee_id: str, week_start_date: date) -> bool:
        """Check if employee is eligible for paid holiday (4+ shifts in week)"""
        week_end_date = week_start_date + timedelta(days=6)
        
        # Count shifts worked in the week
        shifts_worked = self.db.query(TimeEntry).filter(
            TimeEntry.employee_id == employee_id,
            TimeEntry.punch_type == "clock_in",
            func.date(TimeEntry.punch_time) >= week_start_date,
            func.date(TimeEntry.punch_time) <= week_end_date
        ).count()
        
        return shifts_worked >= 4