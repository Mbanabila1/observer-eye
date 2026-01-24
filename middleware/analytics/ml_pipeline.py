"""
Machine Learning Pipeline

Advanced machine learning pipeline for predictive analytics, anomaly detection,
and intelligent insights generation for observability data.
"""

import asyncio
import time
import pickle
import os
from typing import Any, Dict, List, Optional, Tuple, Union
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.ensemble import RandomForestRegressor, IsolationForest
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.cluster import KMeans
from sklearn.metrics import mean_squared_error, accuracy_score, silhouette_score
from sklearn.decomposition import PCA
import joblib
import structlog

from .models import MLModelResult, DataQualityMetrics

logger = structlog.get_logger(__name__)

class MachineLearningPipeline:
    """
    Advanced Machine Learning Pipeline for Observability Analytics
    
    Provides comprehensive ML capabilities including:
    - Predictive analytics for capacity planning
    - Anomaly detection using multiple algorithms
    - Performance forecasting and trend prediction
    - Automated model training and validation
    - Feature engineering and selection
    - Model persistence and versioning
    """
    
    def __init__(self, models_directory: str = "ml_models"):
        self.models_dir = Path(models_directory)
        self.models_dir.mkdir(exist_ok=True)
        
        # ML pipeline statistics
        self._ml_stats = {
            'total_predictions': 0,
            'successful_predictions': 0,
            'failed_predictions': 0,
            'models_trained': 0,
            'models_by_type': {},
            'average_prediction_time_ms': 0.0,
            'average_training_time_ms': 0.0
        }
        
        # Model registry
        self._model_registry = {}
        self._scalers = {}
        self._encoders = {}
        
        # ML configuration
        self.max_features_for_training = 50
        self.min_samples_for_training = 100
        self.model_validation_split = 0.2
        self.cross_validation_folds = 5
        
        # Load existing models
        self._models_loaded = False
        
        logger.info("Machine Learning Pipeline initialized", models_directory=str(self.models_dir))
    
    async def train_anomaly_detection_model(self, training_data: pd.DataFrame, 
                                          model_name: str = "anomaly_detector") -> Dict[str, Any]:
        """
        Train an anomaly detection model
        
        Args:
            training_data: Historical data for training
            model_name: Name for the trained model
            
        Returns:
            Training results and model metadata
        """
        start_time = time.time()
        
        try:
            logger.info("Training anomaly detection model", 
                       model_name=model_name, 
                       data_shape=training_data.shape)
            
            # Prepare features
            features = await self._prepare_features(training_data)
            
            if features.empty or len(features) < self.min_samples_for_training:
                return {
                    'status': 'failed',
                    'error': 'Insufficient training data',
                    'samples_required': self.min_samples_for_training,
                    'samples_provided': len(features)
                }
            
            # Scale features
            scaler = StandardScaler()
            features_scaled = scaler.fit_transform(features)
            
            # Train Isolation Forest for anomaly detection
            model = IsolationForest(
                contamination=0.1,  # Expect 10% anomalies
                random_state=42,
                n_estimators=100
            )
            
            model.fit(features_scaled)
            
            # Validate model
            anomaly_scores = model.decision_function(features_scaled)
            predictions = model.predict(features_scaled)
            
            # Calculate validation metrics
            anomaly_rate = (predictions == -1).sum() / len(predictions)
            
            # Save model and scaler
            model_path = self.models_dir / f"{model_name}.joblib"
            scaler_path = self.models_dir / f"{model_name}_scaler.joblib"
            
            joblib.dump(model, model_path)
            joblib.dump(scaler, scaler_path)
            
            # Update registry
            self._model_registry[model_name] = {
                'type': 'anomaly_detection',
                'model': model,
                'scaler': scaler,
                'features': list(features.columns),
                'trained_at': datetime.utcnow(),
                'training_samples': len(features),
                'anomaly_rate': anomaly_rate
            }
            
            training_time_ms = (time.time() - start_time) * 1000
            
            # Update statistics
            self._ml_stats['models_trained'] += 1
            self._update_model_type_stats('anomaly_detection')
            self._update_average_training_time(training_time_ms)
            
            logger.info("Anomaly detection model trained successfully",
                       model_name=model_name,
                       training_time_ms=training_time_ms,
                       anomaly_rate=anomaly_rate)
            
            return {
                'status': 'success',
                'model_name': model_name,
                'model_type': 'anomaly_detection',
                'training_samples': len(features),
                'features_used': list(features.columns),
                'anomaly_rate': anomaly_rate,
                'training_time_ms': training_time_ms,
                'model_path': str(model_path)
            }
            
        except Exception as e:
            training_time_ms = (time.time() - start_time) * 1000
            logger.error("Anomaly detection model training failed",
                        model_name=model_name,
                        error=str(e),
                        training_time_ms=training_time_ms)
            
            return {
                'status': 'failed',
                'error': str(e),
                'training_time_ms': training_time_ms
            }
    
    async def train_performance_prediction_model(self, training_data: pd.DataFrame,
                                               target_column: str,
                                               model_name: str = "performance_predictor") -> Dict[str, Any]:
        """
        Train a performance prediction model
        
        Args:
            training_data: Historical performance data
            target_column: Column to predict
            model_name: Name for the trained model
            
        Returns:
            Training results and model metadata
        """
        start_time = time.time()
        
        try:
            logger.info("Training performance prediction model",
                       model_name=model_name,
                       target_column=target_column,
                       data_shape=training_data.shape)
            
            # Prepare features and target
            features = await self._prepare_features(training_data, exclude_columns=[target_column])
            
            if target_column not in training_data.columns:
                return {
                    'status': 'failed',
                    'error': f'Target column {target_column} not found in training data'
                }
            
            target = training_data[target_column].dropna()
            
            # Align features and target
            common_index = features.index.intersection(target.index)
            features = features.loc[common_index]
            target = target.loc[common_index]
            
            if len(features) < self.min_samples_for_training:
                return {
                    'status': 'failed',
                    'error': 'Insufficient training data after alignment',
                    'samples_required': self.min_samples_for_training,
                    'samples_provided': len(features)
                }
            
            # Scale features
            scaler = StandardScaler()
            features_scaled = scaler.fit_transform(features)
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                features_scaled, target, 
                test_size=self.model_validation_split, 
                random_state=42
            )
            
            # Train Random Forest model
            model = RandomForestRegressor(
                n_estimators=100,
                random_state=42,
                n_jobs=-1
            )
            
            model.fit(X_train, y_train)
            
            # Validate model
            train_predictions = model.predict(X_train)
            test_predictions = model.predict(X_test)
            
            train_mse = mean_squared_error(y_train, train_predictions)
            test_mse = mean_squared_error(y_test, test_predictions)
            
            # Cross-validation
            cv_scores = cross_val_score(model, features_scaled, target, 
                                      cv=self.cross_validation_folds, 
                                      scoring='neg_mean_squared_error')
            cv_rmse = np.sqrt(-cv_scores.mean())
            
            # Feature importance
            feature_importance = dict(zip(features.columns, model.feature_importances_))
            
            # Save model and scaler
            model_path = self.models_dir / f"{model_name}.joblib"
            scaler_path = self.models_dir / f"{model_name}_scaler.joblib"
            
            joblib.dump(model, model_path)
            joblib.dump(scaler, scaler_path)
            
            # Update registry
            self._model_registry[model_name] = {
                'type': 'performance_prediction',
                'model': model,
                'scaler': scaler,
                'features': list(features.columns),
                'target_column': target_column,
                'trained_at': datetime.utcnow(),
                'training_samples': len(features),
                'test_mse': test_mse,
                'cv_rmse': cv_rmse,
                'feature_importance': feature_importance
            }
            
            training_time_ms = (time.time() - start_time) * 1000
            
            # Update statistics
            self._ml_stats['models_trained'] += 1
            self._update_model_type_stats('performance_prediction')
            self._update_average_training_time(training_time_ms)
            
            logger.info("Performance prediction model trained successfully",
                       model_name=model_name,
                       training_time_ms=training_time_ms,
                       test_mse=test_mse,
                       cv_rmse=cv_rmse)
            
            return {
                'status': 'success',
                'model_name': model_name,
                'model_type': 'performance_prediction',
                'training_samples': len(features),
                'features_used': list(features.columns),
                'target_column': target_column,
                'test_mse': test_mse,
                'cv_rmse': cv_rmse,
                'feature_importance': feature_importance,
                'training_time_ms': training_time_ms,
                'model_path': str(model_path)
            }
            
        except Exception as e:
            training_time_ms = (time.time() - start_time) * 1000
            logger.error("Performance prediction model training failed",
                        model_name=model_name,
                        error=str(e),
                        training_time_ms=training_time_ms)
            
            return {
                'status': 'failed',
                'error': str(e),
                'training_time_ms': training_time_ms
            }
    
    async def predict_anomalies(self, data: pd.DataFrame, 
                               model_name: str = "anomaly_detector") -> MLModelResult:
        """
        Predict anomalies in new data
        
        Args:
            data: Data to analyze for anomalies
            model_name: Name of the trained anomaly detection model
            
        Returns:
            MLModelResult with anomaly predictions
        """
        start_time = time.time()
        self._ml_stats['total_predictions'] += 1
        
        try:
            if model_name not in self._model_registry:
                raise ValueError(f"Model {model_name} not found in registry")
            
            model_info = self._model_registry[model_name]
            model = model_info['model']
            scaler = model_info['scaler']
            
            # Prepare features
            features = await self._prepare_features(data, required_columns=model_info['features'])
            
            if features.empty:
                raise ValueError("No valid features found in input data")
            
            # Scale features
            features_scaled = scaler.transform(features)
            
            # Make predictions
            predictions = model.predict(features_scaled)
            anomaly_scores = model.decision_function(features_scaled)
            
            # Prepare results
            prediction_results = []
            confidence_scores = []
            
            for i, (pred, score) in enumerate(zip(predictions, anomaly_scores)):
                is_anomaly = pred == -1
                confidence = abs(score)  # Higher absolute score = higher confidence
                
                prediction_results.append({
                    'index': i,
                    'is_anomaly': is_anomaly,
                    'anomaly_score': score,
                    'confidence': confidence
                })
                
                confidence_scores.append(confidence)
            
            prediction_time_ms = (time.time() - start_time) * 1000
            
            # Update statistics
            self._ml_stats['successful_predictions'] += 1
            self._update_average_prediction_time(prediction_time_ms)
            
            return MLModelResult(
                model_id=model_name,
                model_type='anomaly_detection',
                predictions=prediction_results,
                confidence_scores=confidence_scores,
                feature_importance=model_info.get('feature_importance', {}),
                model_accuracy=1.0 - model_info.get('anomaly_rate', 0.1),
                training_data_size=model_info.get('training_samples', 0),
                prediction_time_ms=prediction_time_ms
            )
            
        except Exception as e:
            self._ml_stats['failed_predictions'] += 1
            prediction_time_ms = (time.time() - start_time) * 1000
            
            logger.error("Anomaly prediction failed",
                        model_name=model_name,
                        error=str(e),
                        prediction_time_ms=prediction_time_ms)
            
            return MLModelResult(
                model_id=model_name,
                model_type='anomaly_detection',
                predictions=[],
                confidence_scores=[],
                feature_importance={},
                model_accuracy=0.0,
                training_data_size=0,
                prediction_time_ms=prediction_time_ms
            )
    
    async def predict_performance(self, data: pd.DataFrame, 
                                 model_name: str = "performance_predictor") -> MLModelResult:
        """
        Predict performance metrics
        
        Args:
            data: Input data for prediction
            model_name: Name of the trained performance prediction model
            
        Returns:
            MLModelResult with performance predictions
        """
        start_time = time.time()
        self._ml_stats['total_predictions'] += 1
        
        try:
            if model_name not in self._model_registry:
                raise ValueError(f"Model {model_name} not found in registry")
            
            model_info = self._model_registry[model_name]
            model = model_info['model']
            scaler = model_info['scaler']
            
            # Prepare features
            features = await self._prepare_features(data, required_columns=model_info['features'])
            
            if features.empty:
                raise ValueError("No valid features found in input data")
            
            # Scale features
            features_scaled = scaler.transform(features)
            
            # Make predictions
            predictions = model.predict(features_scaled)
            
            # Calculate confidence scores (using prediction variance for Random Forest)
            if hasattr(model, 'estimators_'):
                # For Random Forest, calculate prediction variance as confidence
                tree_predictions = np.array([tree.predict(features_scaled) for tree in model.estimators_])
                confidence_scores = 1.0 / (1.0 + np.var(tree_predictions, axis=0))
            else:
                # Default confidence
                confidence_scores = [0.8] * len(predictions)
            
            # Prepare results
            prediction_results = []
            for i, (pred, conf) in enumerate(zip(predictions, confidence_scores)):
                prediction_results.append({
                    'index': i,
                    'predicted_value': pred,
                    'confidence': conf
                })
            
            prediction_time_ms = (time.time() - start_time) * 1000
            
            # Update statistics
            self._ml_stats['successful_predictions'] += 1
            self._update_average_prediction_time(prediction_time_ms)
            
            return MLModelResult(
                model_id=model_name,
                model_type='performance_prediction',
                predictions=prediction_results,
                confidence_scores=confidence_scores.tolist() if isinstance(confidence_scores, np.ndarray) else confidence_scores,
                feature_importance=model_info.get('feature_importance', {}),
                model_accuracy=1.0 / (1.0 + model_info.get('test_mse', 1.0)),
                training_data_size=model_info.get('training_samples', 0),
                prediction_time_ms=prediction_time_ms
            )
            
        except Exception as e:
            self._ml_stats['failed_predictions'] += 1
            prediction_time_ms = (time.time() - start_time) * 1000
            
            logger.error("Performance prediction failed",
                        model_name=model_name,
                        error=str(e),
                        prediction_time_ms=prediction_time_ms)
            
            return MLModelResult(
                model_id=model_name,
                model_type='performance_prediction',
                predictions=[],
                confidence_scores=[],
                feature_importance={},
                model_accuracy=0.0,
                training_data_size=0,
                prediction_time_ms=prediction_time_ms
            )
    
    async def cluster_analysis(self, data: pd.DataFrame, 
                              n_clusters: Optional[int] = None,
                              model_name: str = "cluster_analyzer") -> Dict[str, Any]:
        """
        Perform cluster analysis on observability data
        
        Args:
            data: Data for clustering
            n_clusters: Number of clusters (auto-determined if None)
            model_name: Name for the clustering model
            
        Returns:
            Clustering results and analysis
        """
        start_time = time.time()
        
        try:
            logger.info("Performing cluster analysis",
                       model_name=model_name,
                       data_shape=data.shape,
                       n_clusters=n_clusters)
            
            # Prepare features
            features = await self._prepare_features(data)
            
            if features.empty or len(features) < 10:
                return {
                    'status': 'failed',
                    'error': 'Insufficient data for clustering',
                    'samples_required': 10,
                    'samples_provided': len(features)
                }
            
            # Scale features
            scaler = StandardScaler()
            features_scaled = scaler.fit_transform(features)
            
            # Determine optimal number of clusters if not provided
            if n_clusters is None:
                n_clusters = await self._determine_optimal_clusters(features_scaled)
            
            # Perform clustering
            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            cluster_labels = kmeans.fit_predict(features_scaled)
            
            # Calculate clustering metrics
            silhouette_avg = silhouette_score(features_scaled, cluster_labels)
            inertia = kmeans.inertia_
            
            # Analyze clusters
            cluster_analysis = {}
            for cluster_id in range(n_clusters):
                cluster_mask = cluster_labels == cluster_id
                cluster_data = features[cluster_mask]
                
                cluster_analysis[f'cluster_{cluster_id}'] = {
                    'size': int(cluster_mask.sum()),
                    'percentage': float(cluster_mask.sum() / len(features) * 100),
                    'centroid': kmeans.cluster_centers_[cluster_id].tolist(),
                    'characteristics': await self._analyze_cluster_characteristics(cluster_data)
                }
            
            # Dimensionality reduction for visualization
            if features_scaled.shape[1] > 2:
                pca = PCA(n_components=2)
                features_2d = pca.fit_transform(features_scaled)
                explained_variance = pca.explained_variance_ratio_.sum()
            else:
                features_2d = features_scaled
                explained_variance = 1.0
            
            analysis_time_ms = (time.time() - start_time) * 1000
            
            logger.info("Cluster analysis completed",
                       model_name=model_name,
                       n_clusters=n_clusters,
                       silhouette_score=silhouette_avg,
                       analysis_time_ms=analysis_time_ms)
            
            return {
                'status': 'success',
                'model_name': model_name,
                'n_clusters': n_clusters,
                'cluster_labels': cluster_labels.tolist(),
                'silhouette_score': silhouette_avg,
                'inertia': inertia,
                'cluster_analysis': cluster_analysis,
                'features_2d': features_2d.tolist(),
                'explained_variance_2d': explained_variance,
                'analysis_time_ms': analysis_time_ms
            }
            
        except Exception as e:
            analysis_time_ms = (time.time() - start_time) * 1000
            logger.error("Cluster analysis failed",
                        model_name=model_name,
                        error=str(e),
                        analysis_time_ms=analysis_time_ms)
            
            return {
                'status': 'failed',
                'error': str(e),
                'analysis_time_ms': analysis_time_ms
            }
    
    async def _prepare_features(self, data: pd.DataFrame, 
                               exclude_columns: Optional[List[str]] = None,
                               required_columns: Optional[List[str]] = None) -> pd.DataFrame:
        """Prepare features for ML models"""
        
        try:
            exclude_columns = exclude_columns or []
            
            # Standard columns to exclude
            standard_excludes = ['id', 'timestamp', 'correlation_id', 'data_source']
            exclude_columns.extend(standard_excludes)
            
            # Select numeric columns
            numeric_data = data.select_dtypes(include=[np.number])
            
            # Remove excluded columns
            for col in exclude_columns:
                if col in numeric_data.columns:
                    numeric_data = numeric_data.drop(columns=[col])
            
            # If required columns specified, ensure they exist
            if required_columns:
                missing_columns = [col for col in required_columns if col not in numeric_data.columns]
                if missing_columns:
                    logger.warning("Missing required columns", missing_columns=missing_columns)
                    return pd.DataFrame()
                
                numeric_data = numeric_data[required_columns]
            
            # Remove columns with too many missing values (>50%)
            missing_threshold = 0.5
            for col in numeric_data.columns:
                missing_ratio = numeric_data[col].isnull().sum() / len(numeric_data)
                if missing_ratio > missing_threshold:
                    numeric_data = numeric_data.drop(columns=[col])
            
            # Fill remaining missing values
            numeric_data = numeric_data.fillna(numeric_data.mean())
            
            # Limit number of features
            if len(numeric_data.columns) > self.max_features_for_training:
                # Select features with highest variance
                feature_variances = numeric_data.var().sort_values(ascending=False)
                top_features = feature_variances.head(self.max_features_for_training).index
                numeric_data = numeric_data[top_features]
            
            return numeric_data
            
        except Exception as e:
            logger.error("Error preparing features", error=str(e))
            return pd.DataFrame()
    
    async def _determine_optimal_clusters(self, features_scaled: np.ndarray) -> int:
        """Determine optimal number of clusters using elbow method"""
        
        try:
            max_clusters = min(10, len(features_scaled) // 5)  # Reasonable upper bound
            
            if max_clusters < 2:
                return 2
            
            inertias = []
            k_range = range(2, max_clusters + 1)
            
            for k in k_range:
                kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
                kmeans.fit(features_scaled)
                inertias.append(kmeans.inertia_)
            
            # Find elbow using rate of change
            if len(inertias) >= 3:
                # Calculate second derivative to find elbow
                second_derivatives = []
                for i in range(1, len(inertias) - 1):
                    second_deriv = inertias[i-1] - 2*inertias[i] + inertias[i+1]
                    second_derivatives.append(second_deriv)
                
                if second_derivatives:
                    elbow_idx = np.argmax(second_derivatives)
                    optimal_k = k_range[elbow_idx + 1]  # Adjust for index offset
                    return optimal_k
            
            # Fallback to middle value
            return max(2, max_clusters // 2)
            
        except Exception as e:
            logger.error("Error determining optimal clusters", error=str(e))
            return 3  # Default fallback
    
    async def _analyze_cluster_characteristics(self, cluster_data: pd.DataFrame) -> Dict[str, Any]:
        """Analyze characteristics of a cluster"""
        
        try:
            if cluster_data.empty:
                return {}
            
            characteristics = {}
            
            for column in cluster_data.columns:
                col_data = cluster_data[column].dropna()
                
                if len(col_data) > 0:
                    characteristics[column] = {
                        'mean': float(col_data.mean()),
                        'std': float(col_data.std()),
                        'min': float(col_data.min()),
                        'max': float(col_data.max()),
                        'median': float(col_data.median())
                    }
            
            return characteristics
            
        except Exception as e:
            logger.error("Error analyzing cluster characteristics", error=str(e))
            return {}
    
    async def _ensure_models_loaded(self):
        """Ensure models are loaded"""
        if not self._models_loaded:
            await self._load_existing_models()
            self._models_loaded = True
    async def _load_existing_models(self):
        """Load existing models from disk"""
        
        try:
            model_files = list(self.models_dir.glob("*.joblib"))
            
            for model_file in model_files:
                if "_scaler" in model_file.name:
                    continue  # Skip scaler files
                
                model_name = model_file.stem
                scaler_file = self.models_dir / f"{model_name}_scaler.joblib"
                
                try:
                    model = joblib.load(model_file)
                    scaler = joblib.load(scaler_file) if scaler_file.exists() else None
                    
                    # Determine model type based on model class
                    if hasattr(model, 'decision_function'):
                        model_type = 'anomaly_detection'
                    elif hasattr(model, 'predict') and hasattr(model, 'feature_importances_'):
                        model_type = 'performance_prediction'
                    else:
                        model_type = 'unknown'
                    
                    self._model_registry[model_name] = {
                        'type': model_type,
                        'model': model,
                        'scaler': scaler,
                        'loaded_from_disk': True,
                        'loaded_at': datetime.utcnow()
                    }
                    
                    logger.info("Loaded existing model", model_name=model_name, model_type=model_type)
                    
                except Exception as e:
                    logger.warning("Failed to load model", model_file=str(model_file), error=str(e))
            
        except Exception as e:
            logger.error("Error loading existing models", error=str(e))
    
    def _update_model_type_stats(self, model_type: str):
        """Update model type statistics"""
        self._ml_stats['models_by_type'][model_type] = (
            self._ml_stats['models_by_type'].get(model_type, 0) + 1
        )
    
    def _update_average_prediction_time(self, prediction_time_ms: float):
        """Update average prediction time statistics"""
        current_avg = self._ml_stats['average_prediction_time_ms']
        successful_predictions = self._ml_stats['successful_predictions']
        
        if successful_predictions > 1:
            new_avg = ((current_avg * (successful_predictions - 1)) + prediction_time_ms) / successful_predictions
            self._ml_stats['average_prediction_time_ms'] = new_avg
        else:
            self._ml_stats['average_prediction_time_ms'] = prediction_time_ms
    
    def _update_average_training_time(self, training_time_ms: float):
        """Update average training time statistics"""
        current_avg = self._ml_stats['average_training_time_ms']
        models_trained = self._ml_stats['models_trained']
        
        if models_trained > 1:
            new_avg = ((current_avg * (models_trained - 1)) + training_time_ms) / models_trained
            self._ml_stats['average_training_time_ms'] = new_avg
        else:
            self._ml_stats['average_training_time_ms'] = training_time_ms
    
    async def get_ml_statistics(self) -> Dict[str, Any]:
        """Get ML pipeline statistics"""
        return {
            'ml_stats': self._ml_stats.copy(),
            'model_registry': {
                name: {
                    'type': info['type'],
                    'trained_at': info.get('trained_at', info.get('loaded_at')).isoformat() if info.get('trained_at') or info.get('loaded_at') else None,
                    'training_samples': info.get('training_samples', 0),
                    'loaded_from_disk': info.get('loaded_from_disk', False)
                }
                for name, info in self._model_registry.items()
            },
            'configuration': {
                'max_features_for_training': self.max_features_for_training,
                'min_samples_for_training': self.min_samples_for_training,
                'model_validation_split': self.model_validation_split,
                'cross_validation_folds': self.cross_validation_folds
            }
        }
    
    async def list_models(self) -> Dict[str, Any]:
        """List all available models"""
        return {
            model_name: {
                'type': model_info['type'],
                'features': model_info.get('features', []),
                'trained_at': model_info.get('trained_at').isoformat() if model_info.get('trained_at') else None,
                'training_samples': model_info.get('training_samples', 0),
                'accuracy_metrics': {
                    'test_mse': model_info.get('test_mse'),
                    'cv_rmse': model_info.get('cv_rmse'),
                    'anomaly_rate': model_info.get('anomaly_rate')
                }
            }
            for model_name, model_info in self._model_registry.items()
        }
    
    async def delete_model(self, model_name: str) -> bool:
        """Delete a model from registry and disk"""
        try:
            if model_name in self._model_registry:
                # Remove from registry
                del self._model_registry[model_name]
                
                # Remove files from disk
                model_file = self.models_dir / f"{model_name}.joblib"
                scaler_file = self.models_dir / f"{model_name}_scaler.joblib"
                
                if model_file.exists():
                    model_file.unlink()
                if scaler_file.exists():
                    scaler_file.unlink()
                
                logger.info("Model deleted", model_name=model_name)
                return True
            
            return False
            
        except Exception as e:
            logger.error("Error deleting model", model_name=model_name, error=str(e))
            return False
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check for the ML pipeline"""
        try:
            # Test basic functionality
            test_data = pd.DataFrame({
                'feature1': np.random.normal(50, 10, 100),
                'feature2': np.random.normal(30, 5, 100),
                'target': np.random.normal(100, 20, 100)
            })
            
            # Test feature preparation
            features = await self._prepare_features(test_data, exclude_columns=['target'])
            
            status = "healthy" if not features.empty else "degraded"
            
            return {
                'status': status,
                'statistics': await self.get_ml_statistics(),
                'models_loaded': len(self._model_registry),
                'test_features_prepared': len(features.columns) if not features.empty else 0,
                'models_directory': str(self.models_dir),
                'last_check': datetime.utcnow().isoformat()
            }
        
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'last_check': datetime.utcnow().isoformat()
            }