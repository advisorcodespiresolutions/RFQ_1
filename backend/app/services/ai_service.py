"""
AI Service for manufacturing analysis and cost prediction
"""

import os
import json
import numpy as np
import cv2
from typing import Dict, List, Any, Optional
from pathlib import Path
import torch
import torch.nn as nn
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
import joblib
import asyncio
from datetime import datetime

from app.core.config import settings
from app.database.models import Part, QuoteFile, PartComplexity, MachiningProcess


class DrawingAnalyzer:
    """Analyzes CAD drawings and technical drawings"""
    
    def __init__(self):
        self.model_path = Path(settings.AI_MODEL_PATH)
        self.confidence_threshold = settings.CONFIDENCE_THRESHOLD
        
    def extract_dimensions(self, image_path: str) -> Dict[str, Any]:
        """Extract dimensions from technical drawings"""
        try:
            # Load image
            image = cv2.imread(image_path)
            if image is None:
                return {"error": "Could not load image"}
            
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Apply edge detection
            edges = cv2.Canny(gray, 50, 150, apertureSize=3)
            
            # Find contours
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Analyze shapes and extract basic dimensions
            dimensions = self._analyze_contours(contours)
            
            # Use OCR to extract text annotations (dimensions)
            text_dimensions = self._extract_text_dimensions(image)
            
            # Combine results
            result = {
                "geometric_dimensions": dimensions,
                "annotated_dimensions": text_dimensions,
                "confidence_score": self._calculate_confidence(dimensions, text_dimensions),
                "processing_time": 0.5  # placeholder
            }
            
            return result
            
        except Exception as e:
            return {"error": f"Dimension extraction failed: {str(e)}"}
    
    def _analyze_contours(self, contours) -> Dict[str, Any]:
        """Analyze contours to extract geometric features"""
        if not contours:
            return {"shapes": [], "total_area": 0}
        
        shapes = []
        total_area = 0
        
        for contour in contours:
            area = cv2.contourArea(contour)
            if area < 100:  # Filter small contours
                continue
                
            # Get bounding rectangle
            x, y, w, h = cv2.boundingRect(contour)
            
            # Calculate basic properties
            perimeter = cv2.arcLength(contour, True)
            aspect_ratio = float(w) / h
            extent = float(area) / (w * h)
            
            # Approximate shape
            epsilon = 0.02 * cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, epsilon, True)
            
            shapes.append({
                "area": area,
                "perimeter": perimeter,
                "width": w,
                "height": h,
                "aspect_ratio": aspect_ratio,
                "extent": extent,
                "vertices": len(approx),
                "shape_type": self._classify_shape(approx, aspect_ratio)
            })
            
            total_area += area
        
        return {
            "shapes": shapes,
            "total_area": total_area,
            "shape_count": len(shapes)
        }
    
    def _extract_text_dimensions(self, image) -> Dict[str, Any]:
        """Extract text-based dimensions using OCR"""
        try:
            import pytesseract
            
            # Extract text
            text = pytesseract.image_to_string(image, config='--psm 6')
            
            # Parse dimension patterns (e.g., "100mm", "2.5"", "Ø25")
            dimensions = self._parse_dimension_text(text)
            
            return {
                "raw_text": text,
                "dimensions": dimensions,
                "units_detected": self._detect_units(text)
            }
            
        except ImportError:
            return {"error": "OCR not available - pytesseract not installed"}
        except Exception as e:
            return {"error": f"OCR failed: {str(e)}"}
    
    def _classify_shape(self, approx, aspect_ratio) -> str:
        """Classify shape based on vertices and aspect ratio"""
        vertices = len(approx)
        
        if vertices == 3:
            return "triangle"
        elif vertices == 4:
            if 0.95 <= aspect_ratio <= 1.05:
                return "square"
            else:
                return "rectangle"
        elif vertices > 8:
            return "circle"
        else:
            return "polygon"
    
    def _parse_dimension_text(self, text: str) -> List[Dict[str, Any]]:
        """Parse dimension values from OCR text"""
        import re
        
        patterns = [
            r'(\d+(?:\.\d+)?)\s*mm',  # millimeters
            r'(\d+(?:\.\d+)?)\s*"',   # inches
            r'Ø\s*(\d+(?:\.\d+)?)',   # diameter
            r'R\s*(\d+(?:\.\d+)?)',   # radius
            r'(\d+(?:\.\d+)?)\s*x\s*(\d+(?:\.\d+)?)',  # dimensions like "10 x 20"
        ]
        
        dimensions = []
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                dimensions.append({
                    "value": match.group(1),
                    "type": self._get_dimension_type(pattern),
                    "position": match.span()
                })
        
        return dimensions
    
    def _get_dimension_type(self, pattern: str) -> str:
        """Determine dimension type from regex pattern"""
        if 'mm' in pattern:
            return "linear_mm"
        elif '"' in pattern:
            return "linear_inch"
        elif 'Ø' in pattern:
            return "diameter"
        elif 'R' in pattern:
            return "radius"
        elif 'x' in pattern:
            return "rectangular"
        return "unknown"
    
    def _detect_units(self, text: str) -> str:
        """Detect measurement units in text"""
        if 'mm' in text.lower():
            return "metric"
        elif '"' in text or 'inch' in text.lower():
            return "imperial"
        return "unknown"
    
    def _calculate_confidence(self, geometric: Dict, text: Dict) -> float:
        """Calculate confidence score for dimension extraction"""
        confidence = 0.5  # Base confidence
        
        # Boost confidence based on successful extractions
        if geometric.get("shapes"):
            confidence += 0.2
        
        if text.get("dimensions"):
            confidence += 0.3
        
        # Penalize for errors
        if geometric.get("error") or text.get("error"):
            confidence -= 0.3
        
        return max(0.0, min(1.0, confidence))


