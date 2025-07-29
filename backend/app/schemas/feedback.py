"""
Pydantic Schemas for Feedback Learning System

This module defines all the data models used for request/response validation
in the feedback learning API. These schemas ensure data integrity and provide
clear documentation for API consumers.

The schemas cover:
1. Feedback Submission: Data structure for submitting actual vs predicted results
2. Analytics Response: Comprehensive learning system analytics
3. Performance Metrics: Model performance evaluation data
4. Learning Status: Real-time system status and metrics

Each schema includes detailed field descriptions and validation rules to
ensure high-quality data for the machine learning feedback loop.
"""

from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from pydantic import BaseModel, Field, validator
from enum import Enum


class FeedbackType(str, Enum):
    """
    Enumeration of different feedback submission types.
    
    This helps categorize feedback sources and apply appropriate
    processing and weighting in the learning algorithms.
    """
    MANUAL = "manual"              # User manually entered feedback
    AUTOMATED = "automated"        # Automatically collected from systems
    ESTIMATED = "estimated"        # Estimated based on similar cases
    IMPORTED = "imported"          # Bulk imported historical data


class QualityRating(int, Enum):
    """
    Standard quality rating scale for manufactured parts.
    
    This provides a consistent way to evaluate manufacturing
    quality outcomes across different projects and teams.
    """
    POOR = 1          # Significant quality issues, rework required
    BELOW_AVERAGE = 2 # Minor quality issues, minimal rework
    AVERAGE = 3       # Meets standard quality expectations
    GOOD = 4          # Above average quality, no issues
    EXCELLENT = 5     # Exceptional quality, exceeds expectations


class FeedbackSubmission(BaseModel):
    """
    Schema for submitting feedback comparing AI predictions with actual results.
    
    This is the primary data structure for collecting real-world manufacturing
    outcomes that will be used to improve AI prediction accuracy through
    machine learning. The schema enforces data quality requirements while
    remaining flexible for different manufacturing scenarios.
    
    Key design principles:
    - Required fields ensure minimum viable learning data
    - Optional fields provide rich context for advanced learning
    - Validation ensures data quality and consistency
    - Comments explain the business purpose of each field
    """
    
    # Core prediction comparison (required for learning)
    predicted_cost: float = Field(
        ..., 
        gt=0, 
        description="AI predicted cost in USD. Must be positive value from original quote."
    )
    
    actual_cost: float = Field(
        ..., 
        gt=0, 
        description="Actual manufacturing cost in USD. This is the real cost incurred."
    )
    
    # Time predictions (optional but valuable for learning)
    predicted_time: Optional[float] = Field(
        None, 
        ge=0, 
        description="AI predicted manufacturing time in hours. None if not predicted."
    )
    
    actual_time: Optional[float] = Field(
        None, 
        ge=0, 
        description="Actual manufacturing time in hours. Critical for time estimation learning."
    )
    
    # Process and quality feedback (enriches learning context)
    predicted_processes: Optional[List[str]] = Field(
        None, 
        description="List of manufacturing processes AI recommended (e.g., ['cnc_milling', 'drilling'])"
    )
    
    actual_processes: Optional[List[str]] = Field(
        None, 
        description="List of processes actually used in manufacturing. Helps improve process selection."
    )
    
    quality_rating: Optional[QualityRating] = Field(
        None, 
        description="Quality assessment of final manufactured part (1-5 scale)"
    )
    
    # Contextual information (helps AI understand manufacturing conditions)
    material_used: Optional[str] = Field(
        None, 
        max_length=100, 
        description="Actual material used (e.g., 'aluminum_6061', 'steel_304'). Case insensitive."
    )
    
    complexity_level: Optional[str] = Field(
        None, 
        regex="^(low|medium|high)$", 
        description="Subjective complexity assessment of the manufactured part"
    )
    
    # Rich context for advanced learning
    manufacturing_notes: Optional[str] = Field(
        None, 
        max_length=1000, 
        description="Free text notes about manufacturing challenges, successes, or observations"
    )
    
    # Metadata for feedback quality assessment
    feedback_type: FeedbackType = Field(
        FeedbackType.MANUAL, 
        description="Source/method of feedback collection"
    )
    
    confidence_level: float = Field(
        1.0, 
        ge=0.0, 
        le=1.0, 
        description="Confidence in feedback accuracy (0.0-1.0). Used for learning weight."
    )
    
    # Optional part identification for cross-referencing
    part_id: Optional[int] = Field(
        None, 
        description="Database ID of the specific part this feedback relates to"
    )

    @validator('material_used')
    def normalize_material(cls, v):
        """
        Normalize material names for consistent learning.
        
        This ensures material names are consistent across the system,
        which is crucial for the AI to learn material-specific patterns.
        """
        if v:
            return v.lower().replace(' ', '_').replace('-', '_')
        return v

    @validator('actual_processes', 'predicted_processes')
    def normalize_processes(cls, v):
        """
        Normalize process names for consistent learning.
        
        Standardizes process naming to ensure the AI can properly
        correlate process combinations with outcomes.
        """
        if v:
            return [process.lower().replace(' ', '_').replace('-', '_') for process in v]
        return v

    class Config:
        """Pydantic configuration for the feedback submission model."""
        schema_extra = {
            "example": {
                "predicted_cost": 1250.00,
                "actual_cost": 1380.50,
                "predicted_time": 12.5,
                "actual_time": 14.2,
                "predicted_processes": ["cnc_milling", "drilling"],
                "actual_processes": ["cnc_milling", "drilling", "manual_finishing"],
                "quality_rating": 4,
                "material_used": "aluminum_6061",
                "complexity_level": "medium",
                "manufacturing_notes": "Required additional hand finishing for surface quality",
                "feedback_type": "manual",
                "confidence_level": 0.9,
                "part_id": 123
            }
        }


