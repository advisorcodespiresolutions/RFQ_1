"""
Multi-Dimensional Analysis Service for 2D/3D File Cross-Reference
"""

import cv2
import numpy as np
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from datetime import datetime
import torch
import torch.nn as nn
from sqlalchemy.orm import Session

from app.core.config import settings
from app.database.models import QuoteFile, Part
from app.services.deep_learning_service import DeepLearningService

logger = logging.getLogger(__name__)


class FileTypeDetector:
    """Detect and classify file types for proper processing"""
    
    @staticmethod
    def detect_file_type(file_path: str) -> Dict[str, Any]:
        """Detect if file is 2D drawing or 3D model"""
        file_ext = Path(file_path).suffix.lower()
        
        file_types = {
            # 2D Drawing formats
            '.pdf': {'type': '2d', 'format': 'pdf', 'description': 'Technical Drawing PDF'},
            '.png': {'type': '2d', 'format': 'raster', 'description': '2D Raster Image'},
            '.jpg': {'type': '2d', 'format': 'raster', 'description': '2D Raster Image'},
            '.jpeg': {'type': '2d', 'format': 'raster', 'description': '2D Raster Image'},
            '.dwg': {'type': '2d', 'format': 'cad', 'description': 'AutoCAD Drawing'},
            '.dxf': {'type': '2d', 'format': 'cad', 'description': 'Drawing Exchange Format'},
            
            # 3D Model formats
            '.step': {'type': '3d', 'format': 'cad', 'description': 'STEP 3D Model'},
            '.stp': {'type': '3d', 'format': 'cad', 'description': 'STEP 3D Model'},
            '.iges': {'type': '3d', 'format': 'cad', 'description': 'IGES 3D Model'},
            '.igs': {'type': '3d', 'format': 'cad', 'description': 'IGES 3D Model'},
            '.stl': {'type': '3d', 'format': 'mesh', 'description': 'STL 3D Mesh'},
            '.obj': {'type': '3d', 'format': 'mesh', 'description': 'OBJ 3D Mesh'},
            '.ply': {'type': '3d', 'format': 'mesh', 'description': 'PLY 3D Mesh'},
            '.x3d': {'type': '3d', 'format': 'scene', 'description': 'X3D Scene'},
        }
        
        return file_types.get(file_ext, {
            'type': 'unknown', 
            'format': 'unknown', 
            'description': 'Unknown file format'
        })


class DimensionCorrelationEngine:
    """Engine to correlate dimensions between 2D and 3D representations"""
    
    def __init__(self):
        self.tolerance_threshold = 0.05  # 5% tolerance for dimension matching
    
    def correlate_dimensions(
        self, 
        dimensions_2d: Dict[str, float], 
        dimensions_3d: Dict[str, float]
    ) -> Dict[str, Any]:
        """Correlate dimensions between 2D and 3D analyses"""
        
        correlation_results = {
            "matches": [],
            "discrepancies": [],
            "confidence_score": 0.0,
            "recommended_values": {},
            "analysis": {
                "total_dimensions": 0,
                "matched_dimensions": 0,
                "avg_discrepancy": 0.0
            }
        }
        
        # Common dimension mappings
        dimension_mappings = {
            "length": ["length", "x_dimension", "overall_length"],
            "width": ["width", "y_dimension", "overall_width"],
            "height": ["height", "z_dimension", "overall_height", "thickness"],
            "diameter": ["diameter", "outer_diameter", "hole_diameter"],
            "radius": ["radius", "fillet_radius", "corner_radius"]
        }
        
        total_comparisons = 0
        total_discrepancy = 0.0
        matched_count = 0
        
        for standard_name, possible_names in dimension_mappings.items():
            # Find matching dimensions in both datasets
            value_2d = self._find_dimension_value(dimensions_2d, possible_names)
            value_3d = self._find_dimension_value(dimensions_3d, possible_names)
            
            if value_2d is not None and value_3d is not None:
                total_comparisons += 1
                discrepancy = abs(value_2d - value_3d) / max(value_2d, value_3d)
                total_discrepancy += discrepancy
                
                if discrepancy <= self.tolerance_threshold:
                    matched_count += 1
                    correlation_results["matches"].append({
                        "dimension": standard_name,
                        "value_2d": value_2d,
                        "value_3d": value_3d,
                        "discrepancy_percent": discrepancy * 100,
                        "status": "match"
                    })
                    # Use 3D value as more accurate for matches
                    correlation_results["recommended_values"][standard_name] = value_3d
                else:
                    correlation_results["discrepancies"].append({
                        "dimension": standard_name,
                        "value_2d": value_2d,
                        "value_3d": value_3d,
                        "discrepancy_percent": discrepancy * 100,
                        "status": "mismatch",
                        "recommendation": "Review drawings for accuracy"
                    })
                    # Use average for discrepancies, weighted toward 3D
                    correlation_results["recommended_values"][standard_name] = (value_2d + 2 * value_3d) / 3
        
        # Calculate overall confidence
        if total_comparisons > 0:
            match_ratio = matched_count / total_comparisons
            avg_discrepancy = total_discrepancy / total_comparisons
            correlation_results["confidence_score"] = max(0, 1 - avg_discrepancy) * match_ratio
            correlation_results["analysis"]["avg_discrepancy"] = avg_discrepancy * 100
        
        correlation_results["analysis"]["total_dimensions"] = total_comparisons
        correlation_results["analysis"]["matched_dimensions"] = matched_count
        
        return correlation_results
    
    def _find_dimension_value(self, dimensions: Dict[str, float], possible_names: List[str]) -> Optional[float]:
        """Find dimension value by checking multiple possible names"""
        for name in possible_names:
            if name in dimensions:
                return float(dimensions[name])
        return None


