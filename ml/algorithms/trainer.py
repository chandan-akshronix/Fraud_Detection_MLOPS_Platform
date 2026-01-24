"""
ML Algorithm Implementations
Fraud detection model training and inference.
"""
import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple, Optional
from dataclasses import dataclass
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler
from ml.transformers.fraud_feature_engineer import FraudFeatureEngineer
from sklearn.metrics import (
    precision_score, recall_score, f1_score, 
    roc_auc_score, confusion_matrix, classification_report
)
import logging

logger = logging.getLogger(__name__)


@dataclass
class TrainingConfig:
    """Configuration for model training."""
    algorithm: str = "xgboost"
    hyperparameters: Dict[str, Any] = None
    test_size: float = 0.2
    random_state: int = 42
    imbalanced_strategy: str = "class_weight"  # class_weight, smote, undersample
    
    def __post_init__(self):
        if self.hyperparameters is None:
            self.hyperparameters = {}


@dataclass
class TrainingResult:
    """Result of model training."""
    model: Any
    pipeline: Any
    metrics: Dict[str, float]
    feature_importance: Dict[str, float]
    feature_names: list
    confusion_matrix: np.ndarray
    classification_report: str
    onnx_bytes: Optional[bytes] = None


class FraudDetectionTrainer:
    """
    Trains fraud detection models using various algorithms.
    
    Supported algorithms:
    - xgboost: XGBoost Classifier (default)
    - lightgbm: LightGBM Classifier
    - random_forest: Random Forest
    - isolation_forest: Isolation Forest (unsupervised)
    """
    
    def __init__(self, config: TrainingConfig = None):
        self.config = config or TrainingConfig()
        self.model = None
        self.pipeline = None
        self.feature_names = []
    
    def train(self, X: pd.DataFrame, y: pd.Series):
        """Train the fraud detection model."""
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y,
            test_size=self.config.test_size,
            random_state=self.config.random_state,
            stratify=y
        )
        
        # Handle imbalanced data
        X_train, y_train = self._handle_imbalanced(X_train, y_train)
        
        # BUILD SKLEARN PIPELINE
        self.pipeline = self._build_pipeline(y_train)
        self.pipeline.fit(X_train, y_train)
        
        # Extract the trained model from pipeline
        self.model = self.pipeline.named_steps['model']
        self.feature_names = self.pipeline.named_steps['fraud_features'].feature_names_out_
        
        # Evaluate
        y_pred = self.pipeline.predict(X_test)
        y_prob = self.pipeline.predict_proba(X_test)[:, 1]
        
        # Compute metrics
        metrics = self._compute_metrics(y_test, y_pred, y_prob)
        
        # Get feature importance
        importance = self._get_feature_importance()
        
        # Build result
        result = TrainingResult(
            model=self.model,
            pipeline=self.pipeline,
            metrics=metrics,
            feature_importance=importance,
            feature_names=self.feature_names,
            confusion_matrix=confusion_matrix(y_test, y_pred),
            classification_report=classification_report(y_test, y_pred)
        )
        
        logger.info(f"Training complete. F1: {metrics['f1']:.4f}, AUC: {metrics['auc']:.4f}")
        return result
    
    def _create_model(self, y_train: pd.Series):
        """Create the model based on algorithm choice."""
        algorithm = self.config.algorithm.lower()
        params = self.config.hyperparameters.copy()
        
        if algorithm == "xgboost":
            from xgboost import XGBClassifier
            
            # Calculate scale_pos_weight for imbalanced data
            if self.config.imbalanced_strategy == "class_weight":
                neg_count = (y_train == 0).sum()
                pos_count = (y_train == 1).sum()
                params.setdefault("scale_pos_weight", neg_count / max(pos_count, 1))
            
            # Default XGBoost params
            params.setdefault("n_estimators", 100)
            params.setdefault("max_depth", 6)
            params.setdefault("learning_rate", 0.1)
            params.setdefault("subsample", 0.8)
            params.setdefault("colsample_bytree", 0.8)
            params.setdefault("random_state", self.config.random_state)
            params.setdefault("verbosity", 0)
            params.setdefault("use_label_encoder", False)
            params.setdefault("eval_metric", "logloss")
            
            return XGBClassifier(**params)
        
        elif algorithm == "lightgbm":
            from lightgbm import LGBMClassifier
            
            if self.config.imbalanced_strategy == "class_weight":
                params.setdefault("class_weight", "balanced")
            
            params.setdefault("n_estimators", 100)
            params.setdefault("max_depth", 6)
            params.setdefault("learning_rate", 0.1)
            params.setdefault("random_state", self.config.random_state)
            params.setdefault("verbosity", -1)
            
            return LGBMClassifier(**params)
        
        elif algorithm == "random_forest":
            from sklearn.ensemble import RandomForestClassifier
            
            if self.config.imbalanced_strategy == "class_weight":
                params.setdefault("class_weight", "balanced")
            
            params.setdefault("n_estimators", 100)
            params.setdefault("max_depth", 10)
            params.setdefault("random_state", self.config.random_state)
            
            return RandomForestClassifier(**params)
        
        elif algorithm == "isolation_forest":
            from sklearn.ensemble import IsolationForest
            
            params.setdefault("n_estimators", 100)
            params.setdefault("contamination", 0.05)
            params.setdefault("random_state", self.config.random_state)
            
            return IsolationForest(**params)
        
        else:
            raise ValueError(f"Unknown algorithm: {algorithm}")
    
    def _handle_imbalanced(
        self, 
        X: pd.DataFrame, 
        y: pd.Series
    ) -> Tuple[pd.DataFrame, pd.Series]:
        """Handle imbalanced data if needed."""
        if self.config.imbalanced_strategy == "smote":
            try:
                from imblearn.over_sampling import SMOTE
                smote = SMOTE(random_state=self.config.random_state)
                X_resampled, y_resampled = smote.fit_resample(X, y)
                logger.info(f"Applied SMOTE: {len(X)} -> {len(X_resampled)}")
                return pd.DataFrame(X_resampled, columns=X.columns), pd.Series(y_resampled)
            except ImportError:
                logger.warning("imblearn not installed, skipping SMOTE")
        
        elif self.config.imbalanced_strategy == "undersample":
            from sklearn.utils import resample
            
            X_combined = X.copy()
            X_combined["_target"] = y
            
            majority = X_combined[X_combined["_target"] == 0]
            minority = X_combined[X_combined["_target"] == 1]
            
            majority_downsampled = resample(
                majority,
                n_samples=len(minority),
                random_state=self.config.random_state
            )
            
            combined = pd.concat([majority_downsampled, minority])
            logger.info(f"Applied undersampling: {len(X)} -> {len(combined)}")
            
            return combined.drop("_target", axis=1), combined["_target"]
        
        return X, y
    
    def _get_probabilities(self, X: pd.DataFrame) -> np.ndarray:
        """Get prediction probabilities."""
        if hasattr(self.model, "predict_proba"):
            return self.model.predict_proba(X)[:, 1]
        elif hasattr(self.model, "decision_function"):
            return self.model.decision_function(X)
        else:
            return self.model.predict(X).astype(float)
    
    def _compute_metrics(
        self, 
        y_true: pd.Series, 
        y_pred: np.ndarray,
        y_prob: np.ndarray
    ) -> Dict[str, float]:
        """Compute evaluation metrics."""
        return {
            "precision": float(precision_score(y_true, y_pred, zero_division=0)),
            "recall": float(recall_score(y_true, y_pred, zero_division=0)),
            "f1": float(f1_score(y_true, y_pred, zero_division=0)),
            "auc": float(roc_auc_score(y_true, y_prob)),
            "accuracy": float((y_true == y_pred).mean()),
        }
    
    def _get_feature_importance(self) -> Dict[str, float]:
        """Get feature importance from model."""
        if hasattr(self.model, "feature_importances_"):
            importance = self.model.feature_importances_
            return dict(zip(self.feature_names, importance.tolist()))
        return {}
    
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Make predictions."""
        if self.pipeline is None:
            raise ValueError("Model not trained")
        return self.pipeline.predict(X)
    
    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """Get prediction probabilities."""
        if self.pipeline is None:
            raise ValueError("Model not trained")
        return self.pipeline.predict_proba(X)[:, 1]
    
    def _build_pipeline(self, y_train: pd.Series) -> Pipeline:
        """
        Build sklearn Pipeline with preprocessing + model.
        For tree-based models (XGBoost, LightGBM, RandomForest):
        - No scaling needed (tree models are scale-invariant)
        - FraudFeatureEngineer already handles all preprocessing
        For other models:
        - Add StandardScaler for better convergence
        """
        fraud_engineer = FraudFeatureEngineer()
        model = self._create_model(y_train)
        
        # Tree models don't need scaling
        if self.config.algorithm in ['xgboost', 'lightgbm', 'random_forest', 'isolation_forest']:
            pipeline = Pipeline([
                ('fraud_features', fraud_engineer),
                ('model', model)
            ])
            logger.info(f"Built pipeline for {self.config.algorithm} (no scaling)")
        else:
            # Future: other algorithms that benefit from scaling
            pipeline = Pipeline([
                ('fraud_features', fraud_engineer),
                ('scaler', StandardScaler()),
                ('model', model)
            ])
            logger.info(f"Built pipeline for {self.config.algorithm} (with scaling)")
        
        return pipeline