class CostPredictor:
    """Predicts manufacturing costs and cycle times"""
    
    def __init__(self):
        self.models = self._load_models()
        
    def _load_models(self) -> Dict[str, Any]:
        """Load pre-trained cost prediction models"""
        models = {}
        
        try:
            # Load saved models if they exist
            model_dir = Path(settings.AI_MODEL_PATH)
            if model_dir.exists():
                # Try to load existing models
                for model_file in ["cost_model.joblib", "time_model.joblib", "complexity_model.joblib"]:
                    model_path = model_dir / model_file
                    if model_path.exists():
                        models[model_file.split('_')[0]] = joblib.load(model_path)
            
            # Create default models if none exist
            if not models:
                models = self._create_default_models()
                
        except Exception as e:
            print(f"Error loading models: {e}")
            models = self._create_default_models()
        
        return models
    
    def _create_default_models(self) -> Dict[str, Any]:
        """Create default regression models with sample data"""
        # Create simple models with basic features
        models = {
            "cost": RandomForestRegressor(n_estimators=10, random_state=42),
            "time": LinearRegression(),
            "complexity": RandomForestRegressor(n_estimators=5, random_state=42)
        }
        
        # Train with dummy data for demonstration
        X_dummy = np.random.rand(100, 5)  # Features: volume, surface area, complexity, material_type, tolerance
        y_cost = X_dummy[:, 0] * 50 + X_dummy[:, 1] * 20 + np.random.normal(0, 5, 100)  # Cost formula
        y_time = X_dummy[:, 0] * 10 + X_dummy[:, 2] * 15 + np.random.normal(0, 2, 100)  # Time formula
        y_complexity = (X_dummy[:, 0] + X_dummy[:, 1] + X_dummy[:, 2]) / 3  # Complexity score
        
        models["cost"].fit(X_dummy, y_cost)
        models["time"].fit(X_dummy, y_time)
        models["complexity"].fit(X_dummy, y_complexity)
        
        return models
    
    def predict_cost(self, part_features: Dict[str, Any]) -> Dict[str, Any]:
        """Predict manufacturing cost for a part"""
        try:
            # Extract features for prediction
            features = self._extract_cost_features(part_features)
            
            # Make predictions
            cost_prediction = self.models["cost"].predict([features])[0]
            time_prediction = self.models["time"].predict([features])[0]
            complexity_score = self.models["complexity"].predict([features])[0]
            
            # Calculate detailed cost breakdown
            breakdown = self._calculate_cost_breakdown(cost_prediction, part_features)
            
            return {
                "total_cost": max(0, cost_prediction),
                "estimated_time": max(0, time_prediction),
                "complexity_score": min(1.0, max(0, complexity_score)),
                "cost_breakdown": breakdown,
                "confidence": 0.85,  # Default confidence
                "machining_processes": self._recommend_processes(part_features)
            }
            
        except Exception as e:
            return {"error": f"Cost prediction failed: {str(e)}"}
    
    def _extract_cost_features(self, part_features: Dict[str, Any]) -> List[float]:
        """Extract numerical features for cost prediction"""
        # Extract basic geometric features
        dimensions = part_features.get("dimensions", {})
        volume = dimensions.get("volume", 100)  # Default volume
        surface_area = dimensions.get("surface_area", 50)  # Default surface area
        
        # Complexity score based on shape analysis
        complexity = self._calculate_complexity_score(part_features)
        
        # Material factor (simplified)
        material_factor = self._get_material_factor(part_features.get("material", "aluminum"))
        
        # Tolerance factor
        tolerance_factor = self._get_tolerance_factor(part_features.get("tolerances", {}))
        
        return [volume, surface_area, complexity, material_factor, tolerance_factor]
    
    def _calculate_complexity_score(self, part_features: Dict[str, Any]) -> float:
        """Calculate part complexity score"""
        complexity = 0.5  # Base complexity
        
        # Add complexity based on features
        shapes = part_features.get("geometric_dimensions", {}).get("shapes", [])
        if len(shapes) > 3:
            complexity += 0.2
        
        # Check for complex shapes
        for shape in shapes:
            if shape.get("vertices", 4) > 6:
                complexity += 0.1
            if shape.get("aspect_ratio", 1) > 3:
                complexity += 0.1
        
        return min(1.0, complexity)
    
    def _get_material_factor(self, material: str) -> float:
        """Get material difficulty factor"""
        material_factors = {
            "aluminum": 1.0,
            "steel": 1.3,
            "stainless_steel": 1.5,
            "titanium": 2.0,
            "plastic": 0.7,
            "brass": 1.2
        }
        return material_factors.get(material.lower(), 1.0)
    
    def _get_tolerance_factor(self, tolerances: Dict) -> float:
        """Get tolerance difficulty factor"""
        if not tolerances:
            return 1.0
        
        # Simplified tolerance analysis
        tight_tolerances = sum(1 for t in tolerances.values() if isinstance(t, (int, float)) and t < 0.1)
        return 1.0 + (tight_tolerances * 0.2)
    
    def _calculate_cost_breakdown(self, total_cost: float, part_features: Dict) -> Dict[str, float]:
        """Calculate detailed cost breakdown"""
        # Simplified cost breakdown percentages
        material_pct = 0.4
        machining_pct = 0.35
        setup_pct = 0.15
        overhead_pct = 0.1
        
        return {
            "material_cost": total_cost * material_pct,
            "machining_cost": total_cost * machining_pct,
            "setup_cost": total_cost * setup_pct,
            "overhead_cost": total_cost * overhead_pct
        }
    
    def _recommend_processes(self, part_features: Dict) -> List[str]:
        """Recommend machining processes based on part features"""
        processes = ["cnc_milling"]  # Default process
        
        # Add processes based on features
        shapes = part_features.get("geometric_dimensions", {}).get("shapes", [])
        
        for shape in shapes:
            if shape.get("shape_type") == "circle":
                processes.append("cnc_turning")
            elif shape.get("vertices", 4) > 8:
                processes.append("cnc_turning")
        
        # Check for holes
        if any("diameter" in str(d) for d in part_features.get("annotated_dimensions", {}).get("dimensions", [])):
            processes.append("drilling")
        
        return list(set(processes))  # Remove duplicates


