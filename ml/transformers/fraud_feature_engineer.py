"""
Fraud Feature Engineer
Custom sklearn transformer for fraud detection feature engineering.
Handles pandas preprocessing with precautions for tree-based models.
"""
from sklearn.base import BaseEstimator, TransformerMixin
import pandas as pd
import numpy as np
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class FraudFeatureEngineer(BaseEstimator, TransformerMixin):
    """
    Custom transformer for fraud detection features.
    
    Compatible with sklearn Pipeline and tree-based models (XGBoost, LightGBM).
    Implements critical precautions for pandas preprocessing:
    - Resets index to avoid misalignment
    - Converts all dtypes to numeric (float32)
    - Enforces consistent feature order
    - Uses label encoding for categorical features
    
    Parameters
    ----------
    cache : Optional[Any]
        Cache object for velocity features (Redis, dict, etc.)
    db_connection : Optional[Any]
        Database connection for user history lookups
    
    Attributes
    ----------
    feature_names_in_ : list
        Input feature names from training
    feature_names_out_ : list
        Output feature names (enforced order)
    user_avg_amount_ : pd.Series
        User average transaction amounts (learned during fit)
    merchant_fraud_rate_ : pd.Series
        Merchant fraud rates (learned during fit)
    """
    
    def __init__(self, cache: Optional[Any] = None, db_connection: Optional[Any] = None):
        self.cache = cache
        self.db_connection = db_connection
    
    def fit(self, X: pd.DataFrame, y: Optional[pd.Series] = None) -> 'FraudFeatureEngineer':
        """
        Fit on training data to learn feature statistics.
        
        Parameters
        ----------
        X : pd.DataFrame
            Training data with columns: amount, user_id, merchant_id, timestamp, etc.
        y : pd.Series, optional
            Target variable (fraud labels)
        
        Returns
        -------
        self : FraudFeatureEngineer
            Fitted transformer
        """
        # Validate input
        if not isinstance(X, pd.DataFrame):
            raise TypeError("X must be a pandas DataFrame")
        
        # Store input schema
        self.feature_names_in_ = list(X.columns)
        self.dtypes_in_ = X.dtypes.to_dict()
        
        # Learn user statistics
        if 'user_id' in X.columns and 'amount' in X.columns:
            self.user_avg_amount_ = X.groupby('user_id')['amount'].mean()
        else:
            self.user_avg_amount_ = pd.Series(dtype=float)
        
        # Learn merchant fraud rates (if labels available)
        if y is not None and 'merchant_id' in X.columns:
            X_with_labels = X.copy()
            X_with_labels['_fraud_label'] = y.values
            self.merchant_fraud_rate_ = X_with_labels.groupby('merchant_id')['_fraud_label'].mean()
        else:
            self.merchant_fraud_rate_ = pd.Series(dtype=float)
        
        # Transform to get output feature names
        X_transformed = self._transform_impl(X)
        self.feature_names_out_ = list(X_transformed.columns)
        
        logger.info(f"FraudFeatureEngineer fitted: {len(X)} samples, "
                   f"{len(self.feature_names_in_)} input features → "
                   f"{len(self.feature_names_out_)} output features")
        
        return self
    
    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        """
        Transform features using learned statistics.
        
        Parameters
        ----------
        X : pd.DataFrame
            Data to transform
        
        Returns
        -------
        X_transformed : pd.DataFrame
            Transformed features (all numeric, consistent order)
        """
        # Validate input schema
        self._validate_input(X)
        
        # Transform
        X_transformed = self._transform_impl(X)
        
        # CRITICAL: Enforce feature order (training = inference)
        X_transformed = X_transformed[self.feature_names_out_]
        
        # CRITICAL: Reset index to avoid misalignment
        X_transformed = X_transformed.reset_index(drop=True)
        
        # Validate output
        self._validate_output(X_transformed)
        
        return X_transformed
    
    def _validate_input(self, X: pd.DataFrame) -> None:
        """Validate input schema matches training."""
        if not isinstance(X, pd.DataFrame):
            raise TypeError("X must be a pandas DataFrame")
        
        # Check for missing required columns
        required_cols = {'amount', 'timestamp'}
        missing_cols = required_cols - set(X.columns)
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")
    
    def _validate_output(self, X: pd.DataFrame) -> None:
        """Validate output features."""
        # Check for NaN (log warning, don't fail - tree models handle NaN)
        nan_cols = X.columns[X.isna().any()].tolist()
        if nan_cols:
            logger.warning(f"NaN values in columns: {nan_cols} (tree models will handle)")
        
        # Check all columns are numeric
        non_numeric = X.select_dtypes(exclude=[np.number]).columns.tolist()
        if non_numeric:
            raise ValueError(f"Non-numeric columns detected: {non_numeric}")
        
        # Check dtypes are float32 or float64
        for col in X.columns:
            if X[col].dtype not in [np.float32, np.float64]:
                logger.warning(f"Column {col} has dtype {X[col].dtype}, expected float32/float64")
    
    def _transform_impl(self, X: pd.DataFrame) -> pd.DataFrame:
        """
        Actual transformation logic.
        Implements all fraud detection features.
        """
        X = X.copy()
        
        # ===== TIME-BASED FEATURES =====
        timestamp = pd.to_datetime(X['timestamp'])
        X['hour'] = timestamp.dt.hour.astype(np.float32)
        X['day_of_week'] = timestamp.dt.dayofweek.astype(np.float32)
        X['is_weekend'] = (X['day_of_week'] >= 5).astype(np.float32)
        X['is_night'] = ((X['hour'] >= 22) | (X['hour'] <= 6)).astype(np.float32)
        X['day_of_month'] = timestamp.dt.day.astype(np.float32)
        
        # ===== VELOCITY FEATURES (from cache) =====
        if self.cache and 'user_id' in X.columns:
            X['user_txn_count_1h'] = X['user_id'].apply(
                lambda uid: float(self.cache.get(f'txn_count_1h:{uid}', 0))
            )
            X['user_txn_count_24h'] = X['user_id'].apply(
                lambda uid: float(self.cache.get(f'txn_count_24h:{uid}', 0))
            )
        else:
            X['user_txn_count_1h'] = 0.0
            X['user_txn_count_24h'] = 0.0
        
        # ===== DERIVED FEATURES =====
        # Amount transformations
        X['amount_log'] = np.log1p(X['amount']).astype(np.float32)
        X['amount_sqrt'] = np.sqrt(X['amount']).astype(np.float32)
        
        # Amount vs user average
        if 'user_id' in X.columns and len(self.user_avg_amount_) > 0:
            X['amount_vs_user_avg'] = (
                X['amount'] / X['user_id'].map(self.user_avg_amount_).fillna(X['amount'].mean())
            ).astype(np.float32)
        else:
            X['amount_vs_user_avg'] = 1.0
        
        # Merchant risk score
        if 'merchant_id' in X.columns and len(self.merchant_fraud_rate_) > 0:
            X['merchant_risk_score'] = X['merchant_id'].map(self.merchant_fraud_rate_).fillna(0.5).astype(np.float32)
        else:
            X['merchant_risk_score'] = 0.5
        
        # ===== CATEGORICAL ENCODING (Label encoding for tree models) =====
        # Don't use one-hot encoding for tree models!
        if 'merchant_category' in X.columns:
            X['merchant_category_code'] = X['merchant_category'].astype('category').cat.codes.astype(np.float32)
        
        if 'device_type' in X.columns:
            X['device_type_code'] = X['device_type'].astype('category').cat.codes.astype(np.float32)
        
        if 'payment_method' in X.columns:
            X['payment_method_code'] = X['payment_method'].astype('category').cat.codes.astype(np.float32)
        
        # ===== CLEANUP =====
        # Drop original columns that were transformed
        cols_to_drop = [
            'timestamp', 'user_id', 'merchant_id', 
            'merchant_category', 'device_type', 'payment_method'
        ]
        X = X.drop(cols_to_drop, axis=1, errors='ignore')
        
        # Ensure all columns are numeric
        X = X.select_dtypes(include=[np.number])
        
        # Convert all to float32 for memory efficiency
        for col in X.columns:
            if X[col].dtype == np.float64:
                X[col] = X[col].astype(np.float32)
        
        return X
    
    def get_feature_names_out(self, input_features: Optional[list] = None) -> list:
        """
        Get output feature names.
        Compatible with sklearn's get_feature_names_out() interface.
        """
        return self.feature_names_out_
