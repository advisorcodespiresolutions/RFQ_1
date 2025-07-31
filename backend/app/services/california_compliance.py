from datetime import datetime, date, timedelta, time
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
import pytz
from ..models.time_attendance import (
    TimeEntry, Employee, OvertimeCalculation, OvertimeType,
    Schedule, PaidHoliday, ComplianceAudit, MissedPunchAlert
)
from ..schemas.time_attendance import OvertimeCalculationCreate

class CaliforniaComplianceEngine:
    """
    California Labor Law Compliance Engine
    Implements California Labor Code §510, §554, and AB 1522 requirements
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.ca_timezone = pytz.timezone('US/Pacific')
        
    def calculate_daily_overtime(self, employee_id: int, work_date: date) -> List[OvertimeCalculationCreate]:
        """
        Calculate California daily overtime rules:
        - >8 hours/day = time-and-a-half (1.5x)
        - >12 hours/day = double time (2.0x)
        - 7th consecutive day = double time beyond 8 hours
        """
        calculations = []
        
        # Get employee info
        employee = self.db.query(Employee).filter(Employee.id == employee_id).first()
        if not employee:
            return calculations
            
        # Get all time entries for the day
        start_of_day = datetime.combine(work_date, time.min)
        end_of_day = datetime.combine(work_date, time.max)
        
        time_entries = self.db.query(TimeEntry).filter(
            and_(
                TimeEntry.employee_id == employee_id,
                TimeEntry.punch_time >= start_of_day,
                TimeEntry.punch_time <= end_of_day,
                TimeEntry.status.in_(['approved', 'pending'])
            )
        ).order_by(TimeEntry.punch_time).all()
        
        if not time_entries:
            return calculations
            
        # Calculate total hours worked
        total_hours = self._calculate_hours_from_entries(time_entries)
        
        if total_hours <= 8:
            return calculations
            
        # Calculate overtime hours
        overtime_8h = min(total_hours - 8, 4)  # Hours 8-12
        overtime_12h = max(0, total_hours - 12)  # Hours beyond 12
        
        # Check if this is 7th consecutive day
        is_seventh_day = self._is_seventh_consecutive_day(employee_id, work_date)
        
        if overtime_8h > 0:
            # Regular daily overtime (8-12 hours)
            if is_seventh_day:
                # 7th consecutive day: double time for all hours beyond 8
                rate = 2.0
                overtime_type = OvertimeType.SEVENTH_DAY
            else:
                rate = 1.5
                overtime_type = OvertimeType.DAILY_8H
                
            calculations.append(OvertimeCalculationCreate(
                employee_id=employee_id,
                date=work_date,
                overtime_type=overtime_type,
                hours_worked=total_hours,
                overtime_hours=overtime_8h,
                overtime_rate=rate,
                base_hourly_rate=employee.hourly_rate,
                overtime_pay=overtime_8h * employee.hourly_rate * rate,
                calculation_details={
                    "rule": "California daily overtime",
                    "hours_8_12": overtime_8h,
                    "is_seventh_day": is_seventh_day
                }
            ))
            
        if overtime_12h > 0:
            # Double time for hours beyond 12
            calculations.append(OvertimeCalculationCreate(
                employee_id=employee_id,
                date=work_date,
                overtime_type=OvertimeType.DAILY_12H,
                hours_worked=total_hours,
                overtime_hours=overtime_12h,
                overtime_rate=2.0,
                base_hourly_rate=employee.hourly_rate,
                overtime_pay=overtime_12h * employee.hourly_rate * 2.0,
                calculation_details={
                    "rule": "California double time",
                    "hours_beyond_12": overtime_12h
                }
            ))
            
        return calculations
        
    def calculate_sixteen_plus_overtime(self, employee_id: int, work_date: date) -> Optional[OvertimeCalculationCreate]:
        """
        Calculate special 16+ hour rule:
        For hours worked beyond 16 hours in a single shift, pay 1.6x of base hourly wage
        """
        employee = self.db.query(Employee).filter(Employee.id == employee_id).first()
        if not employee:
            return None
            
        # Get total hours for the day
        start_of_day = datetime.combine(work_date, time.min)
        end_of_day = datetime.combine(work_date, time.max)
        
        time_entries = self.db.query(TimeEntry).filter(
            and_(
                TimeEntry.employee_id == employee_id,
                TimeEntry.punch_time >= start_of_day,
                TimeEntry.punch_time <= end_of_day,
                TimeEntry.status.in_(['approved', 'pending'])
            )
        ).order_by(TimeEntry.punch_time).all()
        
        total_hours = self._calculate_hours_from_entries(time_entries)
        
        if total_hours <= 16:
            return None
            
        overtime_16h = total_hours - 16
        
        return OvertimeCalculationCreate(
            employee_id=employee_id,
            date=work_date,
            overtime_type=OvertimeType.SIXTEEN_PLUS,
            hours_worked=total_hours,
            overtime_hours=overtime_16h,
            overtime_rate=1.6,
            base_hourly_rate=employee.hourly_rate,
            overtime_pay=overtime_16h * employee.hourly_rate * 1.6,
            calculation_details={
                "rule": "16+ hour special rule",
                "hours_beyond_16": overtime_16h
            }
        )
        
    def calculate_weekly_overtime(self, employee_id: int, week_start: date) -> List[OvertimeCalculationCreate]:
        """
        Calculate weekly overtime (>40 hours/week)
        """
        calculations = []
        employee = self.db.query(Employee).filter(Employee.id == employee_id).first()
        if not employee:
            return calculations
            
        week_end = week_start + timedelta(days=6)
        
        # Get total hours for the week
        start_of_week = datetime.combine(week_start, time.min)
        end_of_week = datetime.combine(week_end, time.max)
        
        time_entries = self.db.query(TimeEntry).filter(
            and_(
                TimeEntry.employee_id == employee_id,
                TimeEntry.punch_time >= start_of_week,
                TimeEntry.punch_time <= end_of_week,
                TimeEntry.status.in_(['approved', 'pending'])
            )
        ).order_by(TimeEntry.punch_time).all()
        
        total_weekly_hours = self._calculate_hours_from_entries(time_entries)
        
        if total_weekly_hours <= 40:
            return calculations
            
        overtime_weekly = total_weekly_hours - 40
        
        calculations.append(OvertimeCalculationCreate(
            employee_id=employee_id,
            date=week_start,
            overtime_type=OvertimeType.WEEKLY_40H,
            hours_worked=total_weekly_hours,
            overtime_hours=overtime_weekly,
            overtime_rate=1.5,
            base_hourly_rate=employee.hourly_rate,
            overtime_pay=overtime_weekly * employee.hourly_rate * 1.5,
            calculation_details={
                "rule": "California weekly overtime",
                "weekly_hours": total_weekly_hours,
                "overtime_hours": overtime_weekly
            }
        ))
        
        return calculations
        
    def check_grace_period_compliance(self, time_entry: TimeEntry, schedule: Optional[Schedule] = None) -> Dict[str, Any]:
        """
        Check if time entry is within 5-minute grace period
        """
        if not schedule:
            return {"within_grace": True, "violation": False}
            
        expected_time = None
        if time_entry.punch_type.value == "clock_in":
            expected_time = schedule.start_time
        elif time_entry.punch_type.value == "clock_out":
            expected_time = schedule.end_time
            
        if not expected_time:
            return {"within_grace": True, "violation": False}
            
        # Convert to datetime for comparison
        expected_datetime = datetime.combine(schedule.date, expected_time)
        time_diff = abs((time_entry.punch_time - expected_datetime).total_seconds() / 60)
        
        within_grace = time_diff <= 5
        violation = time_diff > 5
        
        return {
            "within_grace": within_grace,
            "violation": violation,
            "minutes_off": time_diff,
            "expected_time": expected_datetime,
            "actual_time": time_entry.punch_time
        }
        
    def check_geofence_compliance(self, time_entry: TimeEntry, location_id: int) -> Dict[str, Any]:
        """
        Check if time entry is within geofence boundaries
        """
        location = self.db.query(Location).filter(Location.id == location_id).first()
        if not location or not location.latitude or not location.longitude:
            return {"within_geofence": True, "violation": False}
            
        if not time_entry.latitude or not time_entry.longitude:
            return {"within_geofence": False, "violation": True, "reason": "No GPS coordinates"}
            
        # Calculate distance using Haversine formula
        distance = self._calculate_distance(
            location.latitude, location.longitude,
            time_entry.latitude, time_entry.longitude
        )
        
        within_geofence = distance <= location.geofence_radius
        violation = distance > location.geofence_radius
        
        return {
            "within_geofence": within_geofence,
            "violation": violation,
            "distance_meters": distance,
            "geofence_radius": location.geofence_radius,
            "location_name": location.name
        }
        
    def allocate_paid_holidays(self, week_start: date) -> Dict[str, Any]:
        """
        Automatically allocate 1 paid holiday/week for employees who worked 4+ shifts
        """
        week_end = week_start + timedelta(days=6)
        holidays_allocated = []
        eligible_count = 0
        ineligible_count = 0
        
        # Get all active employees
        employees = self.db.query(Employee).filter(Employee.is_active == True).all()
        
        for employee in employees:
            # Count shifts worked in the week
            shifts_worked = self._count_shifts_in_week(employee.id, week_start, week_end)
            
            if shifts_worked >= 4:
                # Check if holiday already allocated
                existing_holiday = self.db.query(PaidHoliday).filter(
                    and_(
                        PaidHoliday.employee_id == employee.id,
                        PaidHoliday.date >= week_start,
                        PaidHoliday.date <= week_end
                    )
                ).first()
                
                if not existing_holiday:
                    # Allocate holiday
                    holiday = PaidHoliday(
                        employee_id=employee.id,
                        date=week_start + timedelta(days=5),  # Friday
                        hours_paid=8.0,
                        is_auto_allocated=True,
                        notes="Auto-allocated for working 4+ shifts"
                    )
                    self.db.add(holiday)
                    holidays_allocated.append(holiday)
                    eligible_count += 1
                else:
                    eligible_count += 1
            else:
                ineligible_count += 1
                
        self.db.commit()
        
        return {
            "holidays_allocated": holidays_allocated,
            "eligible_count": eligible_count,
            "ineligible_count": ineligible_count,
            "week_start": week_start,
            "week_end": week_end
        }
        
    def create_compliance_audit(self, employee_id: int, violation_type: str, 
                              description: str, severity: str = "medium") -> ComplianceAudit:
        """
        Create compliance audit record for violations
        """
        audit = ComplianceAudit(
            employee_id=employee_id,
            audit_date=date.today(),
            violation_type=violation_type,
            description=description,
            severity=severity
        )
        self.db.add(audit)
        self.db.commit()
        return audit
        
    def generate_compliance_report(self, start_date: date, end_date: date) -> Dict[str, Any]:
        """
        Generate comprehensive compliance report for California audits
        """
        # Get all time entries in date range
        start_datetime = datetime.combine(start_date, time.min)
        end_datetime = datetime.combine(end_date, time.max)
        
        time_entries = self.db.query(TimeEntry).filter(
            and_(
                TimeEntry.punch_time >= start_datetime,
                TimeEntry.punch_time <= end_datetime
            )
        ).all()
        
        # Get all overtime calculations
        overtime_calculations = self.db.query(OvertimeCalculation).filter(
            and_(
                OvertimeCalculation.date >= start_date,
                OvertimeCalculation.date <= end_date
            )
        ).all()
        
        # Get all compliance audits
        compliance_audits = self.db.query(ComplianceAudit).filter(
            and_(
                ComplianceAudit.audit_date >= start_date,
                ComplianceAudit.audit_date <= end_date
            )
        ).all()
        
        return {
            "report_period": {
                "start_date": start_date,
                "end_date": end_date
            },
            "summary": {
                "total_time_entries": len(time_entries),
                "total_overtime_calculations": len(overtime_calculations),
                "total_compliance_violations": len(compliance_audits),
                "resolved_violations": len([a for a in compliance_audits if a.resolved]),
                "unresolved_violations": len([a for a in compliance_audits if not a.resolved])
            },
            "overtime_breakdown": self._summarize_overtime_by_type(overtime_calculations),
            "violations_by_type": self._summarize_violations_by_type(compliance_audits),
            "compliance_score": self._calculate_compliance_score(compliance_audits)
        }
        
    # Helper methods
    def _calculate_hours_from_entries(self, time_entries: List[TimeEntry]) -> float:
        """Calculate total hours worked from time entries"""
        total_hours = 0.0
        clock_in_time = None
        
        for entry in time_entries:
            if entry.punch_type.value == "clock_in":
                clock_in_time = entry.punch_time
            elif entry.punch_type.value == "clock_out" and clock_in_time:
                duration = (entry.punch_time - clock_in_time).total_seconds() / 3600
                total_hours += duration
                clock_in_time = None
                
        return total_hours
        
    def _is_seventh_consecutive_day(self, employee_id: int, work_date: date) -> bool:
        """Check if this is the 7th consecutive day of work"""
        consecutive_days = 0
        current_date = work_date
        
        while consecutive_days < 7:
            # Check if employee worked on this date
            start_of_day = datetime.combine(current_date, time.min)
            end_of_day = datetime.combine(current_date, time.max)
            
            time_entries = self.db.query(TimeEntry).filter(
                and_(
                    TimeEntry.employee_id == employee_id,
                    TimeEntry.punch_time >= start_of_day,
                    TimeEntry.punch_time <= end_of_day,
                    TimeEntry.status.in_(['approved', 'pending'])
                )
            ).first()
            
            if time_entries:
                consecutive_days += 1
                current_date -= timedelta(days=1)
            else:
                break
                
        return consecutive_days >= 7
        
    def _count_shifts_in_week(self, employee_id: int, week_start: date, week_end: date) -> int:
        """Count number of shifts worked in a week"""
        start_datetime = datetime.combine(week_start, time.min)
        end_datetime = datetime.combine(week_end, time.max)
        
        # Get unique days with clock-ins
        clock_in_days = self.db.query(func.date(TimeEntry.punch_time)).filter(
            and_(
                TimeEntry.employee_id == employee_id,
                TimeEntry.punch_time >= start_datetime,
                TimeEntry.punch_time <= end_datetime,
                TimeEntry.punch_type == "clock_in",
                TimeEntry.status.in_(['approved', 'pending'])
            )
        ).distinct().count()
        
        return clock_in_days
        
    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two GPS coordinates using Haversine formula"""
        from math import radians, cos, sin, asin, sqrt
        
        # Convert to radians
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        
        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        r = 6371000  # Radius of earth in meters
        return c * r
        
    def _summarize_overtime_by_type(self, calculations: List[OvertimeCalculation]) -> Dict[str, float]:
        """Summarize overtime hours by type"""
        summary = {}
        for calc in calculations:
            ot_type = calc.overtime_type.value
            if ot_type not in summary:
                summary[ot_type] = 0
            summary[ot_type] += calc.overtime_hours
        return summary
        
    def _summarize_violations_by_type(self, audits: List[ComplianceAudit]) -> Dict[str, int]:
        """Summarize violations by type"""
        summary = {}
        for audit in audits:
            if audit.violation_type not in summary:
                summary[audit.violation_type] = 0
            summary[audit.violation_type] += 1
        return summary
        
    def _calculate_compliance_score(self, audits: List[ComplianceAudit]) -> float:
        """Calculate overall compliance score (0-100)"""
        if not audits:
            return 100.0
            
        resolved = len([a for a in audits if a.resolved])
        total = len(audits)
        
        # Weight by severity
        severity_weights = {"low": 1, "medium": 2, "high": 3, "critical": 4}
        weighted_violations = sum(severity_weights.get(a.severity, 1) for a in audits if not a.resolved)
        
        # Base score from resolved violations
        base_score = (resolved / total) * 100 if total > 0 else 100
        
        # Penalty for unresolved violations
        penalty = min(weighted_violations * 5, 50)  # Max 50 point penalty
        
        return max(0, base_score - penalty)