class AIService:
    """Main AI service orchestrating all AI functionality"""
    
    def __init__(self):
        self.drawing_analyzer = DrawingAnalyzer()
        self.cost_predictor = CostPredictor()
    
    async def process_file(self, file_record: QuoteFile) -> Dict[str, Any]:
        """Process an uploaded file and extract manufacturing data"""
        try:
            file_path = file_record.file_path
            file_type = file_record.file_type.lower()
            
            result = {
                "file_id": file_record.id,
                "processing_status": "completed",
                "extracted_data": {},
                "confidence_score": 0.0,
                "processing_time": 0.0
            }
            
            start_time = datetime.now()
            
            if file_type in ['.png', '.jpg', '.jpeg', '.pdf']:
                # Process images/PDFs as technical drawings
                analysis_result = self.drawing_analyzer.extract_dimensions(file_path)
                
                if "error" not in analysis_result:
                    result["extracted_data"] = analysis_result
                    result["confidence_score"] = analysis_result.get("confidence_score", 0.0)
                else:
                    result["processing_status"] = "failed"
                    result["error"] = analysis_result["error"]
            
            elif file_type in ['.step', '.stp', '.iges', '.igs', '.dwg']:
                # Process 3D CAD files (placeholder - would need specialized libraries)
                result["extracted_data"] = {
                    "file_type": "3d_cad",
                    "message": "3D CAD analysis not yet implemented",
                    "metadata": {
                        "filename": file_record.original_filename,
                        "size": file_record.file_size
                    }
                }
                result["confidence_score"] = 0.5
            
            else:
                result["processing_status"] = "unsupported"
                result["error"] = f"Unsupported file type: {file_type}"
            
            # Calculate processing time
            end_time = datetime.now()
            result["processing_time"] = (end_time - start_time).total_seconds()
            
            return result
            
        except Exception as e:
            return {
                "file_id": file_record.id,
                "processing_status": "failed",
                "error": str(e),
                "confidence_score": 0.0
            }
    
    async def process_file_async(self, file_id: int):
        """Process file asynchronously"""
        # This would typically use a task queue like Celery
        # For now, just mark as placeholder
        await asyncio.sleep(0.1)  # Simulate async processing
        return {"status": "queued", "file_id": file_id}
    
    async def analyze_quote_parts(self, parts: List[Part]) -> Dict[str, Any]:
        """Analyze all parts in a quote and provide cost estimates"""
        try:
            total_cost = 0.0
            total_time = 0.0
            overall_confidence = 0.0
            parts_analysis = []
            
            for part in parts:
                # Create part features from database data
                part_features = {
                    "dimensions": part.dimensions or {},
                    "material": part.material or "aluminum",
                    "tolerances": part.tolerances or {},
                    "complexity": part.complexity.value if part.complexity else "medium"
                }
                
                # Get cost prediction
                prediction = self.cost_predictor.predict_cost(part_features)
                
                if "error" not in prediction:
                    total_cost += prediction["total_cost"]
                    total_time += prediction["estimated_time"]
                    overall_confidence += prediction["confidence"]
                    
                    parts_analysis.append({
                        "part_id": part.id,
                        "part_name": part.name,
                        "prediction": prediction
                    })
            
            # Calculate averages
            part_count = len(parts)
            if part_count > 0:
                overall_confidence /= part_count
            
            return {
                "overall_confidence": overall_confidence,
                "total_estimated_cost": total_cost,
                "total_estimated_time": total_time,
                "parts_analysis": parts_analysis,
                "recommendations": self._generate_recommendations(parts_analysis),
                "warnings": self._generate_warnings(parts_analysis)
            }
            
        except Exception as e:
            return {"error": f"Quote analysis failed: {str(e)}"}
    
    def _generate_recommendations(self, parts_analysis: List[Dict]) -> List[str]:
        """Generate optimization recommendations"""
        recommendations = []
        
        # Analyze cost patterns
        high_cost_parts = [p for p in parts_analysis 
                          if p.get("prediction", {}).get("total_cost", 0) > 100]
        
        if high_cost_parts:
            recommendations.append(f"Consider reviewing {len(high_cost_parts)} high-cost parts for optimization")
        
        # Check complexity
        complex_parts = [p for p in parts_analysis 
                        if p.get("prediction", {}).get("complexity_score", 0) > 0.8]
        
        if complex_parts:
            recommendations.append(f"Simplify design for {len(complex_parts)} complex parts to reduce costs")
        
        return recommendations
    
    def _generate_warnings(self, parts_analysis: List[Dict]) -> List[str]:
        """Generate warnings for potential issues"""
        warnings = []
        
        # Check for low confidence predictions
        low_confidence = [p for p in parts_analysis 
                         if p.get("prediction", {}).get("confidence", 1.0) < 0.7]
        
        if low_confidence:
            warnings.append(f"Low confidence predictions for {len(low_confidence)} parts - manual review recommended")
        
        return warnings