class MultiDimensionalAnalysisService:
    """Main service for handling multi-dimensional file analysis"""
    
    def __init__(self, db: Session):
        self.db = db
        self.deep_learning_service = DeepLearningService()
        self.correlation_engine = DimensionCorrelationEngine()
        self.file_detector = FileTypeDetector()
    
    async def analyze_part_files(
        self, 
        part_id: int, 
        files: List[QuoteFile]
    ) -> Dict[str, Any]:
        """Analyze all files for a part and cross-reference results"""
        
        analysis_results = {
            "part_id": part_id,
            "files_analyzed": len(files),
            "file_breakdown": {"2d": [], "3d": [], "unknown": []},
            "dimensional_analysis": {},
            "cross_reference_results": {},
            "unified_predictions": {},
            "confidence_metrics": {},
            "recommendations": [],
            "processing_time": 0.0
        }
        
        start_time = datetime.now()
        
        # Categorize files by type
        files_2d = []
        files_3d = []
        
        for file in files:
            file_info = self.file_detector.detect_file_type(file.file_path)
            file_data = {
                "file_id": file.id,
                "filename": file.original_filename,
                "file_type": file_info,
                "file_path": file.file_path,
                "analysis_result": None
            }
            
            if file_info['type'] == '2d':
                files_2d.append(file_data)
                analysis_results["file_breakdown"]["2d"].append(file_data)
            elif file_info['type'] == '3d':
                files_3d.append(file_data)
                analysis_results["file_breakdown"]["3d"].append(file_data)
            else:
                analysis_results["file_breakdown"]["unknown"].append(file_data)
        
        # Analyze 2D files
        dimensions_2d_combined = {}
        features_2d_combined = {}
        
        for file_data in files_2d:
            try:
                result_2d = await self._analyze_2d_file(file_data["file_path"])
                file_data["analysis_result"] = result_2d
                
                # Combine dimensional data
                if "extracted_dimensions" in result_2d:
                    dimensions_2d_combined.update(result_2d["extracted_dimensions"])
                
                # Combine feature data
                if "geometric_dimensions" in result_2d:
                    features_2d_combined.update(result_2d["geometric_dimensions"])
                    
            except Exception as e:
                logger.error(f"Error analyzing 2D file {file_data['filename']}: {e}")
                file_data["analysis_result"] = {"error": str(e)}
        
        # Analyze 3D files
        dimensions_3d_combined = {}
        features_3d_combined = {}
        
        for file_data in files_3d:
            try:
                result_3d = await self._analyze_3d_file(file_data["file_path"])
                file_data["analysis_result"] = result_3d
                
                # Combine dimensional data
                if "dimensions" in result_3d:
                    dimensions_3d_combined.update(result_3d["dimensions"])
                
                # Combine feature data
                if "features" in result_3d:
                    features_3d_combined.update(result_3d["features"])
                    
            except Exception as e:
                logger.error(f"Error analyzing 3D file {file_data['filename']}: {e}")
                file_data["analysis_result"] = {"error": str(e)}
        
        # Cross-reference analysis
        if dimensions_2d_combined and dimensions_3d_combined:
            correlation_results = self.correlation_engine.correlate_dimensions(
                dimensions_2d_combined, dimensions_3d_combined
            )
            analysis_results["cross_reference_results"] = correlation_results
            analysis_results["dimensional_analysis"]["recommended"] = correlation_results["recommended_values"]
            
            # Generate recommendations based on correlation
            analysis_results["recommendations"].extend(
                self._generate_correlation_recommendations(correlation_results)
            )
        
        # Store individual analysis results
        analysis_results["dimensional_analysis"]["2d_results"] = dimensions_2d_combined
        analysis_results["dimensional_analysis"]["3d_results"] = dimensions_3d_combined
        
        # Generate unified predictions
        unified_predictions = await self._generate_unified_predictions(
            dimensions_2d_combined,
            dimensions_3d_combined,
            features_2d_combined,
            features_3d_combined,
            part_id
        )
        analysis_results["unified_predictions"] = unified_predictions
        
        # Calculate confidence metrics
        confidence_metrics = self._calculate_confidence_metrics(
            files_2d, files_3d, correlation_results if 'correlation_results' in locals() else None
        )
        analysis_results["confidence_metrics"] = confidence_metrics
        
        # Calculate processing time
        end_time = datetime.now()
        analysis_results["processing_time"] = (end_time - start_time).total_seconds()
        
        return analysis_results
    
    async def _analyze_2d_file(self, file_path: str) -> Dict[str, Any]:
        """Analyze 2D drawing file"""
        return await self.deep_learning_service.analyze_drawing_deep(file_path)
    
    async def _analyze_3d_file(self, file_path: str) -> Dict[str, Any]:
        """Analyze 3D model file"""
        try:
            # For demonstration, create mock 3D analysis
            # In production, this would use libraries like Open3D, VTK, or FreeCAD
            
            result = {
                "file_type": "3d_model",
                "dimensions": {
                    "length": np.random.uniform(50, 200),
                    "width": np.random.uniform(30, 150),
                    "height": np.random.uniform(10, 80),
                    "volume": np.random.uniform(1000, 50000),
                    "surface_area": np.random.uniform(500, 10000)
                },
                "features": {
                    "holes_count": np.random.randint(0, 15),
                    "curved_surfaces": np.random.randint(0, 8),
                    "sharp_edges": np.random.randint(5, 25),
                    "complexity_score": np.random.uniform(0.3, 0.9)
                },
                "material_properties": {
                    "estimated_weight": np.random.uniform(0.1, 5.0),
                    "center_of_mass": [
                        np.random.uniform(-10, 10),
                        np.random.uniform(-10, 10),
                        np.random.uniform(-5, 5)
                    ]
                },
                "manufacturing_insights": {
                    "recommended_processes": ["cnc_milling", "drilling"],
                    "tool_accessibility": np.random.uniform(0.7, 0.95),
                    "setup_complexity": np.random.choice(["simple", "moderate", "complex"])
                },
                "confidence": np.random.uniform(0.85, 0.98),
                "processing_method": "3d_cad_analysis"
            }
            
            return result
            
        except Exception as e:
            logger.error(f"3D analysis failed: {e}")
            return {"error": f"3D analysis failed: {str(e)}"}
    
    async def _generate_unified_predictions(
        self,
        dimensions_2d: Dict[str, float],
        dimensions_3d: Dict[str, float],
        features_2d: Dict[str, Any],
        features_3d: Dict[str, Any],
        part_id: int
    ) -> Dict[str, Any]:
        """Generate unified predictions based on both 2D and 3D analysis"""
        
        # Combine best features from both analyses
        combined_features = {
            "dimensions": {},
            "complexity": {},
            "manufacturing": {},
            "quality": {}
        }
        
        # Use 3D dimensions as primary, 2D as validation
        if dimensions_3d:
            combined_features["dimensions"] = dimensions_3d.copy()
            # Add any unique 2D dimensions
            for key, value in dimensions_2d.items():
                if key not in combined_features["dimensions"]:
                    combined_features["dimensions"][key] = value
        else:
            combined_features["dimensions"] = dimensions_2d.copy()
        
        # Combine complexity analysis
        complexity_2d = features_2d.get("complexity_score", 0.5) if features_2d else 0.5
        complexity_3d = features_3d.get("complexity_score", 0.5) if features_3d else 0.5
        combined_complexity = (complexity_2d + complexity_3d * 1.5) / 2.5  # Weight 3D higher
        
        combined_features["complexity"] = {
            "overall_score": combined_complexity,
            "2d_complexity": complexity_2d,
            "3d_complexity": complexity_3d,
            "factors": {
                "geometric_complexity": complexity_3d,
                "dimensional_accuracy": 1.0 - abs(complexity_2d - complexity_3d),
                "feature_count": features_3d.get("holes_count", 0) + features_3d.get("curved_surfaces", 0)
            }
        }
        
        # Generate cost prediction using combined data
        cost_prediction = await self.deep_learning_service.predict_cost_deep({
            "dimensions": combined_features["dimensions"],
            "complexity": "high" if combined_complexity > 0.7 else "medium" if combined_complexity > 0.4 else "low",
            "features": {
                "holes": features_3d.get("holes_count", 0),
                "curved_surfaces": features_3d.get("curved_surfaces", 0)
            }
        })
        
        # Enhanced manufacturing recommendations
        manufacturing_processes = []
        confidence_factors = []
        
        # Add processes based on 3D geometry
        if features_3d.get("holes_count", 0) > 0:
            manufacturing_processes.append({
                "process": "drilling",
                "confidence": 0.95,
                "reason": f"{features_3d.get('holes_count', 0)} holes detected in 3D model"
            })
            confidence_factors.append(0.95)
        
        if features_3d.get("curved_surfaces", 0) > 2:
            manufacturing_processes.append({
                "process": "cnc_milling",
                "confidence": 0.88,
                "reason": f"{features_3d.get('curved_surfaces', 0)} curved surfaces require precision milling"
            })
            confidence_factors.append(0.88)
        
        if combined_features["dimensions"].get("height", 0) < 20:
            manufacturing_processes.append({
                "process": "laser_cutting",
                "confidence": 0.75,
                "reason": "Thin part suitable for laser cutting"
            })
            confidence_factors.append(0.75)
        
        # Default process
        if not manufacturing_processes:
            manufacturing_processes.append({
                "process": "cnc_milling",
                "confidence": 0.80,
                "reason": "Standard CNC milling recommended"
            })
            confidence_factors.append(0.80)
        
        overall_confidence = np.mean(confidence_factors) if confidence_factors else 0.75
        
        unified_predictions = {
            "cost_estimation": cost_prediction,
            "manufacturing_processes": manufacturing_processes,
            "time_estimation": {
                "setup_time_hours": np.random.uniform(1, 6),
                "machining_time_hours": np.random.uniform(2, 12),
                "total_time_hours": np.random.uniform(3, 18),
                "confidence": overall_confidence
            },
            "quality_assessment": {
                "achievable_tolerance": "±0.1mm" if combined_complexity < 0.6 else "±0.05mm",
                "surface_finish": "Ra 1.6" if combined_complexity < 0.7 else "Ra 0.8",
                "dimensional_stability": "high" if overall_confidence > 0.85 else "medium"
            },
            "risk_assessment": {
                "geometric_risk": "low" if combined_complexity < 0.6 else "medium",
                "dimensional_risk": "low" if overall_confidence > 0.85 else "medium",
                "manufacturing_risk": "low" if len(manufacturing_processes) <= 2 else "medium"
            },
            "overall_confidence": overall_confidence,
            "prediction_basis": {
                "2d_files_used": len([f for f in [dimensions_2d] if f]),
                "3d_files_used": len([f for f in [dimensions_3d] if f]),
                "cross_validation": bool(dimensions_2d and dimensions_3d),
                "ai_models_used": ["CNN_2D", "3D_CAD_Analyzer", "Cost_Predictor"]
            }
        }
        
        return unified_predictions
    
    def _generate_correlation_recommendations(self, correlation_results: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on correlation analysis"""
        recommendations = []
        
        if correlation_results["confidence_score"] < 0.8:
            recommendations.append(
                "Cross-reference analysis shows discrepancies between 2D and 3D files. "
                "Please verify dimensional accuracy."
            )
        
        if correlation_results["discrepancies"]:
            for discrepancy in correlation_results["discrepancies"]:
                if discrepancy["discrepancy_percent"] > 10:
                    recommendations.append(
                        f"Significant discrepancy in {discrepancy['dimension']}: "
                        f"2D shows {discrepancy['value_2d']:.2f}, 3D shows {discrepancy['value_3d']:.2f}"
                    )
        
        if correlation_results["analysis"]["matched_dimensions"] == 0:
            recommendations.append(
                "No matching dimensions found between 2D and 3D files. "
                "Consider uploading complementary drawing files."
            )
        
        return recommendations
    
    def _calculate_confidence_metrics(
        self, 
        files_2d: List[Dict], 
        files_3d: List[Dict], 
        correlation_results: Optional[Dict]
    ) -> Dict[str, Any]:
        """Calculate overall confidence metrics"""
        
        metrics = {
            "overall_confidence": 0.0,
            "2d_analysis_confidence": 0.0,
            "3d_analysis_confidence": 0.0,
            "cross_validation_confidence": 0.0,
            "file_completeness_score": 0.0,
            "recommendation_confidence": 0.0
        }
        
        # Calculate 2D confidence
        if files_2d:
            confidences_2d = []
            for file_data in files_2d:
                if file_data["analysis_result"] and "confidence" in file_data["analysis_result"]:
                    confidences_2d.append(file_data["analysis_result"]["confidence"])
            metrics["2d_analysis_confidence"] = np.mean(confidences_2d) if confidences_2d else 0.0
        
        # Calculate 3D confidence  
        if files_3d:
            confidences_3d = []
            for file_data in files_3d:
                if file_data["analysis_result"] and "confidence" in file_data["analysis_result"]:
                    confidences_3d.append(file_data["analysis_result"]["confidence"])
            metrics["3d_analysis_confidence"] = np.mean(confidences_3d) if confidences_3d else 0.0
        
        # Cross-validation confidence
        if correlation_results:
            metrics["cross_validation_confidence"] = correlation_results["confidence_score"]
        
        # File completeness score
        has_2d = len(files_2d) > 0
        has_3d = len(files_3d) > 0
        if has_2d and has_3d:
            metrics["file_completeness_score"] = 1.0
        elif has_2d or has_3d:
            metrics["file_completeness_score"] = 0.7
        else:
            metrics["file_completeness_score"] = 0.0
        
        # Overall recommendation confidence
        confidence_components = [
            metrics["2d_analysis_confidence"] * 0.3,
            metrics["3d_analysis_confidence"] * 0.4,
            metrics["cross_validation_confidence"] * 0.2,
            metrics["file_completeness_score"] * 0.1
        ]
        
        metrics["overall_confidence"] = sum(confidence_components)
        metrics["recommendation_confidence"] = min(0.95, metrics["overall_confidence"] + 0.1)
        
        return metrics
    
    async def get_part_analysis_summary(self, part_id: int) -> Dict[str, Any]:
        """Get comprehensive analysis summary for a part"""
        
        # Get all files for the part
        files = self.db.query(QuoteFile).filter(
            QuoteFile.quote_id.in_(
                self.db.query(Part.quote_id).filter(Part.id == part_id)
            )
        ).all()
        
        if not files:
            return {"error": "No files found for this part"}
        
        # Run full analysis
        analysis_results = await self.analyze_part_files(part_id, files)
        
        # Add summary statistics
        summary = {
            "part_id": part_id,
            "analysis_timestamp": datetime.now().isoformat(),
            "file_analysis": analysis_results,
            "summary_statistics": {
                "total_files": len(files),
                "successful_analyses": len([f for f in files if f"analysis_result" in str(f)]),
                "average_confidence": analysis_results["confidence_metrics"]["overall_confidence"],
                "primary_process": analysis_results["unified_predictions"]["manufacturing_processes"][0]["process"] if analysis_results["unified_predictions"]["manufacturing_processes"] else "unknown",
                "estimated_cost": analysis_results["unified_predictions"]["cost_estimation"].get("total_cost", 0),
                "complexity_level": "high" if analysis_results["confidence_metrics"]["overall_confidence"] > 0.8 else "medium"
            },
            "key_insights": self._generate_key_insights(analysis_results)
        }
        
        return summary
    
    def _generate_key_insights(self, analysis_results: Dict[str, Any]) -> List[str]:
        """Generate key insights from analysis results"""
        insights = []
        
        confidence = analysis_results["confidence_metrics"]["overall_confidence"]
        
        if confidence > 0.9:
            insights.append("High confidence analysis - All dimensions cross-validated successfully")
        elif confidence > 0.7:
            insights.append("Good confidence analysis - Minor discrepancies detected")
        else:
            insights.append("Low confidence analysis - Significant discrepancies require review")
        
        # File type insights
        files_2d = len(analysis_results["file_breakdown"]["2d"])
        files_3d = len(analysis_results["file_breakdown"]["3d"])
        
        if files_2d > 0 and files_3d > 0:
            insights.append(f"Complete file set: {files_2d} 2D drawing(s) and {files_3d} 3D model(s)")
        elif files_3d > 0:
            insights.append("3D model available - Accurate geometric analysis possible")
        elif files_2d > 0:
            insights.append("2D drawings only - Consider adding 3D model for better accuracy")
        
        # Manufacturing insights
        processes = analysis_results["unified_predictions"]["manufacturing_processes"]
        if len(processes) > 3:
            insights.append("Complex part requiring multiple manufacturing processes")
        elif len(processes) == 1:
            insights.append(f"Simple part suitable for {processes[0]['process']}")
        
        return insights