class ImpactMetrics(BaseModel):
    """
    Metrics describing the learning impact of submitted feedback.
    
    These metrics help users understand how their feedback contributes
    to improving the AI system and provide transparency into the
    learning process.
    """
    
    prediction_error: float = Field(
        description="Percentage error between predicted and actual values"
    )
    
    learning_value: str = Field(
        description="Qualitative assessment of feedback value (low, medium, high)"
    )
    
    model_improvement_potential: float = Field(
        ge=0.0, 
        le=1.0, 
        description="Estimated potential for this feedback to improve model accuracy"
    )
    
    rare_case_value: float = Field(
        ge=0.0, 
        le=1.0, 
        description="Value of feedback for rare/underrepresented scenarios"
    )
    
    overall_impact_score: float = Field(
        ge=0.0, 
        le=1.0, 
        description="Combined impact score for this feedback submission"
    )


class FeedbackResponse(BaseModel):
    """
    Response schema for feedback submission results.
    
    Provides comprehensive information about the feedback processing
    including success status, learning impact, and system response.
    """
    
    success: bool = Field(description="Whether feedback was successfully processed")
    
    feedback_id: Optional[int] = Field(
        description="Database ID of the created feedback record"
    )
    
    message: str = Field(description="Human-readable result message")
    
    learning_triggered: bool = Field(
        description="Whether this feedback triggered model learning updates"
    )
    
    learning_results: Optional[Dict[str, Any]] = Field(
        description="Results from model learning process, if triggered"
    )
    
    impact_metrics: Optional[ImpactMetrics] = Field(
        description="Metrics about the learning impact of this feedback"
    )
    
    processing_time: float = Field(
        description="Time taken to process feedback in seconds"
    )


class AccuracyTrends(BaseModel):
    """
    Historical accuracy trends for different prediction types.
    
    Tracks how prediction accuracy changes over time as the system
    learns from more feedback data.
    """
    
    cost_prediction_accuracy: List[float] = Field(
        description="Historical cost prediction accuracy scores (0.0-1.0)"
    )
    
    time_prediction_accuracy: List[float] = Field(
        description="Historical time prediction accuracy scores (0.0-1.0)"
    )
    
    process_prediction_accuracy: List[float] = Field(
        description="Historical process selection accuracy scores (0.0-1.0)"
    )


