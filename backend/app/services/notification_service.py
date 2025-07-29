"""
Notification and Alert Service for Quote Journey Tracking
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from enum import Enum
import logging
from sqlalchemy.orm import Session

from app.database.models import Quote, QuoteStatus, User, AuditLog
from app.core.config import settings

logger = logging.getLogger(__name__)


class AlertType(str, Enum):
    """Types of alerts in the system"""
    INFO = "info"
    SUCCESS = "success" 
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertCategory(str, Enum):
    """Categories of alerts"""
    QUOTE_STATUS = "quote_status"
    FILE_PROCESSING = "file_processing"
    AI_ANALYSIS = "ai_analysis"
    APPROVAL = "approval"
    DEADLINE = "deadline"
    SYSTEM = "system"
    QUALITY = "quality"


class QuoteJourneyPhase(str, Enum):
    """Detailed phases in quote journey"""
    # Initial Phase
    CREATED = "created"
    FILES_UPLOADED = "files_uploaded"
    
    # Processing Phase
    FILE_VALIDATION = "file_validation"
    AI_ANALYSIS_QUEUED = "ai_analysis_queued"
    AI_ANALYSIS_PROCESSING = "ai_analysis_processing"
    AI_ANALYSIS_COMPLETED = "ai_analysis_completed"
    
    # Review Phase
    TECHNICAL_REVIEW = "technical_review"
    COST_CALCULATION = "cost_calculation"
    MARGIN_REVIEW = "margin_review"
    
    # Approval Phase
    PENDING_APPROVAL = "pending_approval"
    MANAGER_REVIEW = "manager_review"
    CLIENT_REVIEW = "client_review"
    
    # Final Phase
    APPROVED = "approved"
    REJECTED = "rejected"
    SENT_TO_CLIENT = "sent_to_client"
    CLIENT_FEEDBACK = "client_feedback"
    COMPLETED = "completed"
    
    # Exception Phases
    ON_HOLD = "on_hold"
    REVISION_REQUIRED = "revision_required"
    EXPIRED = "expired"


class NotificationService:
    """Service for managing notifications and alerts"""
    
    def __init__(self, db: Session):
        self.db = db
        self.active_alerts = []
        self.journey_phases = {}  # quote_id -> current phase info
    
    async def create_alert(
        self,
        title: str,
        message: str,
        alert_type: AlertType,
        category: AlertCategory,
        quote_id: Optional[int] = None,
        user_id: Optional[int] = None,
        metadata: Optional[Dict] = None,
        auto_dismiss_after: Optional[int] = None  # seconds
    ) -> Dict[str, Any]:
        """Create a new alert"""
        
        alert = {
            "id": len(self.active_alerts) + 1,
            "title": title,
            "message": message,
            "type": alert_type.value,
            "category": category.value,
            "quote_id": quote_id,
            "user_id": user_id,
            "metadata": metadata or {},
            "created_at": datetime.utcnow().isoformat(),
            "dismissed": False,
            "auto_dismiss_after": auto_dismiss_after,
            "actions": self._get_alert_actions(alert_type, category, quote_id)
        }
        
        self.active_alerts.append(alert)
        
        # Log the alert
        logger.info(f"Alert created: {title} - {message}")
        
        # Auto-dismiss if specified
        if auto_dismiss_after:
            asyncio.create_task(self._auto_dismiss_alert(alert["id"], auto_dismiss_after))
        
        return alert
    
    def _get_alert_actions(self, alert_type: AlertType, category: AlertCategory, quote_id: Optional[int]) -> List[Dict]:
        """Get available actions for an alert"""
        actions = []
        
        if quote_id:
            actions.append({
                "label": "View Quote",
                "action": "navigate",
                "target": f"/quotes/{quote_id}",
                "style": "primary"
            })
        
        if category == AlertCategory.APPROVAL:
            actions.extend([
                {
                    "label": "Approve",
                    "action": "approve_quote",
                    "target": quote_id,
                    "style": "success"
                },
                {
                    "label": "Reject",
                    "action": "reject_quote", 
                    "target": quote_id,
                    "style": "danger"
                }
            ])
        
        if category == AlertCategory.FILE_PROCESSING and alert_type == AlertType.ERROR:
            actions.append({
                "label": "Retry Processing",
                "action": "retry_file_processing",
                "target": quote_id,
                "style": "warning"
            })
        
        actions.append({
            "label": "Dismiss",
            "action": "dismiss",
            "style": "secondary"
        })
        
        return actions
    
    async def _auto_dismiss_alert(self, alert_id: int, delay_seconds: int):
        """Auto-dismiss alert after specified delay"""
        await asyncio.sleep(delay_seconds)
        self.dismiss_alert(alert_id)
    
    def dismiss_alert(self, alert_id: int) -> bool:
        """Dismiss an alert"""
        for alert in self.active_alerts:
            if alert["id"] == alert_id:
                alert["dismissed"] = True
                alert["dismissed_at"] = datetime.utcnow().isoformat()
                return True
        return False
    
    def get_active_alerts(self, user_id: Optional[int] = None) -> List[Dict]:
        """Get all active alerts for a user"""
        alerts = [alert for alert in self.active_alerts if not alert["dismissed"]]
        
        if user_id:
            alerts = [alert for alert in alerts if alert["user_id"] is None or alert["user_id"] == user_id]
        
        # Sort by creation time, newest first
        alerts.sort(key=lambda x: x["created_at"], reverse=True)
        
        return alerts
    
    def get_alert_counts(self, user_id: Optional[int] = None) -> Dict[str, int]:
        """Get count of alerts by type"""
        active_alerts = self.get_active_alerts(user_id)
        
        counts = {
            "total": len(active_alerts),
            "critical": len([a for a in active_alerts if a["type"] == AlertType.CRITICAL.value]),
            "error": len([a for a in active_alerts if a["type"] == AlertType.ERROR.value]),
            "warning": len([a for a in active_alerts if a["type"] == AlertType.WARNING.value]),
            "info": len([a for a in active_alerts if a["type"] == AlertType.INFO.value]),
            "success": len([a for a in active_alerts if a["type"] == AlertType.SUCCESS.value])
        }
        
        return counts


class QuoteJourneyTracker:
    """Service for tracking detailed quote journey phases"""
    
    def __init__(self, db: Session, notification_service: NotificationService):
        self.db = db
        self.notification_service = notification_service
        self.quote_phases = {}  # quote_id -> phase info
    
    async def update_quote_phase(
        self,
        quote_id: int,
        phase: QuoteJourneyPhase,
        metadata: Optional[Dict] = None,
        user_id: Optional[int] = None
    ):
        """Update quote phase and create appropriate notifications"""
        
        phase_info = {
            "phase": phase.value,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": metadata or {},
            "user_id": user_id,
            "duration_in_phase": 0
        }
        
        # Calculate time in previous phase
        if quote_id in self.quote_phases:
            previous_phase = self.quote_phases[quote_id]
            previous_time = datetime.fromisoformat(previous_phase["timestamp"])
            current_time = datetime.utcnow()
            phase_info["duration_in_previous_phase"] = (current_time - previous_time).total_seconds()
        
        self.quote_phases[quote_id] = phase_info
        
        # Create appropriate alerts based on phase
        await self._create_phase_alert(quote_id, phase, metadata, user_id)
        
        # Check for SLA violations
        await self._check_sla_violations(quote_id, phase)
        
        # Log phase change
        logger.info(f"Quote {quote_id} moved to phase: {phase.value}")
    
    async def _create_phase_alert(
        self,
        quote_id: int,
        phase: QuoteJourneyPhase,
        metadata: Optional[Dict],
        user_id: Optional[int]
    ):
        """Create alerts based on phase transitions"""
        
        phase_alerts = {
            QuoteJourneyPhase.CREATED: {
                "title": "New Quote Created",
                "message": f"Quote #{quote_id} has been created and is ready for file upload",
                "type": AlertType.INFO,
                "category": AlertCategory.QUOTE_STATUS
            },
            QuoteJourneyPhase.AI_ANALYSIS_PROCESSING: {
                "title": "AI Analysis in Progress",
                "message": f"Quote #{quote_id} is being analyzed by AI systems",
                "type": AlertType.INFO,
                "category": AlertCategory.AI_ANALYSIS,
                "auto_dismiss": 30
            },
            QuoteJourneyPhase.AI_ANALYSIS_COMPLETED: {
                "title": "AI Analysis Complete",
                "message": f"Quote #{quote_id} AI analysis completed with {metadata.get('confidence', 'N/A')}% confidence",
                "type": AlertType.SUCCESS,
                "category": AlertCategory.AI_ANALYSIS,
                "auto_dismiss": 10
            },
            QuoteJourneyPhase.PENDING_APPROVAL: {
                "title": "Approval Required",
                "message": f"Quote #{quote_id} is pending manager approval",
                "type": AlertType.WARNING,
                "category": AlertCategory.APPROVAL
            },
            QuoteJourneyPhase.APPROVED: {
                "title": "Quote Approved",
                "message": f"Quote #{quote_id} has been approved and is ready to send",
                "type": AlertType.SUCCESS,
                "category": AlertCategory.QUOTE_STATUS,
                "auto_dismiss": 15
            },
            QuoteJourneyPhase.SENT_TO_CLIENT: {
                "title": "Quote Sent to Client",
                "message": f"Quote #{quote_id} has been sent to client for review",
                "type": AlertType.SUCCESS,
                "category": AlertCategory.QUOTE_STATUS,
                "auto_dismiss": 10
            },
            QuoteJourneyPhase.REVISION_REQUIRED: {
                "title": "Revision Required",
                "message": f"Quote #{quote_id} requires revisions based on feedback",
                "type": AlertType.WARNING,
                "category": AlertCategory.QUALITY
            },
            QuoteJourneyPhase.EXPIRED: {
                "title": "Quote Expired",
                "message": f"Quote #{quote_id} has expired and needs attention",
                "type": AlertType.ERROR,
                "category": AlertCategory.DEADLINE
            }
        }
        
        if phase in phase_alerts:
            alert_config = phase_alerts[phase]
            await self.notification_service.create_alert(
                title=alert_config["title"],
                message=alert_config["message"],
                alert_type=alert_config["type"],
                category=alert_config["category"],
                quote_id=quote_id,
                user_id=user_id,
                metadata=metadata,
                auto_dismiss_after=alert_config.get("auto_dismiss")
            )
    
    async def _check_sla_violations(self, quote_id: int, current_phase: QuoteJourneyPhase):
        """Check for SLA violations and create alerts"""
        
        if quote_id not in self.quote_phases:
            return
        
        phase_info = self.quote_phases[quote_id]
        phase_start = datetime.fromisoformat(phase_info["timestamp"])
        time_in_phase = (datetime.utcnow() - phase_start).total_seconds() / 3600  # hours
        
        # SLA thresholds (in hours)
        sla_thresholds = {
            QuoteJourneyPhase.AI_ANALYSIS_PROCESSING: 2,
            QuoteJourneyPhase.TECHNICAL_REVIEW: 24,
            QuoteJourneyPhase.PENDING_APPROVAL: 48,
            QuoteJourneyPhase.CLIENT_REVIEW: 168  # 7 days
        }
        
        if current_phase in sla_thresholds and time_in_phase > sla_thresholds[current_phase]:
            await self.notification_service.create_alert(
                title="SLA Violation",
                message=f"Quote #{quote_id} has been in {current_phase.value} phase for {time_in_phase:.1f} hours",
                alert_type=AlertType.WARNING if time_in_phase < sla_thresholds[current_phase] * 1.5 else AlertType.ERROR,
                category=AlertCategory.DEADLINE,
                quote_id=quote_id,
                metadata={"time_in_phase_hours": time_in_phase, "sla_threshold": sla_thresholds[current_phase]}
            )
    
    def get_quote_journey(self, quote_id: int) -> Dict[str, Any]:
        """Get complete journey information for a quote"""
        
        if quote_id not in self.quote_phases:
            return {"error": "Quote journey not found"}
        
        current_phase_info = self.quote_phases[quote_id]
        current_phase = QuoteJourneyPhase(current_phase_info["phase"])
        
        # Define the complete journey map
        journey_map = self._get_journey_map()
        
        # Calculate progress
        total_phases = len(journey_map)
        current_phase_index = list(journey_map.keys()).index(current_phase)
        progress_percentage = ((current_phase_index + 1) / total_phases) * 100
        
        # Get phase timeline
        timeline = self._build_phase_timeline(quote_id, journey_map)
        
        # Calculate estimated completion
        estimated_completion = self._estimate_completion_time(current_phase, current_phase_info)
        
        return {
            "quote_id": quote_id,
            "current_phase": {
                "phase": current_phase.value,
                "title": journey_map[current_phase]["title"],
                "description": journey_map[current_phase]["description"],
                "icon": journey_map[current_phase]["icon"],
                "color": journey_map[current_phase]["color"],
                "timestamp": current_phase_info["timestamp"],
                "duration": self._calculate_phase_duration(current_phase_info["timestamp"])
            },
            "progress": {
                "percentage": round(progress_percentage, 1),
                "current_step": current_phase_index + 1,
                "total_steps": total_phases,
                "status": self._get_progress_status(current_phase)
            },
            "timeline": timeline,
            "estimated_completion": estimated_completion,
            "next_actions": self._get_next_actions(current_phase),
            "sla_status": self._get_sla_status(quote_id, current_phase)
        }
    
    def _get_journey_map(self) -> Dict[QuoteJourneyPhase, Dict[str, Any]]:
        """Get the complete journey map with phase details"""
        return {
            QuoteJourneyPhase.CREATED: {
                "title": "Quote Created",
                "description": "Quote has been initialized in the system",
                "icon": "DocumentPlusIcon",
                "color": "blue",
                "category": "initial"
            },
            QuoteJourneyPhase.FILES_UPLOADED: {
                "title": "Files Uploaded",
                "description": "CAD files and documents have been uploaded",
                "icon": "CloudArrowUpIcon",
                "color": "blue",
                "category": "initial"
            },
            QuoteJourneyPhase.FILE_VALIDATION: {
                "title": "File Validation",
                "description": "Uploaded files are being validated",
                "icon": "CheckBadgeIcon",
                "color": "yellow",
                "category": "processing"
            },
            QuoteJourneyPhase.AI_ANALYSIS_PROCESSING: {
                "title": "AI Analysis",
                "description": "AI is analyzing drawings and calculating costs",
                "icon": "CpuChipIcon",
                "color": "purple",
                "category": "processing"
            },
            QuoteJourneyPhase.AI_ANALYSIS_COMPLETED: {
                "title": "Analysis Complete",
                "description": "AI analysis has been completed successfully",
                "icon": "CheckCircleIcon",
                "color": "green",
                "category": "processing"
            },
            QuoteJourneyPhase.TECHNICAL_REVIEW: {
                "title": "Technical Review",
                "description": "Technical team is reviewing the analysis",
                "icon": "MagnifyingGlassIcon",
                "color": "orange",
                "category": "review"
            },
            QuoteJourneyPhase.COST_CALCULATION: {
                "title": "Cost Calculation",
                "description": "Final costs are being calculated",
                "icon": "CalculatorIcon",
                "color": "yellow",
                "category": "review"
            },
            QuoteJourneyPhase.PENDING_APPROVAL: {
                "title": "Pending Approval",
                "description": "Quote is waiting for management approval",
                "icon": "ClockIcon",
                "color": "yellow",
                "category": "approval"
            },
            QuoteJourneyPhase.APPROVED: {
                "title": "Approved",
                "description": "Quote has been approved for sending",
                "icon": "CheckBadgeIcon",
                "color": "green",
                "category": "approval"
            },
            QuoteJourneyPhase.SENT_TO_CLIENT: {
                "title": "Sent to Client",
                "description": "Quote has been sent to the client",
                "icon": "PaperAirplaneIcon",
                "color": "blue",
                "category": "final"
            },
            QuoteJourneyPhase.CLIENT_REVIEW: {
                "title": "Client Review",
                "description": "Client is reviewing the quote",
                "icon": "EyeIcon",
                "color": "gray",
                "category": "final"
            },
            QuoteJourneyPhase.COMPLETED: {
                "title": "Completed",
                "description": "Quote process has been completed",
                "icon": "CheckCircleIcon",
                "color": "green",
                "category": "final"
            }
        }
    
    def _build_phase_timeline(self, quote_id: int, journey_map: Dict) -> List[Dict]:
        """Build timeline of phase transitions"""
        # This would query the database for actual phase history
        # For now, return current phase info
        if quote_id in self.quote_phases:
            current_info = self.quote_phases[quote_id]
            current_phase = QuoteJourneyPhase(current_info["phase"])
            
            return [{
                "phase": current_phase.value,
                "title": journey_map[current_phase]["title"],
                "timestamp": current_info["timestamp"],
                "duration": self._calculate_phase_duration(current_info["timestamp"]),
                "completed": True,
                "metadata": current_info.get("metadata", {})
            }]
        
        return []
    
    def _calculate_phase_duration(self, start_timestamp: str) -> Dict[str, Any]:
        """Calculate how long has been spent in current phase"""
        start_time = datetime.fromisoformat(start_timestamp)
        duration_seconds = (datetime.utcnow() - start_time).total_seconds()
        
        hours = int(duration_seconds // 3600)
        minutes = int((duration_seconds % 3600) // 60)
        
        return {
            "total_seconds": duration_seconds,
            "hours": hours,
            "minutes": minutes,
            "display": f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"
        }
    
    def _get_progress_status(self, phase: QuoteJourneyPhase) -> str:
        """Get overall progress status"""
        if phase in [QuoteJourneyPhase.COMPLETED]:
            return "completed"
        elif phase in [QuoteJourneyPhase.REJECTED, QuoteJourneyPhase.EXPIRED]:
            return "failed"
        elif phase in [QuoteJourneyPhase.ON_HOLD, QuoteJourneyPhase.REVISION_REQUIRED]:
            return "on_hold"
        else:
            return "in_progress"
    
    def _estimate_completion_time(self, current_phase: QuoteJourneyPhase, phase_info: Dict) -> Dict[str, Any]:
        """Estimate when quote will be completed"""
        # Estimated times for each remaining phase (in hours)
        phase_estimates = {
            QuoteJourneyPhase.CREATED: 72,
            QuoteJourneyPhase.FILES_UPLOADED: 48,
            QuoteJourneyPhase.AI_ANALYSIS_PROCESSING: 24,
            QuoteJourneyPhase.TECHNICAL_REVIEW: 12,
            QuoteJourneyPhase.PENDING_APPROVAL: 8,
            QuoteJourneyPhase.APPROVED: 2,
            QuoteJourneyPhase.SENT_TO_CLIENT: 168,  # 7 days for client response
        }
        
        estimated_hours = phase_estimates.get(current_phase, 24)
        estimated_completion = datetime.utcnow() + timedelta(hours=estimated_hours)
        
        return {
            "estimated_hours_remaining": estimated_hours,
            "estimated_completion_date": estimated_completion.isoformat(),
            "confidence": "medium"  # This could be calculated based on historical data
        }
    
    def _get_next_actions(self, current_phase: QuoteJourneyPhase) -> List[Dict]:
        """Get suggested next actions for current phase"""
        actions_map = {
            QuoteJourneyPhase.CREATED: [
                {"action": "upload_files", "label": "Upload CAD Files", "priority": "high"}
            ],
            QuoteJourneyPhase.FILES_UPLOADED: [
                {"action": "start_ai_analysis", "label": "Start AI Analysis", "priority": "high"}
            ],
            QuoteJourneyPhase.AI_ANALYSIS_COMPLETED: [
                {"action": "technical_review", "label": "Start Technical Review", "priority": "high"},
                {"action": "view_analysis", "label": "View AI Analysis Results", "priority": "medium"}
            ],
            QuoteJourneyPhase.TECHNICAL_REVIEW: [
                {"action": "approve_analysis", "label": "Approve Technical Analysis", "priority": "high"},
                {"action": "request_revision", "label": "Request Revision", "priority": "medium"}
            ],
            QuoteJourneyPhase.PENDING_APPROVAL: [
                {"action": "approve_quote", "label": "Approve Quote", "priority": "high"},
                {"action": "reject_quote", "label": "Reject Quote", "priority": "medium"}
            ],
            QuoteJourneyPhase.APPROVED: [
                {"action": "send_to_client", "label": "Send to Client", "priority": "high"}
            ]
        }
        
        return actions_map.get(current_phase, [])
    
    def _get_sla_status(self, quote_id: int, current_phase: QuoteJourneyPhase) -> Dict[str, Any]:
        """Get SLA status for current phase"""
        if quote_id not in self.quote_phases:
            return {"status": "unknown"}
        
        phase_info = self.quote_phases[quote_id]
        phase_start = datetime.fromisoformat(phase_info["timestamp"])
        time_in_phase_hours = (datetime.utcnow() - phase_start).total_seconds() / 3600
        
        # SLA thresholds
        sla_thresholds = {
            QuoteJourneyPhase.AI_ANALYSIS_PROCESSING: 2,
            QuoteJourneyPhase.TECHNICAL_REVIEW: 24,
            QuoteJourneyPhase.PENDING_APPROVAL: 48,
            QuoteJourneyPhase.CLIENT_REVIEW: 168
        }
        
        if current_phase not in sla_thresholds:
            return {"status": "no_sla"}
        
        threshold = sla_thresholds[current_phase]
        remaining_hours = threshold - time_in_phase_hours
        
        if remaining_hours > threshold * 0.5:
            status = "on_track"
        elif remaining_hours > 0:
            status = "approaching"
        else:
            status = "violated"
        
        return {
            "status": status,
            "threshold_hours": threshold,
            "elapsed_hours": round(time_in_phase_hours, 1),
            "remaining_hours": max(0, round(remaining_hours, 1)),
            "percentage_used": min(100, round((time_in_phase_hours / threshold) * 100, 1))
        }