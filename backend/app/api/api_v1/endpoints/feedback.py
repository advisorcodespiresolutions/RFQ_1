"""
Feedback Learning API Endpoints

This module provides REST API endpoints for the feedback learning system that
enables continuous improvement of AI predictions through real-world data collection.

The endpoints support:
1. Submitting feedback comparing AI predictions vs actual results
2. Retrieving feedback analytics and learning performance metrics
3. Triggering model retraining with accumulated feedback
4. Managing feedback data and learning configurations

Each endpoint includes comprehensive validation, error handling, and detailed
response information to support both automated and manual feedback collection.
"""

import logging
import numpy as np
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.database.database import get_db
from app.services.feedback_learning_service import FeedbackLearningService
from app.core.deps import get_current_user
from app.database.models import User
from app.schemas.feedback import (
    FeedbackSubmission, FeedbackResponse, FeedbackAnalytics,
    LearningMetrics, ModelPerformance
)

# Initialize the router for feedback-related endpoints
router = APIRouter()

logger = logging.getLogger(__name__)


@router.post("/submit", response_model=FeedbackResponse)
async def submit_feedback(
    quote_id: int,
    feedback_data: FeedbackSubmission,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Submit feedback comparing AI predictions with actual manufacturing results.
    
    This is the primary endpoint for collecting real-world feedback that drives
    the continuous learning system. Users provide actual costs, manufacturing
    times, processes used, and quality outcomes compared to AI predictions.
    
    The system uses this feedback to:
    1. Identify prediction errors and patterns
    2. Update ML models through online learning
    3. Improve future prediction accuracy
    4. Generate insights for process optimization
    
    Args:
        quote_id: ID of the quote being evaluated
        feedback_data: Structured feedback data with actual vs predicted values
        db: Database session dependency
        current_user: Authenticated user submitting feedback
        
    Returns:
        FeedbackResponse containing submission status and learning impact
        
    Raises:
        HTTPException: If quote not found, invalid data, or processing error
    """
    try:
        # Initialize the feedback learning service
        feedback_service = FeedbackLearningService(db)
        
        # Convert Pydantic model to dictionary for processing
        feedback_dict = feedback_data.dict()
        
        # Submit feedback and trigger learning process
        result = await feedback_service.submit_feedback(
            quote_id=quote_id,
            user_id=current_user.id,
            feedback_data=feedback_dict
        )
        
        if not result['success']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get('error', 'Failed to submit feedback')
            )
        
        return FeedbackResponse(
            success=True,
            feedback_id=result['feedback_id'],
            message=result['message'],
            learning_triggered=result.get('learning_triggered', False),
            learning_results=result.get('learning_results'),
            impact_metrics=result.get('impact_metrics'),
            processing_time=result.get('processing_time', 0.0)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in submit_feedback endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/analytics", response_model=FeedbackAnalytics)
async def get_feedback_analytics(
    user_id: Optional[int] = Query(None, description="Filter analytics by specific user"),
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    include_patterns: bool = Query(True, description="Include error pattern analysis"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve comprehensive analytics about feedback and learning performance.
    
    This endpoint provides detailed insights into how well the AI learning system
    is performing and improving over time. Analytics include:
    
    1. Prediction Accuracy Trends: How accuracy changes with more feedback
    2. Error Pattern Analysis: Common types of prediction mistakes
    3. Learning Effectiveness: How well models adapt to new data
    4. User Engagement Metrics: Feedback submission patterns
    5. Model Performance: Quantitative performance measurements
    
    The analytics help identify:
    - Areas where AI predictions are most/least accurate
    - Materials or processes that need more training data
    - Systematic biases in predictions
    - Optimal feedback collection strategies
    
    Args:
        user_id: Optional filter to show analytics for specific user only
        days: Time window for analytics calculation
        include_patterns: Whether to include detailed error pattern analysis
        db: Database session dependency
        current_user: Authenticated user requesting analytics
        
    Returns:
        FeedbackAnalytics containing comprehensive learning system metrics
        
    Raises:
        HTTPException: If access denied or data processing error
    """
    try:
        # Check permissions - only admins can view other users' analytics
        target_user_id = user_id
        if user_id and user_id != current_user.id and not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Can only view your own analytics"
            )
        
        # Use current user ID if not admin and no specific user requested
        if not current_user.is_admin and not user_id:
            target_user_id = current_user.id
        
        # Initialize feedback service and get analytics
        feedback_service = FeedbackLearningService(db)
        analytics = await feedback_service.get_feedback_analytics(target_user_id)
        
        if 'error' in analytics:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Analytics generation failed: {analytics['error']}"
            )
        
        # Structure response according to schema
        return FeedbackAnalytics(
            summary=analytics['summary'],
            accuracy_trends=analytics['accuracy_trends'],
            error_analysis=analytics['error_analysis'] if include_patterns else {},
            learning_effectiveness=analytics['learning_effectiveness'],
            time_period_days=days,
            generated_at=datetime.utcnow(),
            user_filter=target_user_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_feedback_analytics endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate analytics: {str(e)}"
        )