class ErrorAnalysis(BaseModel):
    """
    Detailed analysis of prediction error patterns.
    
    Helps identify systematic issues and improvement opportunities
    in the AI prediction models.
    """
    
    common_error_patterns: List[Dict[str, Any]] = Field(
        description="Frequently occurring error patterns and their characteristics"
    )
    
    largest_discrepancies: List[Dict[str, Any]] = Field(
        description="Cases with the largest prediction errors for investigation"
    )
    
    improvement_opportunities: List[str] = Field(
        description="Identified areas where model performance could be enhanced"
    )


class LearningEffectiveness(BaseModel):
    """
    Metrics about how effectively the system learns from feedback.
    
    Measures the performance of the online learning system itself,
    not just the prediction accuracy.
    """
    
    model_performance_before_feedback: float = Field(
        description="Model accuracy before incorporating recent feedback"
    )
    
    model_performance_after_feedback: float = Field(
        description="Model accuracy after incorporating recent feedback"
    )
    
    learning_rate: float = Field(
        description="Rate at which the model improves with new feedback"
    )
    
    feedback_utilization_rate: float = Field(
        description="Percentage of feedback successfully used for learning"
    )


class FeedbackAnalytics(BaseModel):
    """
    Comprehensive analytics about the feedback learning system.
    
    Provides detailed insights into system performance, learning
    effectiveness, and prediction accuracy trends.
    """
    
    summary: Dict[str, Any] = Field(
        description="High-level summary statistics about feedback and learning"
    )
    
    accuracy_trends: AccuracyTrends = Field(
        description="Historical trends in prediction accuracy"
    )
    
    error_analysis: ErrorAnalysis = Field(
        description="Analysis of prediction errors and patterns"
    )
    
    learning_effectiveness: LearningEffectiveness = Field(
        description="Metrics about the effectiveness of the learning system"
    )
    
    time_period_days: int = Field(
        description="Number of days covered by this analytics report"
    )
    
    generated_at: datetime = Field(
        description="Timestamp when analytics were generated"
    )
    
    user_filter: Optional[int] = Field(
        description="User ID filter applied to analytics, if any"
    )


class LearningMetrics(BaseModel):
    """
    Real-time metrics about the learning system status and performance.
    
    Provides current operational status of the online learning system
    for monitoring and debugging purposes.
    """
    
    current_metrics: Dict[str, Any] = Field(
        description="Current system performance and status metrics"
    )
    
    model_details: Dict[str, Any] = Field(
        description="Detailed information about loaded AI models"
    )
    
    recent_accuracy: Dict[str, Any] = Field(
        description="Recent prediction accuracy trends and improvements"
    )
    
    system_health: Dict[str, Any] = Field(
        description="Overall health and status of the learning system"
    )
    
    generated_at: datetime = Field(
        description="Timestamp when metrics were collected"
    )


class ModelPerformance(BaseModel):
    """
    Detailed model performance evaluation and statistics.
    
    Comprehensive analysis of AI model performance including
    accuracy metrics, error analysis, and confidence assessment.
    """
    
    evaluation_period_days: int = Field(
        description="Time window used for performance evaluation"
    )
    
    sample_count: int = Field(
        description="Number of feedback samples used in evaluation"
    )
    
    accuracy_metrics: Dict[str, Any] = Field(
        description="Quantitative accuracy metrics (MAE, MSE, R² scores)"
    )
    
    error_analysis: Dict[str, Any] = Field(
        description="Statistical analysis of prediction errors"
    )
    
    performance_trends: Dict[str, Any] = Field(
        description="Trends in model performance over time"
    )
    
    model_confidence: Dict[str, Any] = Field(
        description="Analysis of model confidence scores and their accuracy"
    )
    
    generated_at: datetime = Field(
        description="Timestamp when performance evaluation was conducted"
    )
    
    message: Optional[str] = Field(
        description="Additional information about the performance evaluation"
    )


