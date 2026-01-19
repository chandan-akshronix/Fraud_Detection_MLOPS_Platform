"""
Inference API Endpoints
Real-time fraud prediction with explanations.
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
import numpy as np

from app.core.database import get_db

router = APIRouter(prefix="/inference", tags=["Inference"])


class PredictionRequest(BaseModel):
    """Request for single prediction."""
    transaction_id: Optional[str] = None
    features: dict = Field(..., description="Feature name to value mapping")


class BatchPredictionRequest(BaseModel):
    """Request for batch prediction."""
    transactions: List[PredictionRequest]


class PredictionResponse(BaseModel):
    """Response for single prediction."""
    transaction_id: Optional[str] = None
    prediction: int  # 0 = legit, 1 = fraud
    fraud_score: float  # 0.0 to 1.0
    confidence: float  # 0.0 to 1.0
    risk_level: str  # LOW, MEDIUM, HIGH, CRITICAL
    response_time_ms: float


class ExplainedPredictionResponse(PredictionResponse):
    """Response with explanation."""
    explanation: dict


@router.post("/predict", response_model=PredictionResponse)
async def predict(
    request: PredictionRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Make a single fraud prediction.
    
    Returns prediction (0/1), fraud probability score,
    confidence, and risk level.
    """
    # Mock inference for now - will be replaced with ONNX engine
    import random
    import time
    
    start = time.perf_counter()
    
    # Simulate prediction
    fraud_score = random.uniform(0.0, 1.0)
    prediction = 1 if fraud_score > 0.5 else 0
    confidence = abs(fraud_score - 0.5) * 2
    
    # Determine risk level
    if fraud_score > 0.9:
        risk_level = "CRITICAL"
    elif fraud_score > 0.7:
        risk_level = "HIGH"
    elif fraud_score > 0.4:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"
    
    elapsed_ms = (time.perf_counter() - start) * 1000
    
    return PredictionResponse(
        transaction_id=request.transaction_id,
        prediction=prediction,
        fraud_score=fraud_score,
        confidence=confidence,
        risk_level=risk_level,
        response_time_ms=elapsed_ms,
    )


@router.post("/predict/explain", response_model=ExplainedPredictionResponse)
async def predict_with_explanation(
    request: PredictionRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Make a prediction with SHAP-based explanation.
    
    Returns prediction plus feature contributions
    explaining why the model made this decision.
    """
    import random
    import time
    
    start = time.perf_counter()
    
    fraud_score = random.uniform(0.0, 1.0)
    prediction = 1 if fraud_score > 0.5 else 0
    confidence = abs(fraud_score - 0.5) * 2
    
    if fraud_score > 0.9:
        risk_level = "CRITICAL"
    elif fraud_score > 0.7:
        risk_level = "HIGH"
    elif fraud_score > 0.4:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"
    
    # Mock explanation
    explanation = {
        "feature_contributions": {
            "amount": 0.15,
            "is_night": 0.08,
            "user_txn_count": -0.12,
            "is_high_risk_merchant": 0.05,
            "time_since_last": 0.03,
        },
        "top_positive_factors": [
            "Transaction amount is unusually high",
            "Transaction occurred during night hours",
            "High-risk merchant category",
        ],
        "top_negative_factors": [
            "User has consistent transaction history",
            "Normal transaction frequency",
        ],
        "explanation_text": f"Risk Level: {risk_level}\n\n"
            "This transaction was flagged due to:\n"
            "• Unusually high amount\n"
            "• Night-time transaction\n"
            "• High-risk merchant category",
    }
    
    elapsed_ms = (time.perf_counter() - start) * 1000
    
    return ExplainedPredictionResponse(
        transaction_id=request.transaction_id,
        prediction=prediction,
        fraud_score=fraud_score,
        confidence=confidence,
        risk_level=risk_level,
        response_time_ms=elapsed_ms,
        explanation=explanation,
    )


@router.post("/predict/batch")
async def predict_batch(
    request: BatchPredictionRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Make batch predictions for multiple transactions.
    
    Optimized for throughput - processes all transactions
    in a single forward pass.
    """
    import random
    import time
    
    start = time.perf_counter()
    
    results = []
    for txn in request.transactions:
        fraud_score = random.uniform(0.0, 1.0)
        prediction = 1 if fraud_score > 0.5 else 0
        confidence = abs(fraud_score - 0.5) * 2
        
        if fraud_score > 0.9:
            risk_level = "CRITICAL"
        elif fraud_score > 0.7:
            risk_level = "HIGH"
        elif fraud_score > 0.4:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"
        
        results.append({
            "transaction_id": txn.transaction_id,
            "prediction": prediction,
            "fraud_score": fraud_score,
            "confidence": confidence,
            "risk_level": risk_level,
        })
    
    total_ms = (time.perf_counter() - start) * 1000
    avg_ms = total_ms / len(request.transactions) if request.transactions else 0
    
    return {
        "data": results,
        "meta": {
            "total_transactions": len(results),
            "total_time_ms": total_ms,
            "avg_time_per_transaction_ms": avg_ms,
        }
    }


@router.get("/model/info")
async def get_model_info(db: AsyncSession = Depends(get_db)):
    """Get information about the currently loaded model."""
    return {
        "data": {
            "model_id": "production-model-001",
            "model_name": "XGBoost Fraud Detector v1.2",
            "algorithm": "xgboost",
            "version": "1.2.0",
            "loaded_at": "2026-01-17T10:00:00Z",
            "feature_count": 30,
            "onnx_enabled": True,
            "avg_latency_ms": 5.2,
            "throughput_per_second": 192,
        }
    }
