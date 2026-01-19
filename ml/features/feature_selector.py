"""
Feature Selection Pipeline
Selects the most informative features using multiple methods.
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from sklearn.feature_selection import mutual_info_classif, VarianceThreshold
from sklearn.preprocessing import StandardScaler
import logging

logger = logging.getLogger(__name__)


@dataclass
class FeatureSelectionConfig:
    """Configuration for feature selection."""
    max_features: int = 30
    variance_threshold: float = 0.01
    correlation_threshold: float = 0.95
    mi_weight: float = 0.5
    importance_weight: float = 0.5


class FeatureSelector:
    """
    Multi-stage feature selection pipeline.
    
    Stages:
    1. Variance Threshold - Remove near-constant features
    2. Correlation Filter - Remove highly correlated features
    3. Mutual Information - Rank by information gain
    4. Model Importance - Validate with XGBoost
    5. Combined Ranking - Select top N features
    """
    
    def __init__(self, config: FeatureSelectionConfig = None):
        self.config = config or FeatureSelectionConfig()
        self.selected_features: List[str] = []
        self.selection_report: Dict = {}
        self.scaler = StandardScaler()
    
    def fit_transform(
        self, 
        df: pd.DataFrame, 
        target_column: str,
        exclude_columns: List[str] = None
    ) -> Tuple[pd.DataFrame, Dict]:
        """
        Apply feature selection pipeline.
        
        Args:
            df: DataFrame with features
            target_column: Name of target column
            exclude_columns: Columns to exclude from selection
        
        Returns:
            Tuple of (selected features DataFrame, selection report)
        """
        exclude = set(exclude_columns or [])
        exclude.add(target_column)
        
        # Get feature columns
        feature_cols = [c for c in df.columns if c not in exclude and df[c].dtype in ['int64', 'float64']]
        
        X = df[feature_cols].copy()
        y = df[target_column].copy()
        
        # Handle missing values
        X = X.fillna(X.median())
        
        logger.info(f"Starting feature selection: {len(feature_cols)} features")
        
        # Stage 1: Variance filter
        X_var, var_removed = self._apply_variance_filter(X)
        logger.info(f"After variance filter: {X_var.shape[1]} features (removed {len(var_removed)})")
        
        # Stage 2: Correlation filter
        X_uncorr, corr_removed = self._apply_correlation_filter(X_var)
        logger.info(f"After correlation filter: {X_uncorr.shape[1]} features (removed {len(corr_removed)})")
        
        # Stage 3: Mutual Information
        mi_scores = self._compute_mutual_information(X_uncorr, y)
        logger.info(f"Computed mutual information scores")
        
        # Stage 4: Model importance
        importance_scores = self._compute_model_importance(X_uncorr, y)
        logger.info(f"Computed model importance scores")
        
        # Stage 5: Combined ranking
        self.selected_features = self._combine_rankings(
            mi_scores, 
            importance_scores, 
            max_features=self.config.max_features
        )
        logger.info(f"Selected {len(self.selected_features)} features")
        
        # Build report
        self.selection_report = {
            "stages": {
                "original": len(feature_cols),
                "after_variance": X_var.shape[1],
                "after_correlation": X_uncorr.shape[1],
                "final_selected": len(self.selected_features),
            },
            "removed": {
                "variance_filter": var_removed,
                "correlation_filter": corr_removed,
            },
            "scores": {
                f: {
                    "mutual_information": float(mi_scores.get(f, 0)),
                    "importance": float(importance_scores.get(f, 0)),
                    "rank": i + 1
                }
                for i, f in enumerate(self.selected_features)
            }
        }
        
        # Return selected features
        result = df[self.selected_features + [target_column]].copy()
        return result, self.selection_report
    
    def _apply_variance_filter(self, X: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
        """Remove features with low variance."""
        selector = VarianceThreshold(threshold=self.config.variance_threshold)
        
        # Fit and transform
        X_scaled = self.scaler.fit_transform(X)
        selector.fit(X_scaled)
        
        mask = selector.get_support()
        selected_cols = X.columns[mask].tolist()
        removed_cols = X.columns[~mask].tolist()
        
        return X[selected_cols], removed_cols
    
    def _apply_correlation_filter(self, X: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
        """Remove highly correlated features."""
        corr_matrix = X.corr().abs()
        
        # Get upper triangle
        upper = corr_matrix.where(
            np.triu(np.ones(corr_matrix.shape), k=1).astype(bool)
        )
        
        # Find columns with high correlation
        to_drop = [
            col for col in upper.columns 
            if any(upper[col] > self.config.correlation_threshold)
        ]
        
        return X.drop(columns=to_drop), to_drop
    
    def _compute_mutual_information(
        self, 
        X: pd.DataFrame, 
        y: pd.Series
    ) -> Dict[str, float]:
        """Compute mutual information scores."""
        scores = mutual_info_classif(X, y, random_state=42)
        return dict(zip(X.columns, scores))
    
    def _compute_model_importance(
        self, 
        X: pd.DataFrame, 
        y: pd.Series
    ) -> Dict[str, float]:
        """Compute feature importance using XGBoost."""
        try:
            from xgboost import XGBClassifier
            
            model = XGBClassifier(
                n_estimators=50,
                max_depth=5,
                learning_rate=0.1,
                random_state=42,
                verbosity=0,
                use_label_encoder=False,
                eval_metric="logloss"
            )
            model.fit(X, y)
            
            return dict(zip(X.columns, model.feature_importances_))
        except Exception as e:
            logger.warning(f"XGBoost importance failed: {e}, using zeros")
            return {col: 0.0 for col in X.columns}
    
    def _combine_rankings(
        self, 
        mi_scores: Dict[str, float],
        importance_scores: Dict[str, float],
        max_features: int
    ) -> List[str]:
        """Combine rankings from multiple methods."""
        features = list(mi_scores.keys())
        
        # Normalize scores
        mi_values = np.array([mi_scores[f] for f in features])
        imp_values = np.array([importance_scores[f] for f in features])
        
        # Handle edge cases
        if mi_values.max() > 0:
            mi_values = mi_values / mi_values.max()
        if imp_values.max() > 0:
            imp_values = imp_values / imp_values.max()
        
        # Weighted combination
        combined = (
            self.config.mi_weight * mi_values + 
            self.config.importance_weight * imp_values
        )
        
        # Sort and select top N
        sorted_indices = np.argsort(combined)[::-1]
        selected = [features[i] for i in sorted_indices[:max_features]]
        
        return selected
    
    def get_report(self) -> Dict:
        """Get the selection report."""
        return self.selection_report
