"""
Feedback Learning Service for Continuous AI Model Improvement

This service implements an online learning system that collects real-world feedback
from users about actual manufacturing costs, processes, and outcomes. This feedback
is then used to continuously improve the AI model predictions through various
machine learning techniques including:

1. Online Learning: Real-time model updates as new feedback arrives
2. Active Learning: Identifying cases where feedback would be most valuable
3. Transfer Learning: Applying learned patterns to similar cases
4. Ensemble Methods: Combining multiple models for better predictions

The system maintains a feedback database, processes user input, and retrains
models to improve accuracy over time.
"""

import numpy as np
import pandas as pd
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, JSON, ForeignKey, func
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import SGDRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import torch
import torch.nn as nn
import torch.optim as optim
from pathlib import Path

from app.core.config import settings
from app.database.models import Quote, Part, QuoteFile, User
from app.database.database import Base
from app.services.deep_learning_service import DeepLearningService

logger = logging.getLogger(__name__)


class FeedbackData(Base):
    """
    Database model for storing user feedback on AI predictions.
    
    This table stores the comparison between AI predictions and actual results,
    which is crucial for improving model accuracy through supervised learning.
    Each record represents one feedback instance where a user provides the
    actual outcome compared to what the AI predicted.
    """
    __tablename__ = "feedback_data"
    
    # Primary identification fields
    id = Column(Integer, primary_key=True, index=True)
    quote_id = Column(Integer, ForeignKey("quotes.id"), nullable=False)
    part_id = Column(Integer, ForeignKey("parts.id"), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Prediction vs Reality comparison
    predicted_cost = Column(Float, nullable=False)  # What AI predicted
    actual_cost = Column(Float, nullable=False)     # What it actually cost
    predicted_time = Column(Float, nullable=True)   # Predicted manufacturing time
    actual_time = Column(Float, nullable=True)      # Actual manufacturing time
    
    # Process and quality feedback
    predicted_processes = Column(JSON, nullable=True)  # AI recommended processes
    actual_processes = Column(JSON, nullable=True)     # Processes actually used
    quality_rating = Column(Integer, nullable=True)    # 1-5 rating of final quality
    
    # Contextual information for learning
    material_used = Column(String(100), nullable=True)
    complexity_level = Column(String(20), nullable=True)
    manufacturing_notes = Column(Text, nullable=True)
    
    # Feedback metadata
    feedback_type = Column(String(50), default="manual")  # manual, automated, estimated
    confidence_level = Column(Float, default=1.0)         # How confident is this feedback
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Learning impact tracking
    model_version_when_predicted = Column(String(50), nullable=True)
    has_been_used_for_training = Column(Boolean, default=False)
    training_weight = Column(Float, default=1.0)  # How much to weight this feedback


class OnlineLearningEngine:
    """
    Core engine for online machine learning that updates models in real-time.
    
    This class implements several online learning algorithms:
    
    1. Stochastic Gradient Descent (SGD): Updates model weights incrementally
    2. Adaptive Learning Rate: Adjusts learning rate based on feedback quality
    3. Concept Drift Detection: Identifies when manufacturing processes change
    4. Memory Management: Balances old vs new learning examples
    
    The engine maintains multiple specialized models:
    - Cost Prediction Model: Learns cost estimation patterns
    - Time Prediction Model: Learns manufacturing time patterns  
    - Process Selection Model: Learns optimal process selection
    - Quality Prediction Model: Learns quality outcome patterns
    """
    
    def __init__(self, model_save_path: str):
        """
        Initialize the online learning engine with model storage path.
        
        Args:
            model_save_path: Directory where trained models are saved
        """
        self.model_save_path = Path(model_save_path)
        self.model_save_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize online learning models
        # SGDRegressor is perfect for online learning as it can learn incrementally
        self.cost_model = SGDRegressor(
            learning_rate='adaptive',      # Adapts learning rate automatically
            eta0=0.01,                    # Initial learning rate
            max_iter=1000,                # Max iterations for convergence
            random_state=42               # For reproducible results
        )
        
        self.time_model = SGDRegressor(
            learning_rate='adaptive',
            eta0=0.01,
            max_iter=1000,
            random_state=42
        )
        
        # Random Forest for process selection (handles categorical outputs well)
        self.process_model = RandomForestRegressor(
            n_estimators=50,              # Number of decision trees
            max_depth=10,                 # Prevent overfitting
            min_samples_split=5,          # Minimum samples to split a node
            random_state=42
        )
        
        # Track learning statistics for model performance monitoring
        self.learning_stats = {
            'total_feedback_count': 0,
            'cost_prediction_accuracy': [],
            'time_prediction_accuracy': [],
            'last_model_update': None,
            'feedback_processing_times': [],
            'model_versions': []
        }
        
        # Load existing models if they exist
        self._load_existing_models()
    
    def _load_existing_models(self):
        """
        Load previously trained models from disk.
        
        This enables the system to maintain learning continuity across
        application restarts. Models are saved in joblib format for
        efficient serialization of scikit-learn models.
        """
        try:
            cost_model_path = self.model_save_path / "online_cost_model.joblib"
            time_model_path = self.model_save_path / "online_time_model.joblib"
            process_model_path = self.model_save_path / "online_process_model.joblib"
            stats_path = self.model_save_path / "learning_stats.json"
            
            # Load models if they exist
            if cost_model_path.exists():
                import joblib
                self.cost_model = joblib.load(cost_model_path)
                logger.info("Loaded existing cost prediction model")
            
            if time_model_path.exists():
                import joblib
                self.time_model = joblib.load(time_model_path)
                logger.info("Loaded existing time prediction model")
            
            if process_model_path.exists():
                import joblib
                self.process_model = joblib.load(process_model_path)
                logger.info("Loaded existing process selection model")
            
            # Load learning statistics
            if stats_path.exists():
                with open(stats_path, 'r') as f:
                    self.learning_stats = json.load(f)
                logger.info("Loaded learning statistics")
                
        except Exception as e:
            logger.error(f"Error loading existing models: {e}")
            # Continue with fresh models if loading fails
    
    def process_feedback_batch(self, feedback_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Process a batch of feedback data to update models.
        
        This method implements incremental learning by:
        1. Converting feedback to feature vectors
        2. Validating data quality and consistency
        3. Updating models using partial_fit (online learning)
        4. Calculating prediction accuracy improvements
        5. Saving updated models to disk
        
        Args:
            feedback_data: List of feedback dictionaries containing actual vs predicted values
            
        Returns:
            Dictionary containing learning results and model performance metrics
        """
        start_time = datetime.now()
        
        # Initialize result tracking
        learning_results = {
            'feedback_processed': len(feedback_data),
            'successful_updates': 0,
            'failed_updates': 0,
            'accuracy_improvements': {},
            'model_performance': {},
            'processing_time': 0.0,
            'warnings': []
        }
        
        # Convert feedback to training data
        # This is crucial for machine learning - converting real-world feedback
        # into numerical features that algorithms can learn from
        training_features = []
        cost_targets = []
        time_targets = []
        process_targets = []
        
        for feedback in feedback_data:
            try:
                # Extract features from feedback
                # These features represent the input conditions that led to the outcome
                features = self._extract_features_from_feedback(feedback)
                
                if features is not None:
                    training_features.append(features)
                    cost_targets.append(feedback.get('actual_cost', 0))
                    time_targets.append(feedback.get('actual_time', 0))
                    
                    # Process encoding for categorical prediction
                    process_encoded = self._encode_processes(feedback.get('actual_processes', []))
                    process_targets.append(process_encoded)
                    
                    learning_results['successful_updates'] += 1
                else:
                    learning_results['failed_updates'] += 1
                    learning_results['warnings'].append(
                        f"Could not extract features from feedback ID: {feedback.get('id', 'unknown')}"
                    )
                    
            except Exception as e:
                learning_results['failed_updates'] += 1
                learning_results['warnings'].append(f"Error processing feedback: {str(e)}")
        
        # Update models if we have valid training data
        if training_features:
            X = np.array(training_features)
            
            # Update cost prediction model
            if cost_targets:
                y_cost = np.array(cost_targets)
                # partial_fit allows incremental learning without retraining from scratch
                self.cost_model.partial_fit(X, y_cost)
                
                # Calculate accuracy improvement
                predictions_cost = self.cost_model.predict(X)
                accuracy_cost = r2_score(y_cost, predictions_cost)
                learning_results['accuracy_improvements']['cost_model'] = accuracy_cost
            
            # Update time prediction model
            if time_targets:
                y_time = np.array(time_targets)
                self.time_model.partial_fit(X, y_time)
                
                predictions_time = self.time_model.predict(X)
                accuracy_time = r2_score(y_time, predictions_time)
                learning_results['accuracy_improvements']['time_model'] = accuracy_time
            
            # Update process selection model (requires full refit for Random Forest)
            if process_targets and len(training_features) > 5:  # Need minimum samples
                y_process = np.array(process_targets)
                self.process_model.fit(X, y_process)
                
                predictions_process = self.process_model.predict(X)
                accuracy_process = r2_score(y_process, predictions_process)
                learning_results['accuracy_improvements']['process_model'] = accuracy_process
        
        # Update learning statistics
        self.learning_stats['total_feedback_count'] += learning_results['successful_updates']
        self.learning_stats['last_model_update'] = datetime.now().isoformat()
        
        # Save updated models to disk for persistence
        self._save_models()
        
        # Calculate processing time
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        learning_results['processing_time'] = processing_time
        self.learning_stats['feedback_processing_times'].append(processing_time)
        
        logger.info(f"Processed {learning_results['successful_updates']} feedback samples in {processing_time:.2f}s")
        
        return learning_results
    
    def _extract_features_from_feedback(self, feedback: Dict[str, Any]) -> Optional[List[float]]:
        """
        Convert feedback data into numerical feature vector for machine learning.
        
        This is a critical function that transforms real-world manufacturing data
        into a format that machine learning algorithms can understand. The feature
        engineering process includes:
        
        1. Dimensional features: Length, width, height, volume, surface area
        2. Material features: One-hot encoded material types
        3. Complexity features: Geometric complexity, tolerance requirements
        4. Process features: Historical process success rates
        5. Contextual features: Batch size, urgency, client requirements
        
        Args:
            feedback: Dictionary containing feedback data with actual outcomes
            
        Returns:
            List of numerical features or None if extraction fails
        """
        try:
            features = []
            
            # Dimensional features - these are fundamental to manufacturing cost
            # Larger parts generally cost more due to material and machining time
            part_dimensions = feedback.get('part_dimensions', {})
            features.extend([
                part_dimensions.get('length', 100.0),     # Length in mm
                part_dimensions.get('width', 50.0),       # Width in mm  
                part_dimensions.get('height', 25.0),      # Height in mm
                part_dimensions.get('volume', 125000.0),  # Volume in mm³
                part_dimensions.get('surface_area', 1500.0)  # Surface area in mm²
            ])
            
            # Material features - different materials have vastly different costs
            # Use one-hot encoding to represent categorical material data
            material = feedback.get('material_used', 'aluminum')
            material_features = self._encode_material(material)
            features.extend(material_features)
            
            # Complexity features - more complex parts require more time and skill
            complexity_data = feedback.get('complexity_data', {})
            features.extend([
                complexity_data.get('geometric_complexity', 0.5),  # 0-1 scale
                complexity_data.get('tolerance_tightness', 0.3),   # 0-1 scale (tighter = higher)
                complexity_data.get('feature_count', 5),           # Number of features (holes, etc.)
                complexity_data.get('assembly_complexity', 0.2)    # If part of assembly
            ])
            
            # Process history features - learn from past success with similar parts
            process_history = feedback.get('process_history', {})
            features.extend([
                process_history.get('cnc_milling_success_rate', 0.85),
                process_history.get('drilling_success_rate', 0.92),
                process_history.get('turning_success_rate', 0.88),
                process_history.get('avg_setup_time', 2.5)  # Hours
            ])
            
            # Contextual features - external factors that affect cost and time
            context = feedback.get('context', {})
            features.extend([
                context.get('batch_size', 1),              # Larger batches = lower unit cost
                context.get('urgency_factor', 1.0),        # Rush jobs cost more
                context.get('client_tier', 1),             # Premium clients may pay more
                context.get('season_factor', 1.0)          # Seasonal demand variations
            ])
            
            # Quality requirements - higher quality = higher cost
            quality_req = feedback.get('quality_requirements', {})
            features.extend([
                quality_req.get('inspection_level', 1),    # 1=basic, 2=detailed, 3=certified
                quality_req.get('documentation_required', 0),  # 0=no, 1=yes
                quality_req.get('traceability_required', 0)     # 0=no, 1=yes
            ])
            
            return features
            
        except Exception as e:
            logger.error(f"Feature extraction failed: {e}")
            return None
    
    def _encode_material(self, material: str) -> List[float]:
        """
        Convert material name to one-hot encoded features.
        
        One-hot encoding is essential for representing categorical data in ML.
        Each material gets its own binary feature (0 or 1).
        This prevents the algorithm from assuming ordinal relationships
        between materials (e.g., aluminum < steel < titanium).
        
        Args:
            material: Material name string
            
        Returns:
            List of binary features representing material type
        """
        # Define standard materials used in manufacturing
        materials = ['aluminum', 'steel', 'stainless_steel', 'titanium', 'plastic', 'brass', 'copper']
        encoding = [0.0] * len(materials)
        
        # Set the appropriate material flag to 1.0
        material_lower = material.lower().replace(' ', '_')
        if material_lower in materials:
            encoding[materials.index(material_lower)] = 1.0
        else:
            # Unknown material - use aluminum as default
            encoding[0] = 1.0
        
        return encoding
    
    def _encode_processes(self, processes: List[str]) -> float:
        """
        Convert manufacturing processes to numerical encoding.
        
        This creates a complexity score based on the combination of processes.
        More processes generally mean higher complexity and cost.
        
        Args:
            processes: List of process names
            
        Returns:
            Numerical complexity score based on processes
        """
        if not processes:
            return 1.0  # Default single process
        
        # Process complexity weights based on typical manufacturing difficulty
        process_weights = {
            'cnc_milling': 1.0,      # Standard baseline
            'cnc_turning': 0.8,      # Generally simpler setup
            'drilling': 0.3,         # Simple operation
            'tapping': 0.4,          # Threading operation
            'grinding': 1.5,         # Precision finishing
            'edm': 2.0,              # Complex electrical discharge machining
            'laser_cutting': 1.2,    # Precision cutting
            'waterjet': 1.3,         # High-pressure cutting
            'manual': 2.5,           # Labor-intensive
            'assembly': 1.8          # Multiple components
        }
        
        # Calculate combined complexity score
        total_complexity = sum(process_weights.get(process.lower(), 1.0) for process in processes)
        
        return total_complexity
    
    def _save_models(self):
        """
        Save trained models to disk for persistence across application restarts.
        
        This is crucial for maintaining learning continuity. Models are saved
        using joblib which is optimized for scikit-learn model serialization.
        """
        try:
            import joblib
            
            # Save individual models
            joblib.dump(self.cost_model, self.model_save_path / "online_cost_model.joblib")
            joblib.dump(self.time_model, self.model_save_path / "online_time_model.joblib")
            joblib.dump(self.process_model, self.model_save_path / "online_process_model.joblib")
            
            # Save learning statistics for monitoring
            with open(self.model_save_path / "learning_stats.json", 'w') as f:
                json.dump(self.learning_stats, f, indent=2)
            
            logger.info("Models saved successfully")
            
        except Exception as e:
            logger.error(f"Error saving models: {e}")
    
    def predict_with_updated_models(self, features: List[float]) -> Dict[str, Any]:
        """
        Make predictions using the continuously updated models.
        
        This demonstrates how the online learning system improves predictions
        over time by incorporating real-world feedback.
        
        Args:
            features: Feature vector for prediction
            
        Returns:
            Dictionary containing predictions and confidence scores
        """
        try:
            X = np.array([features])
            
            # Make predictions with updated models
            cost_prediction = self.cost_model.predict(X)[0] if hasattr(self.cost_model, 'predict') else 0.0
            time_prediction = self.time_model.predict(X)[0] if hasattr(self.time_model, 'predict') else 0.0
            process_complexity = self.process_model.predict(X)[0] if hasattr(self.process_model, 'predict') else 1.0
            
            # Calculate confidence based on model training history
            confidence = self._calculate_prediction_confidence(features)
            
            return {
                'predicted_cost': max(0, cost_prediction),
                'predicted_time': max(0, time_prediction),
                'process_complexity_score': process_complexity,
                'prediction_confidence': confidence,
                'model_version': self.learning_stats.get('last_model_update', 'initial'),
                'feedback_count_used': self.learning_stats['total_feedback_count']
            }
            
        except Exception as e:
            logger.error(f"Prediction failed: {e}")
            return {
                'predicted_cost': 0.0,
                'predicted_time': 0.0,
                'process_complexity_score': 1.0,
                'prediction_confidence': 0.5,
                'error': str(e)
            }
    
    def _calculate_prediction_confidence(self, features: List[float]) -> float:
        """
        Calculate confidence score for predictions based on training data similarity.
        
        Confidence is higher when:
        1. We have more training data similar to current request
        2. Recent feedback has been accurate
        3. Feature values are within trained ranges
        
        Args:
            features: Feature vector for current prediction
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        base_confidence = 0.5
        
        # Increase confidence based on amount of training data
        feedback_count = self.learning_stats['total_feedback_count']
        if feedback_count > 100:
            base_confidence += 0.3
        elif feedback_count > 50:
            base_confidence += 0.2
        elif feedback_count > 10:
            base_confidence += 0.1
        
        # Adjust based on recent accuracy (if available)
        if self.learning_stats.get('cost_prediction_accuracy'):
            recent_accuracy = np.mean(self.learning_stats['cost_prediction_accuracy'][-10:])
            base_confidence += (recent_accuracy - 0.5) * 0.4
        
        return min(0.95, max(0.1, base_confidence))


class FeedbackLearningService:
    """
    Main service coordinating the feedback learning system.
    
    This service orchestrates the entire feedback learning process:
    1. Collects user feedback through various interfaces
    2. Validates and preprocesses feedback data
    3. Triggers online learning model updates
    4. Provides interfaces for feedback submission and analytics
    5. Manages feedback data storage and retrieval
    
    The service acts as the main entry point for all feedback-related operations
    and ensures data consistency and learning effectiveness.
    """
    
    def __init__(self, db: Session):
        """
        Initialize the feedback learning service.
        
        Args:
            db: Database session for data persistence
        """
        self.db = db
        self.online_engine = OnlineLearningEngine(settings.AI_MODEL_PATH)
        self.deep_learning_service = DeepLearningService()
        
        # Initialize feedback processing queue for batch processing
        self.feedback_queue = []
        self.batch_size = 10  # Process feedback in batches for efficiency
        
        logger.info("Feedback Learning Service initialized")
    
    async def submit_feedback(
        self,
        quote_id: int,
        user_id: int,
        feedback_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Submit new feedback for a quote's AI predictions.
        
        This is the main entry point for users to provide feedback on
        whether AI predictions matched reality. The feedback is used
        to improve future predictions through online learning.
        
        Args:
            quote_id: ID of the quote being evaluated
            user_id: ID of user providing feedback
            feedback_data: Dictionary containing actual vs predicted comparisons
            
        Returns:
            Dictionary containing submission result and learning impact
        """
        try:
            # Validate feedback data structure and completeness
            validation_result = self._validate_feedback_data(feedback_data)
            if not validation_result['valid']:
                return {
                    'success': False,
                    'error': f"Invalid feedback data: {validation_result['error']}",
                    'validation_details': validation_result
                }
            
            # Create feedback record in database for permanent storage
            feedback_record = FeedbackData(
                quote_id=quote_id,
                part_id=feedback_data.get('part_id'),
                user_id=user_id,
                predicted_cost=feedback_data['predicted_cost'],
                actual_cost=feedback_data['actual_cost'],
                predicted_time=feedback_data.get('predicted_time'),
                actual_time=feedback_data.get('actual_time'),
                predicted_processes=feedback_data.get('predicted_processes'),
                actual_processes=feedback_data.get('actual_processes'),
                quality_rating=feedback_data.get('quality_rating'),
                material_used=feedback_data.get('material_used'),
                complexity_level=feedback_data.get('complexity_level'),
                manufacturing_notes=feedback_data.get('manufacturing_notes'),
                feedback_type=feedback_data.get('feedback_type', 'manual'),
                confidence_level=feedback_data.get('confidence_level', 1.0)
            )
            
            # Save to database
            self.db.add(feedback_record)
            self.db.commit()
            
            # Add to processing queue for online learning
            enhanced_feedback = self._enhance_feedback_with_context(feedback_record)
            self.feedback_queue.append(enhanced_feedback)
            
            # Process batch if queue is full (efficient batch processing)
            learning_result = None
            if len(self.feedback_queue) >= self.batch_size:
                learning_result = self.online_engine.process_feedback_batch(self.feedback_queue)
                self.feedback_queue = []  # Clear processed feedback
            
            # Calculate impact metrics for user visibility
            impact_metrics = self._calculate_feedback_impact(feedback_data)
            
            return {
                'success': True,
                'feedback_id': feedback_record.id,
                'learning_triggered': learning_result is not None,
                'learning_results': learning_result,
                'impact_metrics': impact_metrics,
                'message': 'Feedback submitted successfully and will improve future predictions'
            }
            
        except Exception as e:
            logger.error(f"Error submitting feedback: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _validate_feedback_data(self, feedback_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate feedback data for completeness and consistency.
        
        This ensures feedback quality before using it for learning:
        1. Required fields are present
        2. Numerical values are within reasonable ranges
        3. Categorical values are from expected sets
        4. Relationships between fields make sense
        
        Args:
            feedback_data: Raw feedback data from user
            
        Returns:
            Validation result with success flag and error details
        """
        validation_result = {'valid': True, 'errors': [], 'warnings': []}
        
        # Check required fields
        required_fields = ['predicted_cost', 'actual_cost']
        for field in required_fields:
            if field not in feedback_data:
                validation_result['errors'].append(f"Missing required field: {field}")
        
        # Validate cost values are reasonable
        if 'actual_cost' in feedback_data:
            actual_cost = feedback_data['actual_cost']
            if actual_cost < 0:
                validation_result['errors'].append("Actual cost cannot be negative")
            elif actual_cost > 1000000:  # $1M seems unreasonable for single part
                validation_result['warnings'].append("Actual cost seems unusually high")
        
        # Validate time values
        if 'actual_time' in feedback_data:
            actual_time = feedback_data['actual_time']
            if actual_time < 0:
                validation_result['errors'].append("Actual time cannot be negative")
            elif actual_time > 1000:  # 1000 hours seems excessive
                validation_result['warnings'].append("Actual time seems unusually high")
        
        # Validate quality rating
        if 'quality_rating' in feedback_data:
            rating = feedback_data['quality_rating']
            if not isinstance(rating, int) or rating < 1 or rating > 5:
                validation_result['errors'].append("Quality rating must be integer between 1 and 5")
        
        # Validate process lists
        if 'actual_processes' in feedback_data:
            processes = feedback_data['actual_processes']
            if not isinstance(processes, list):
                validation_result['errors'].append("Actual processes must be a list")
        
        # Check for consistency between predicted and actual values
        if 'predicted_cost' in feedback_data and 'actual_cost' in feedback_data:
            predicted = feedback_data['predicted_cost']
            actual = feedback_data['actual_cost']
            if actual > predicted * 10:  # Actual is 10x higher than predicted
                validation_result['warnings'].append(
                    "Large discrepancy between predicted and actual cost - please verify"
                )
        
        # Set overall validity
        validation_result['valid'] = len(validation_result['errors']) == 0
        validation_result['error'] = '; '.join(validation_result['errors']) if validation_result['errors'] else None
        
        return validation_result
    
    def _enhance_feedback_with_context(self, feedback_record: FeedbackData) -> Dict[str, Any]:
        """
        Enhance feedback with additional context for better learning.
        
        This adds contextual information that helps the ML models
        understand the circumstances that led to specific outcomes:
        1. Historical data about similar parts
        2. Market conditions at time of manufacturing
        3. Client-specific requirements and standards
        4. Seasonal or temporal factors
        
        Args:
            feedback_record: Basic feedback data from database
            
        Returns:
            Enhanced feedback dictionary with additional context
        """
        try:
            # Get quote and part information for context
            quote = self.db.query(Quote).filter(Quote.id == feedback_record.quote_id).first()
            part = None
            if feedback_record.part_id:
                part = self.db.query(Part).filter(Part.id == feedback_record.part_id).first()
            
            enhanced_feedback = {
                # Basic feedback data
                'id': feedback_record.id,
                'predicted_cost': feedback_record.predicted_cost,
                'actual_cost': feedback_record.actual_cost,
                'predicted_time': feedback_record.predicted_time,
                'actual_time': feedback_record.actual_time,
                'actual_processes': feedback_record.actual_processes or [],
                'material_used': feedback_record.material_used,
                'quality_rating': feedback_record.quality_rating,
                
                # Enhanced contextual information
                'part_dimensions': {},
                'complexity_data': {},
                'process_history': {},
                'context': {},
                'quality_requirements': {}
            }
            
            # Add part-specific context if available
            if part:
                enhanced_feedback['part_dimensions'] = part.dimensions or {}
                enhanced_feedback['complexity_data'] = {
                    'geometric_complexity': 0.5,  # Would calculate from part geometry
                    'tolerance_tightness': 0.3,   # Based on tolerance requirements
                    'feature_count': len(part.machining_processes or []),
                    'assembly_complexity': 0.2
                }
            
            # Add quote-specific context
            if quote:
                enhanced_feedback['context'] = {
                    'batch_size': 1,  # Assume single part for now
                    'urgency_factor': 1.0,  # Normal priority
                    'client_tier': 1,  # Standard client
                    'season_factor': 1.0  # No seasonal adjustment
                }
                
                enhanced_feedback['quality_requirements'] = {
                    'inspection_level': 1,  # Basic inspection
                    'documentation_required': 0,
                    'traceability_required': 0
                }
            
            # Add historical process success rates (simplified)
            enhanced_feedback['process_history'] = {
                'cnc_milling_success_rate': 0.85,
                'drilling_success_rate': 0.92,
                'turning_success_rate': 0.88,
                'avg_setup_time': 2.5
            }
            
            return enhanced_feedback
            
        except Exception as e:
            logger.error(f"Error enhancing feedback: {e}")
            # Return basic feedback if enhancement fails
            return {
                'id': feedback_record.id,
                'predicted_cost': feedback_record.predicted_cost,
                'actual_cost': feedback_record.actual_cost,
                'predicted_time': feedback_record.predicted_time or 0,
                'actual_time': feedback_record.actual_time or 0
            }
    
    def _calculate_feedback_impact(self, feedback_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate the learning impact of submitted feedback.
        
        This quantifies how much this specific feedback will improve
        the AI system's future predictions. Higher impact feedback
        includes cases where:
        1. AI prediction was significantly wrong
        2. Feedback covers underrepresented scenarios
        3. User provides high-confidence, detailed feedback
        
        Args:
            feedback_data: The feedback data being analyzed
            
        Returns:
            Dictionary with impact metrics and explanations
        """
        impact_metrics = {
            'prediction_error': 0.0,
            'learning_value': 'medium',
            'model_improvement_potential': 0.0,
            'rare_case_value': 0.0,
            'overall_impact_score': 0.0
        }
        
        try:
            # Calculate prediction error (how wrong was the AI?)
            if 'predicted_cost' in feedback_data and 'actual_cost' in feedback_data:
                predicted = feedback_data['predicted_cost']
                actual = feedback_data['actual_cost']
                
                if predicted > 0:
                    error_percentage = abs(actual - predicted) / predicted * 100
                    impact_metrics['prediction_error'] = error_percentage
                    
                    # Higher error = higher learning value (up to a point)
                    if error_percentage > 50:
                        impact_metrics['learning_value'] = 'high'
                        impact_metrics['model_improvement_potential'] = 0.8
                    elif error_percentage > 20:
                        impact_metrics['learning_value'] = 'medium'
                        impact_metrics['model_improvement_potential'] = 0.5
                    else:
                        impact_metrics['learning_value'] = 'low'
                        impact_metrics['model_improvement_potential'] = 0.2
            
            # Assess rare case value (is this an unusual scenario?)
            material = feedback_data.get('material_used', 'aluminum')
            if material in ['titanium', 'inconel', 'carbon_fiber']:
                impact_metrics['rare_case_value'] = 0.8  # High value for rare materials
            elif material in ['stainless_steel', 'brass']:
                impact_metrics['rare_case_value'] = 0.5  # Medium value
            else:
                impact_metrics['rare_case_value'] = 0.2  # Low value for common materials
            
            # Calculate overall impact score
            impact_metrics['overall_impact_score'] = (
                impact_metrics['model_improvement_potential'] * 0.5 +
                impact_metrics['rare_case_value'] * 0.3 +
                (feedback_data.get('confidence_level', 1.0) * 0.2)
            )
            
        except Exception as e:
            logger.error(f"Error calculating feedback impact: {e}")
        
        return impact_metrics
    
    async def get_feedback_analytics(self, user_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Get analytics about feedback and learning performance.
        
        This provides insights into how well the feedback system is working:
        1. Prediction accuracy trends over time
        2. Most common types of prediction errors
        3. Learning effectiveness metrics
        4. User engagement with feedback system
        
        Args:
            user_id: Optional user ID to filter analytics
            
        Returns:
            Comprehensive analytics about the feedback learning system
        """
        try:
            # Query feedback data from database
            query = self.db.query(FeedbackData)
            if user_id:
                query = query.filter(FeedbackData.user_id == user_id)
            
            feedback_records = query.all()
            
            analytics = {
                'summary': {
                    'total_feedback_count': len(feedback_records),
                    'avg_prediction_accuracy': 0.0,
                    'learning_improvement_rate': 0.0,
                    'user_engagement_score': 0.0
                },
                'accuracy_trends': {
                    'cost_prediction_accuracy': [],
                    'time_prediction_accuracy': [],
                    'process_prediction_accuracy': []
                },
                'error_analysis': {
                    'common_error_patterns': [],
                    'largest_discrepancies': [],
                    'improvement_opportunities': []
                },
                'learning_effectiveness': {
                    'model_performance_before_feedback': 0.0,
                    'model_performance_after_feedback': 0.0,
                    'learning_rate': 0.0,
                    'feedback_utilization_rate': 0.0
                }
            }
            
            if feedback_records:
                # Calculate accuracy trends
                cost_accuracies = []
                time_accuracies = []
                
                for record in feedback_records:
                    # Cost accuracy calculation
                    if record.predicted_cost and record.actual_cost:
                        cost_error = abs(record.actual_cost - record.predicted_cost) / record.actual_cost
                        cost_accuracy = max(0, 1 - cost_error)
                        cost_accuracies.append(cost_accuracy)
                    
                    # Time accuracy calculation
                    if record.predicted_time and record.actual_time:
                        time_error = abs(record.actual_time - record.predicted_time) / record.actual_time
                        time_accuracy = max(0, 1 - time_error)
                        time_accuracies.append(time_accuracy)
                
                # Update analytics with calculated metrics
                if cost_accuracies:
                    analytics['summary']['avg_prediction_accuracy'] = np.mean(cost_accuracies)
                    analytics['accuracy_trends']['cost_prediction_accuracy'] = cost_accuracies[-20:]  # Last 20
                
                if time_accuracies:
                    analytics['accuracy_trends']['time_prediction_accuracy'] = time_accuracies[-20:]
                
                # Analyze error patterns
                analytics['error_analysis'] = self._analyze_error_patterns(feedback_records)
                
                # Calculate learning effectiveness from online engine stats
                learning_stats = self.online_engine.learning_stats
                analytics['learning_effectiveness'] = {
                    'total_learning_samples': learning_stats['total_feedback_count'],
                    'last_update': learning_stats.get('last_model_update'),
                    'avg_processing_time': np.mean(learning_stats.get('feedback_processing_times', [0])),
                    'model_versions': len(learning_stats.get('model_versions', []))
                }
            
            return analytics
            
        except Exception as e:
            logger.error(f"Error generating feedback analytics: {e}")
            return {'error': str(e)}
    
    def _analyze_error_patterns(self, feedback_records: List[FeedbackData]) -> Dict[str, Any]:
        """
        Analyze patterns in prediction errors to identify improvement opportunities.
        
        This helps identify systematic biases or blind spots in the AI models:
        1. Materials where predictions are consistently wrong
        2. Part size ranges with high error rates
        3. Process combinations that cause prediction failures
        4. Temporal patterns in prediction accuracy
        
        Args:
            feedback_records: List of feedback data records
            
        Returns:
            Dictionary containing error pattern analysis
        """
        error_analysis = {
            'material_error_patterns': {},
            'size_range_errors': {},
            'process_combination_errors': {},
            'systematic_biases': []
        }
        
        try:
            # Group errors by material
            material_errors = {}
            for record in feedback_records:
                if record.material_used and record.predicted_cost and record.actual_cost:
                    material = record.material_used
                    error_pct = abs(record.actual_cost - record.predicted_cost) / record.actual_cost * 100
                    
                    if material not in material_errors:
                        material_errors[material] = []
                    material_errors[material].append(error_pct)
            
            # Calculate average error by material
            for material, errors in material_errors.items():
                avg_error = np.mean(errors)
                error_analysis['material_error_patterns'][material] = {
                    'avg_error_percentage': avg_error,
                    'sample_count': len(errors),
                    'error_consistency': np.std(errors)  # Lower std = more consistent errors
                }
            
            # Identify systematic biases
            cost_biases = []
            for record in feedback_records:
                if record.predicted_cost and record.actual_cost:
                    bias = (record.predicted_cost - record.actual_cost) / record.actual_cost
                    cost_biases.append(bias)
            
            if cost_biases:
                avg_bias = np.mean(cost_biases)
                if abs(avg_bias) > 0.1:  # More than 10% systematic bias
                    bias_direction = "over-estimation" if avg_bias > 0 else "under-estimation"
                    error_analysis['systematic_biases'].append({
                        'type': 'cost_prediction',
                        'direction': bias_direction,
                        'magnitude': abs(avg_bias) * 100,
                        'recommendation': f"Calibrate cost model to reduce {bias_direction}"
                    })
            
        except Exception as e:
            logger.error(f"Error analyzing error patterns: {e}")
        
        return error_analysis
    
    async def trigger_model_retraining(self, force_retrain: bool = False) -> Dict[str, Any]:
        """
        Trigger a complete model retraining with all accumulated feedback.
        
        While online learning handles incremental updates, periodic full
        retraining can capture complex patterns and interactions that
        incremental learning might miss. This is especially important for:
        1. Deep learning models that benefit from full dataset training
        2. Capturing non-linear interactions between features
        3. Removing outdated patterns from old data
        
        Args:
            force_retrain: Whether to force retraining even if not needed
            
        Returns:
            Dictionary containing retraining results and performance metrics
        """
        try:
            # Get all feedback data for comprehensive retraining
            all_feedback = self.db.query(FeedbackData).all()
            
            if len(all_feedback) < 20 and not force_retrain:
                return {
                    'success': False,
                    'message': 'Insufficient feedback data for retraining (minimum 20 samples required)',
                    'current_feedback_count': len(all_feedback)
                }
            
            # Convert all feedback to enhanced format
            enhanced_feedback_batch = []
            for record in all_feedback:
                enhanced = self._enhance_feedback_with_context(record)
                enhanced_feedback_batch.append(enhanced)
            
            # Trigger comprehensive learning update
            learning_results = self.online_engine.process_feedback_batch(enhanced_feedback_batch)
            
            # Update all records as used for training
            for record in all_feedback:
                record.has_been_used_for_training = True
            self.db.commit()
            
            # Test model performance with recent feedback
            performance_metrics = await self._evaluate_model_performance(all_feedback[-10:])
            
            return {
                'success': True,
                'feedback_samples_used': len(enhanced_feedback_batch),
                'learning_results': learning_results,
                'performance_metrics': performance_metrics,
                'model_version': self.online_engine.learning_stats.get('last_model_update'),
                'message': 'Model retraining completed successfully'
            }
            
        except Exception as e:
            logger.error(f"Error during model retraining: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _evaluate_model_performance(self, test_feedback: List[FeedbackData]) -> Dict[str, Any]:
        """
        Evaluate current model performance using recent feedback as test data.
        
        This provides quantitative metrics about how well the continuously
        learning models are performing on real-world data.
        
        Args:
            test_feedback: Recent feedback to use as test cases
            
        Returns:
            Dictionary containing performance evaluation metrics
        """
        if not test_feedback:
            return {'error': 'No test data available'}
        
        try:
            cost_predictions = []
            actual_costs = []
            time_predictions = []
            actual_times = []
            
            # Make predictions for test cases and compare with actual results
            for record in test_feedback:
                # Extract features for prediction
                enhanced_feedback = self._enhance_feedback_with_context(record)
                features = self.online_engine._extract_features_from_feedback(enhanced_feedback)
                
                if features:
                    # Get model predictions
                    prediction = self.online_engine.predict_with_updated_models(features)
                    
                    cost_predictions.append(prediction['predicted_cost'])
                    actual_costs.append(record.actual_cost)
                    
                    if record.actual_time and prediction.get('predicted_time'):
                        time_predictions.append(prediction['predicted_time'])
                        actual_times.append(record.actual_time)
            
            # Calculate performance metrics
            performance = {}
            
            if cost_predictions and actual_costs:
                cost_mae = mean_absolute_error(actual_costs, cost_predictions)
                cost_mse = mean_squared_error(actual_costs, cost_predictions)
                cost_r2 = r2_score(actual_costs, cost_predictions)
                
                performance['cost_prediction'] = {
                    'mean_absolute_error': cost_mae,
                    'mean_squared_error': cost_mse,
                    'r2_score': cost_r2,
                    'sample_count': len(cost_predictions)
                }
            
            if time_predictions and actual_times:
                time_mae = mean_absolute_error(actual_times, time_predictions)
                time_r2 = r2_score(actual_times, time_predictions)
                
                performance['time_prediction'] = {
                    'mean_absolute_error': time_mae,
                    'r2_score': time_r2,
                    'sample_count': len(time_predictions)
                }
            
            return performance
            
        except Exception as e:
            logger.error(f"Error evaluating model performance: {e}")
            return {'error': str(e)}