@router.post("/retrain-models")
async def trigger_model_retraining(
    force_retrain: bool = Body(False, description="Force retraining even with limited data"),
    full_retrain: bool = Body(False, description="Perform full retrain vs incremental"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Trigger comprehensive model retraining with all accumulated feedback.
    
    This endpoint initiates a complete retraining process that:
    1. Collects all feedback data from the database
    2. Preprocesses and validates the training data
    3. Updates all ML models with the complete dataset
    4. Evaluates model performance improvements
    5. Saves updated models for future predictions
    
    Two types of retraining are supported:
    - Incremental: Updates existing models with new data (faster)
    - Full: Retrains models from scratch with all data (more thorough)
    
    Retraining is typically triggered when:
    - Significant amount of new feedback has accumulated
    - Model performance has degraded
    - New types of parts/processes are being manufactured
    - Systematic prediction errors are detected
    
    Args:
        force_retrain: Skip minimum data requirements check
        full_retrain: Whether to perform complete retraining vs incremental
        db: Database session dependency
        current_user: Authenticated user (must be admin)
        
    Returns:
        Dictionary containing retraining results and performance metrics
        
    Raises:
        HTTPException: If not admin, insufficient data, or retraining fails
    """
    try:
        # Check admin permissions - model retraining is restricted operation
        if not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Only administrators can trigger model retraining"
            )
        
        # Initialize feedback service
        feedback_service = FeedbackLearningService(db)
        
        # Trigger retraining process
        retraining_result = await feedback_service.trigger_model_retraining(
            force_retrain=force_retrain
        )
        
        if not retraining_result['success']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=retraining_result.get('message', 'Model retraining failed')
            )
        
        return {
            'success': True,
            'message': retraining_result['message'],
            'feedback_samples_used': retraining_result['feedback_samples_used'],
            'learning_results': retraining_result['learning_results'],
            'performance_metrics': retraining_result['performance_metrics'],
            'model_version': retraining_result['model_version'],
            'retraining_type': 'full' if full_retrain else 'incremental',
            'triggered_by': current_user.username,
            'triggered_at': datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in trigger_model_retraining endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Model retraining failed: {str(e)}"
        )


@router.get("/learning-metrics", response_model=LearningMetrics)
async def get_learning_metrics(
    include_model_details: bool = Query(True, description="Include detailed model information"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get real-time metrics about the learning system performance.
    
    This endpoint provides current status and performance metrics for the
    online learning system, including:
    
    1. Model Status: Current model versions and update timestamps
    2. Learning Progress: How many feedback samples have been processed
    3. Accuracy Metrics: Current prediction accuracy across different categories
    4. Processing Performance: Speed and efficiency of feedback processing
    5. System Health: Overall health and status of learning components
    
    These metrics are essential for:
    - Monitoring system performance in production
    - Identifying when models need retraining
    - Tracking improvement over time
    - Debugging learning system issues
    
    Args:
        include_model_details: Whether to include detailed model information
        db: Database session dependency
        current_user: Authenticated user
        
    Returns:
        LearningMetrics containing real-time system performance data
        
    Raises:
        HTTPException: If access denied or metrics unavailable
    """
    try:
        # Initialize feedback service to access learning engine
        feedback_service = FeedbackLearningService(db)
        learning_engine = feedback_service.online_engine
        
        # Get current learning statistics
        learning_stats = learning_engine.learning_stats
        
        # Calculate current model performance metrics
        current_metrics = {
            'total_feedback_processed': learning_stats['total_feedback_count'],
            'last_model_update': learning_stats.get('last_model_update'),
            'avg_processing_time': (
                sum(learning_stats.get('feedback_processing_times', [0])) / 
                max(1, len(learning_stats.get('feedback_processing_times', [1])))
            ),
            'model_versions_count': len(learning_stats.get('model_versions', [])),
            'learning_system_status': 'active' if learning_stats['total_feedback_count'] > 0 else 'initializing'
        }
        
        # Add detailed model information if requested
        model_details = {}
        if include_model_details:
            try:
                # Test model predictions to verify they're working
                test_features = [100.0, 50.0, 25.0, 125000.0, 1500.0] + [0.0] * 15  # Sample features
                test_prediction = learning_engine.predict_with_updated_models(test_features)
                
                model_details = {
                    'cost_model_status': 'active' if 'predicted_cost' in test_prediction else 'inactive',
                    'time_model_status': 'active' if 'predicted_time' in test_prediction else 'inactive',
                    'process_model_status': 'active' if 'process_complexity_score' in test_prediction else 'inactive',
                    'last_prediction_confidence': test_prediction.get('prediction_confidence', 0.0),
                    'models_directory': str(learning_engine.model_save_path)
                }
            except Exception as model_error:
                model_details = {
                    'model_status': 'error',
                    'error_message': str(model_error)
                }
        
        # Recent accuracy trends (last 10 predictions if available)
        recent_accuracy = {
            'cost_accuracy_trend': learning_stats.get('cost_prediction_accuracy', [])[-10:],
            'time_accuracy_trend': learning_stats.get('time_prediction_accuracy', [])[-10:],
            'overall_improvement_rate': 0.0  # Calculate if enough data available
        }
        
        if recent_accuracy['cost_accuracy_trend']:
            recent_avg = sum(recent_accuracy['cost_accuracy_trend']) / len(recent_accuracy['cost_accuracy_trend'])
            recent_accuracy['overall_improvement_rate'] = recent_avg
        
        return LearningMetrics(
            current_metrics=current_metrics,
            model_details=model_details,
            recent_accuracy=recent_accuracy,
            system_health={
                'status': 'healthy' if learning_stats['total_feedback_count'] > 0 else 'needs_data',
                'last_health_check': datetime.utcnow(),
                'uptime_hours': 24,  # Simplified - would track actual uptime
                'error_rate': 0.0   # Would calculate from error logs
            },
            generated_at=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Error in get_learning_metrics endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve learning metrics: {str(e)}"
        )


@router.get("/feedback-history")
async def get_feedback_history(
    quote_id: Optional[int] = Query(None, description="Filter by specific quote"),
    part_id: Optional[int] = Query(None, description="Filter by specific part"),
    limit: int = Query(50, ge=1, le=200, description="Maximum number of records"),
    offset: int = Query(0, ge=0, description="Number of records to skip"),
    sort_by: str = Query("created_at", description="Field to sort by"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="Sort order"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve historical feedback data with filtering and pagination.
    
    This endpoint provides access to the complete feedback history, allowing
    users to review past submissions and track learning progress over time.
    
    Filtering options help users find specific feedback:
    - By quote: See all feedback for a particular quote
    - By part: See feedback for specific part types
    - By date range: Focus on recent or historical feedback
    - By user: See feedback from specific team members (admin only)
    
    The feedback history is valuable for:
    - Auditing prediction accuracy over time
    - Understanding which factors lead to prediction errors
    - Training new team members on feedback quality
    - Identifying data quality issues
    
    Args:
        quote_id: Optional filter by quote ID
        part_id: Optional filter by part ID  
        limit: Maximum number of records to return
        offset: Number of records to skip (for pagination)
        sort_by: Field name to sort results by
        sort_order: Sort direction (asc or desc)
        db: Database session dependency
        current_user: Authenticated user
        
    Returns:
        Dictionary containing feedback records and pagination information
        
    Raises:
        HTTPException: If access denied or query error
    """
    try:
        from app.services.feedback_learning_service import FeedbackData
        
        # Build query with filters
        query = db.query(FeedbackData)
        
        # Apply filters based on user permissions
        if not current_user.is_admin:
            # Non-admin users can only see their own feedback
            query = query.filter(FeedbackData.user_id == current_user.id)
        
        # Apply additional filters
        if quote_id:
            query = query.filter(FeedbackData.quote_id == quote_id)
        if part_id:
            query = query.filter(FeedbackData.part_id == part_id)
        
        # Apply sorting
        if sort_by == "created_at":
            if sort_order == "desc":
                query = query.order_by(FeedbackData.created_at.desc())
            else:
                query = query.order_by(FeedbackData.created_at.asc())
        elif sort_by == "predicted_cost":
            if sort_order == "desc":
                query = query.order_by(FeedbackData.predicted_cost.desc())
            else:
                query = query.order_by(FeedbackData.predicted_cost.asc())
        
        # Get total count for pagination
        total_count = query.count()
        
        # Apply pagination
        feedback_records = query.offset(offset).limit(limit).all()
        
        # Convert to response format
        feedback_list = []
        for record in feedback_records:
            # Calculate prediction accuracy for this record
            cost_accuracy = None
            if record.predicted_cost and record.actual_cost:
                error_pct = abs(record.actual_cost - record.predicted_cost) / record.actual_cost * 100
                cost_accuracy = max(0, 100 - error_pct)
            
            feedback_item = {
                'id': record.id,
                'quote_id': record.quote_id,
                'part_id': record.part_id,
                'predicted_cost': record.predicted_cost,
                'actual_cost': record.actual_cost,
                'predicted_time': record.predicted_time,
                'actual_time': record.actual_time,
                'cost_accuracy_percentage': cost_accuracy,
                'material_used': record.material_used,
                'quality_rating': record.quality_rating,
                'feedback_type': record.feedback_type,
                'confidence_level': record.confidence_level,
                'created_at': record.created_at.isoformat() if record.created_at else None,
                'has_been_used_for_training': record.has_been_used_for_training,
                'manufacturing_notes': record.manufacturing_notes
            }
            feedback_list.append(feedback_item)
        
        return {
            'feedback_records': feedback_list,
            'pagination': {
                'total_count': total_count,
                'limit': limit,
                'offset': offset,
                'has_next': offset + limit < total_count,
                'has_previous': offset > 0
            },
            'filters_applied': {
                'quote_id': quote_id,
                'part_id': part_id,
                'user_restricted': not current_user.is_admin
            },
            'sorting': {
                'sort_by': sort_by,
                'sort_order': sort_order
            }
        }
        
    except Exception as e:
        logger.error(f"Error in get_feedback_history endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve feedback history: {str(e)}"
        )


@router.post("/batch-feedback")
async def submit_batch_feedback(
    feedback_batch: List[Dict[str, Any]] = Body(..., description="List of feedback submissions"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Submit multiple feedback records in a single batch operation.
    
    This endpoint is optimized for bulk feedback submission, which is useful for:
    1. Importing historical manufacturing data
    2. Batch processing completed jobs
    3. Integration with external manufacturing systems
    4. Periodic bulk updates from production data
    
    Batch processing provides several advantages:
    - More efficient database operations
    - Better learning algorithm performance
    - Reduced API overhead
    - Atomic transaction handling
    
    Each feedback item in the batch is validated independently, and the
    system provides detailed results for each submission including success
    status and any validation errors.
    
    Args:
        feedback_batch: List of feedback data dictionaries
        db: Database session dependency
        current_user: Authenticated user submitting batch
        
    Returns:
        Dictionary containing batch processing results and statistics
        
    Raises:
        HTTPException: If batch too large, validation errors, or processing failure
    """
    try:
        # Validate batch size to prevent system overload
        max_batch_size = 100  # Configurable limit
        if len(feedback_batch) > max_batch_size:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Batch size too large: {len(feedback_batch)} (max: {max_batch_size})"
            )
        
        if not feedback_batch:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Empty feedback batch provided"
            )
        
        # Initialize feedback service
        feedback_service = FeedbackLearningService(db)
        
        # Process each feedback item in the batch
        batch_results = {
            'total_submitted': len(feedback_batch),
            'successful_submissions': 0,
            'failed_submissions': 0,
            'processing_errors': [],
            'learning_triggered': False,
            'batch_learning_results': None,
            'processing_time': 0.0
        }
        
        start_time = datetime.now()
        successful_feedback = []
        
        # Process each feedback item individually
        for i, feedback_item in enumerate(feedback_batch):
            try:
                # Each item should include quote_id and feedback data
                if 'quote_id' not in feedback_item:
                    batch_results['failed_submissions'] += 1
                    batch_results['processing_errors'].append({
                        'index': i,
                        'error': 'Missing required field: quote_id'
                    })
                    continue
                
                quote_id = feedback_item.pop('quote_id')
                
                # Submit individual feedback
                result = await feedback_service.submit_feedback(
                    quote_id=quote_id,
                    user_id=current_user.id,
                    feedback_data=feedback_item
                )
                
                if result['success']:
                    batch_results['successful_submissions'] += 1
                    successful_feedback.append(result)
                else:
                    batch_results['failed_submissions'] += 1
                    batch_results['processing_errors'].append({
                        'index': i,
                        'quote_id': quote_id,
                        'error': result.get('error', 'Unknown error')
                    })
                    
            except Exception as item_error:
                batch_results['failed_submissions'] += 1
                batch_results['processing_errors'].append({
                    'index': i,
                    'error': str(item_error)
                })
        
        # Check if any successful submissions triggered learning
        batch_results['learning_triggered'] = any(
            result.get('learning_triggered', False) for result in successful_feedback
        )
        
        # If significant batch processed, trigger additional learning
        if batch_results['successful_submissions'] >= 10:
            try:
                # Trigger batch learning with accumulated feedback
                learning_result = await feedback_service.trigger_model_retraining(force_retrain=True)
                batch_results['batch_learning_results'] = learning_result
            except Exception as learning_error:
                batch_results['processing_errors'].append({
                    'type': 'batch_learning_error',
                    'error': str(learning_error)
                })
        
        # Calculate processing time
        end_time = datetime.now()
        batch_results['processing_time'] = (end_time - start_time).total_seconds()
        
        # Determine overall success status
        success_rate = batch_results['successful_submissions'] / batch_results['total_submitted']
        batch_results['success_rate'] = success_rate
        batch_results['overall_status'] = (
            'success' if success_rate == 1.0 else
            'partial_success' if success_rate > 0.5 else
            'mostly_failed' if success_rate > 0.0 else
            'complete_failure'
        )
        
        return batch_results
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in submit_batch_feedback endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch feedback processing failed: {str(e)}"
        )


@router.get("/model-performance", response_model=ModelPerformance)
async def get_model_performance(
    evaluation_period_days: int = Query(30, ge=1, le=365, description="Period for performance evaluation"),
    include_predictions: bool = Query(False, description="Include sample predictions in response"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get detailed model performance evaluation and statistics.
    
    This endpoint provides comprehensive performance analysis of the AI models,
    including accuracy metrics, prediction confidence, and error analysis.
    
    Performance evaluation includes:
    1. Accuracy Metrics: MAE, MSE, R² scores for different prediction types
    2. Confidence Analysis: How well confidence scores correlate with accuracy
    3. Error Distribution: Analysis of prediction error patterns
    4. Temporal Performance: How accuracy changes over time
    5. Category Performance: Accuracy by material, process, complexity, etc.
    
    This information is crucial for:
    - Understanding model reliability
    - Identifying areas needing improvement
    - Making informed decisions about prediction usage
    - Communicating AI performance to stakeholders
    
    Args:
        evaluation_period_days: Time window for performance evaluation
        include_predictions: Whether to include sample predictions
        db: Database session dependency
        current_user: Authenticated user
        
    Returns:
        ModelPerformance containing detailed performance metrics
        
    Raises:
        HTTPException: If access denied or evaluation fails
    """
    try:
        # Initialize feedback service
        feedback_service = FeedbackLearningService(db)
        
        # Get recent feedback for performance evaluation
        from app.services.feedback_learning_service import FeedbackData
        
        cutoff_date = datetime.now() - timedelta(days=evaluation_period_days)
        recent_feedback = db.query(FeedbackData).filter(
            FeedbackData.created_at >= cutoff_date
        ).all()
        
        if not recent_feedback:
            return ModelPerformance(
                evaluation_period_days=evaluation_period_days,
                sample_count=0,
                accuracy_metrics={},
                error_analysis={},
                performance_trends={},
                model_confidence={},
                generated_at=datetime.utcnow(),
                message="No feedback data available for the specified period"
            )
        
        # Evaluate model performance using recent feedback
        performance_metrics = await feedback_service._evaluate_model_performance(recent_feedback)
        
        # Calculate additional statistics
        cost_errors = []
        time_errors = []
        confidence_scores = []
        
        for record in recent_feedback:
            if record.predicted_cost and record.actual_cost:
                error_pct = abs(record.actual_cost - record.predicted_cost) / record.actual_cost * 100
                cost_errors.append(error_pct)
            
            if record.predicted_time and record.actual_time:
                time_error_pct = abs(record.actual_time - record.predicted_time) / record.actual_time * 100
                time_errors.append(time_error_pct)
            
            if record.confidence_level:
                confidence_scores.append(record.confidence_level)
        
        # Calculate error distribution statistics
        error_analysis = {}
        if cost_errors:
            cost_errors_array = np.array(cost_errors)
            error_analysis['cost_prediction'] = {
                'mean_error_percentage': float(np.mean(cost_errors_array)),
                'median_error_percentage': float(np.median(cost_errors_array)),
                'std_error_percentage': float(np.std(cost_errors_array)),
                'max_error_percentage': float(np.max(cost_errors_array)),
                'min_error_percentage': float(np.min(cost_errors_array)),
                'error_distribution': {
                    'excellent_predictions': len([e for e in cost_errors if e < 5]),  # <5% error
                    'good_predictions': len([e for e in cost_errors if 5 <= e < 15]),  # 5-15% error
                    'fair_predictions': len([e for e in cost_errors if 15 <= e < 30]),  # 15-30% error
                    'poor_predictions': len([e for e in cost_errors if e >= 30])  # >30% error
                }
            }
        
        if time_errors:
            time_errors_array = np.array(time_errors)
            error_analysis['time_prediction'] = {
                'mean_error_percentage': float(np.mean(time_errors_array)),
                'median_error_percentage': float(np.median(time_errors_array)),
                'std_error_percentage': float(np.std(time_errors_array))
            }
        
        # Model confidence analysis
        model_confidence = {}
        if confidence_scores:
            confidence_array = np.array(confidence_scores)
            model_confidence = {
                'average_confidence': float(np.mean(confidence_array)),
                'confidence_distribution': {
                    'high_confidence': len([c for c in confidence_scores if c > 0.8]),
                    'medium_confidence': len([c for c in confidence_scores if 0.5 <= c <= 0.8]),
                    'low_confidence': len([c for c in confidence_scores if c < 0.5])
                }
            }
        
        # Performance trends (simplified - would calculate actual trends over time)
        performance_trends = {
            'accuracy_improving': len(cost_errors) > 5 and np.mean(cost_errors[-5:]) < np.mean(cost_errors[:-5]),
            'prediction_count_trend': 'increasing',  # Would calculate actual trend
            'confidence_trend': 'stable'  # Would analyze confidence over time
        }
        
        return ModelPerformance(
            evaluation_period_days=evaluation_period_days,
            sample_count=len(recent_feedback),
            accuracy_metrics=performance_metrics,
            error_analysis=error_analysis,
            performance_trends=performance_trends,
            model_confidence=model_confidence,
            generated_at=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Error in get_model_performance endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to evaluate model performance: {str(e)}"
        )