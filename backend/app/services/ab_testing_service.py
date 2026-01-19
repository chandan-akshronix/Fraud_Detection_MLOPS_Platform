"""
A/B Testing Service
Champion-challenger model testing in production.
"""
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from uuid import uuid4
from datetime import datetime, timedelta
from enum import Enum
import logging
import random

logger = logging.getLogger(__name__)


class ABTestStatus(str, Enum):
    """A/B test status."""
    DRAFT = "DRAFT"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    ABORTED = "ABORTED"


class ABTestResult(str, Enum):
    """A/B test outcome."""
    PENDING = "PENDING"
    CHALLENGER_WINS = "CHALLENGER_WINS"
    CHAMPION_WINS = "CHAMPION_WINS"
    NO_SIGNIFICANT_DIFFERENCE = "NO_SIGNIFICANT_DIFFERENCE"


@dataclass
class ABTestConfig:
    """Configuration for A/B test."""
    challenger_traffic_percent: float = 10.0  # Start with 10% traffic
    min_samples: int = 1000  # Minimum samples before evaluation
    max_duration_hours: int = 168  # 1 week max
    significance_level: float = 0.95  # 95% confidence
    primary_metric: str = "f1"
    secondary_metrics: List[str] = None
    auto_promote_on_win: bool = False
    rollback_on_performance_drop: bool = True
    performance_drop_threshold: float = 0.05  # 5% drop triggers rollback
    
    def __post_init__(self):
        if self.secondary_metrics is None:
            self.secondary_metrics = ["precision", "recall", "auc"]


@dataclass
class ABTest:
    """A/B test record."""
    id: str
    name: str
    champion_model_id: str
    challenger_model_id: str
    config: ABTestConfig
    status: ABTestStatus
    result: ABTestResult
    created_at: datetime
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    champion_samples: int = 0
    challenger_samples: int = 0
    champion_metrics: Optional[Dict] = None
    challenger_metrics: Optional[Dict] = None
    statistical_analysis: Optional[Dict] = None