class BatchFeedbackItem(BaseModel):
    """
    Individual feedback item for batch submission.
    
    Similar to FeedbackSubmission but includes quote_id for
    batch processing scenarios.
    """
    
    quote_id: int = Field(description="ID of the quote this feedback relates to")
    
    # Inherit all fields from FeedbackSubmission
    predicted_cost: float = Field(..., gt=0)
    actual_cost: float = Field(..., gt=0)
    predicted_time: Optional[float] = Field(None, ge=0)
    actual_time: Optional[float] = Field(None, ge=0)
    predicted_processes: Optional[List[str]] = None
    actual_processes: Optional[List[str]] = None
    quality_rating: Optional[QualityRating] = None
    material_used: Optional[str] = Field(None, max_length=100)
    complexity_level: Optional[str] = Field(None, regex="^(low|medium|high)$")
    manufacturing_notes: Optional[str] = Field(None, max_length=1000)
    feedback_type: FeedbackType = FeedbackType.MANUAL
    confidence_level: float = Field(1.0, ge=0.0, le=1.0)
    part_id: Optional[int] = None


class BatchFeedbackResponse(BaseModel):
    """
    Response schema for batch feedback submission.
    
    Provides detailed results for bulk feedback processing including
    success/failure counts and individual error details.
    """
    
    total_submitted: int = Field(description="Total number of feedback items submitted")
    
    successful_submissions: int = Field(description="Number of successfully processed items")
    
    failed_submissions: int = Field(description="Number of failed submissions")
    
    processing_errors: List[Dict[str, Any]] = Field(
        description="Detailed error information for failed submissions"
    )
    
    learning_triggered: bool = Field(
        description="Whether batch processing triggered model learning"
    )
    
    batch_learning_results: Optional[Dict[str, Any]] = Field(
        description="Results from batch learning process, if triggered"
    )
    
    processing_time: float = Field(description="Total time to process batch in seconds")
    
    success_rate: float = Field(
        ge=0.0, 
        le=1.0, 
        description="Percentage of successful submissions"
    )
    
    overall_status: str = Field(
        description="Overall batch processing status (success, partial_success, etc.)"
    )


class FeedbackHistoryItem(BaseModel):
    """
    Individual feedback record for history retrieval.
    
    Represents a single feedback submission with calculated
    metrics and processing status.
    """
    
    id: int = Field(description="Unique feedback record ID")
    quote_id: int = Field(description="Associated quote ID")
    part_id: Optional[int] = Field(description="Associated part ID, if any")
    
    predicted_cost: float = Field(description="Original AI cost prediction")
    actual_cost: float = Field(description="Actual manufacturing cost")
    predicted_time: Optional[float] = Field(description="Original AI time prediction")
    actual_time: Optional[float] = Field(description="Actual manufacturing time")
    
    cost_accuracy_percentage: Optional[float] = Field(
        description="Calculated accuracy of cost prediction (0-100%)"
    )
    
    material_used: Optional[str] = Field(description="Material actually used")
    quality_rating: Optional[int] = Field(description="Quality rating (1-5)")
    feedback_type: str = Field(description="Type of feedback submission")
    confidence_level: float = Field(description="Confidence level of feedback")
    
    created_at: Optional[str] = Field(description="Feedback submission timestamp")
    has_been_used_for_training: bool = Field(
        description="Whether this feedback has been incorporated into model training"
    )
    
    manufacturing_notes: Optional[str] = Field(description="Additional notes")


class FeedbackHistoryResponse(BaseModel):
    """
    Response schema for feedback history retrieval.
    
    Provides paginated access to historical feedback data with
    filtering and sorting information.
    """
    
    feedback_records: List[FeedbackHistoryItem] = Field(
        description="List of feedback records matching the query"
    )
    
    pagination: Dict[str, Any] = Field(
        description="Pagination information (total_count, has_next, etc.)"
    )
    
    filters_applied: Dict[str, Any] = Field(
        description="Summary of filters applied to the query"
    )
    
    sorting: Dict[str, Any] = Field(
        description="Sorting criteria applied to results"
    )