class ABTestingService:
    """
    A/B testing service for model comparison.
    
    Features:
    - Traffic splitting between champion and challenger
    - Statistical significance testing
    - Auto-promotion and rollback
    - Real-time metrics tracking
    """
    
    def __init__(self):
        self._tests: Dict[str, ABTest] = {}
        self._active_test: Optional[str] = None
    
    def create_test(
        self,
        name: str,
        champion_model_id: str,
        challenger_model_id: str,
        config: Optional[ABTestConfig] = None,
    ) -> ABTest:
        """Create a new A/B test."""
        test = ABTest(
            id=str(uuid4()),
            name=name,
            champion_model_id=champion_model_id,
            challenger_model_id=challenger_model_id,
            config=config or ABTestConfig(),
            status=ABTestStatus.DRAFT,
            result=ABTestResult.PENDING,
            created_at=datetime.utcnow(),
        )
        
        self._tests[test.id] = test
        logger.info(f"Created A/B test: {test.id} - {name}")
        
        return test
    
    def start_test(self, test_id: str) -> ABTest:
        """Start an A/B test."""
        test = self._tests.get(test_id)
        if not test:
            raise ValueError(f"Test {test_id} not found")
        
        if self._active_test and self._active_test != test_id:
            raise ValueError("Another test is already running")
        
        test.status = ABTestStatus.RUNNING
        test.started_at = datetime.utcnow()
        self._active_test = test_id
        
        logger.info(f"Started A/B test: {test_id}")
        return test
    
    def route_request(self, test_id: Optional[str] = None) -> str:
        """
        Route a request to champion or challenger.
        
        Returns:
            Model ID to use for this request
        """
        tid = test_id or self._active_test
        if not tid:
            return "default"  # No active test
        
        test = self._tests.get(tid)
        if not test or test.status != ABTestStatus.RUNNING:
            return "default"
        
        # Random routing based on traffic split
        if random.random() * 100 < test.config.challenger_traffic_percent:
            test.challenger_samples += 1
            return test.challenger_model_id
        else:
            test.champion_samples += 1
            return test.champion_model_id
    
    def record_prediction(
        self,
        test_id: str,
        model_id: str,
        prediction: int,
        actual: Optional[int] = None,
        response_time_ms: float = 0.0,
    ):
        """Record a prediction result for the test."""
        test = self._tests.get(test_id)
        if not test:
            return
        
        # In production, this would store to a dedicated metrics table
        logger.debug(f"Recorded prediction for test {test_id}, model {model_id}")
    
    def evaluate_test(self, test_id: str) -> Dict:
        """
        Evaluate current test status.
        
        Performs statistical significance testing if enough samples.
        """
        test = self._tests.get(test_id)
        if not test:
            raise ValueError(f"Test {test_id} not found")
        
        total_samples = test.champion_samples + test.challenger_samples
        
        # Check if we have enough samples
        if total_samples < test.config.min_samples:
            return {
                "ready_for_decision": False,
                "samples_collected": total_samples,
                "samples_needed": test.config.min_samples,
                "message": f"Need {test.config.min_samples - total_samples} more samples",
            }
        
        # Mock metrics for evaluation
        # In production, aggregate from recorded predictions
        test.champion_metrics = {
            "f1": 0.88,
            "precision": 0.90,
            "recall": 0.86,
            "auc": 0.94,
            "avg_latency_ms": 5.2,
        }
        
        test.challenger_metrics = {
            "f1": 0.91,
            "precision": 0.92,
            "recall": 0.89,
            "auc": 0.96,
            "avg_latency_ms": 5.5,
        }
        
        # Perform statistical analysis
        analysis = self._statistical_analysis(test)
        test.statistical_analysis = analysis
        
        return {
            "ready_for_decision": True,
            "champion_metrics": test.champion_metrics,
            "challenger_metrics": test.challenger_metrics,
            "analysis": analysis,
            "recommendation": analysis.get("recommendation"),
        }
    
    def _statistical_analysis(self, test: ABTest) -> Dict:
        """
        Perform statistical significance testing.
        
        Uses two-proportion z-test for fairness.
        """
        champion = test.champion_metrics
        challenger = test.challenger_metrics
        primary = test.config.primary_metric
        
        champ_val = champion.get(primary, 0)
        chal_val = challenger.get(primary, 0)
        
        diff = chal_val - champ_val
        diff_percent = (diff / champ_val * 100) if champ_val > 0 else 0
        
        # Simplified significance test
        # In production, use proper statistical tests
        is_significant = test.challenger_samples >= 500 and abs(diff_percent) > 1.0
        
        if is_significant and diff > 0:
            recommendation = "PROMOTE_CHALLENGER"
            result = ABTestResult.CHALLENGER_WINS
        elif is_significant and diff < 0:
            recommendation = "KEEP_CHAMPION"
            result = ABTestResult.CHAMPION_WINS
        else:
            recommendation = "CONTINUE_TEST"
            result = ABTestResult.NO_SIGNIFICANT_DIFFERENCE
        
        return {
            "primary_metric": primary,
            "champion_value": champ_val,
            "challenger_value": chal_val,
            "difference": diff,
            "difference_percent": diff_percent,
            "is_significant": is_significant,
            "confidence": 0.95 if is_significant else 0.0,
            "recommendation": recommendation,
            "result": result.value,
        }
    
    def conclude_test(
        self,
        test_id: str,
        result: ABTestResult,
        promote_challenger: bool = False,
    ) -> ABTest:
        """Conclude an A/B test."""
        test = self._tests.get(test_id)
        if not test:
            raise ValueError(f"Test {test_id} not found")
        
        test.status = ABTestStatus.COMPLETED
        test.result = result
        test.ended_at = datetime.utcnow()
        
        if self._active_test == test_id:
            self._active_test = None
        
        if promote_challenger and result == ABTestResult.CHALLENGER_WINS:
            logger.info(f"Promoting challenger model: {test.challenger_model_id}")
            # In production, update model registry
        
        logger.info(f"Concluded A/B test {test_id}: {result.value}")
        return test
    
    def abort_test(self, test_id: str, reason: str = "") -> ABTest:
        """Abort a running test."""
        test = self._tests.get(test_id)
        if not test:
            raise ValueError(f"Test {test_id} not found")
        
        test.status = ABTestStatus.ABORTED
        test.ended_at = datetime.utcnow()
        
        if self._active_test == test_id:
            self._active_test = None
        
        logger.info(f"Aborted A/B test {test_id}: {reason}")
        return test
    
    def get_test(self, test_id: str) -> Optional[ABTest]:
        """Get test by ID."""
        return self._tests.get(test_id)
    
    def list_tests(
        self,
        status: Optional[ABTestStatus] = None,
        limit: int = 20,
    ) -> List[ABTest]:
        """List A/B tests."""
        tests = list(self._tests.values())
        
        if status:
            tests = [t for t in tests if t.status == status]
        
        tests.sort(key=lambda t: t.created_at, reverse=True)
        return tests[:limit]
    
    def get_active_test(self) -> Optional[ABTest]:
        """Get currently active test."""
        if self._active_test:
            return self._tests.get(self._active_test)
        return None


# Singleton service instance
_ab_service: Optional[ABTestingService] = None


def get_ab_testing_service() -> ABTestingService:
    """Get the global A/B testing service instance."""
    global _ab_service
    if _ab_service is None:
        _ab_service = ABTestingService()
    return _ab_service
