"""
Job Scheduler
Manages scheduled monitoring and maintenance tasks.
"""
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import asyncio
import logging

logger = logging.getLogger(__name__)


class JobStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class JobType(str, Enum):
    DRIFT_CHECK = "DRIFT_CHECK"
    BIAS_CHECK = "BIAS_CHECK"
    PERFORMANCE_CHECK = "PERFORMANCE_CHECK"
    MODEL_RETRAIN = "MODEL_RETRAIN"
    DATA_CLEANUP = "DATA_CLEANUP"


@dataclass
class ScheduledJob:
    """Represents a scheduled job."""
    id: str
    job_type: JobType
    schedule: str  # Cron expression or interval
    model_id: Optional[str]
    enabled: bool
    last_run: Optional[datetime]
    next_run: datetime
    status: JobStatus
    config: Dict[str, Any]


@dataclass
class JobRun:
    """Record of a job execution."""
    id: str
    job_id: str
    job_type: JobType
    started_at: datetime
    completed_at: Optional[datetime]
    status: JobStatus
    result: Optional[Dict]
    error: Optional[str]


class JobScheduler:
    """
    Manages scheduled monitoring jobs.
    
    Default scheduled jobs:
    - Drift check: Every hour
    - Bias check: Every 6 hours
    - Performance check: Every hour
    """
    
    # Default schedules
    DEFAULT_SCHEDULES = {
        JobType.DRIFT_CHECK: "0 * * * *",      # Every hour
        JobType.BIAS_CHECK: "0 */6 * * *",     # Every 6 hours
        JobType.PERFORMANCE_CHECK: "30 * * * *", # Every hour at :30
    }
    
    def __init__(self):
        self._jobs: Dict[str, ScheduledJob] = {}
        self._runs: Dict[str, JobRun] = {}
        self._handlers: Dict[JobType, Callable] = {}
        
        # Register default handlers
        self._register_default_handlers()
    
    def _register_default_handlers(self):
        """Register default job handlers."""
        self._handlers[JobType.DRIFT_CHECK] = self._run_drift_check
        self._handlers[JobType.BIAS_CHECK] = self._run_bias_check
        self._handlers[JobType.PERFORMANCE_CHECK] = self._run_performance_check
    
    async def _run_drift_check(self, job: ScheduledJob) -> Dict:
        """Run drift check job."""
        logger.info(f"Running drift check for model {job.model_id}")
        
        # In production, this would call DriftMonitoringService
        return {
            "status": "completed",
            "features_checked": 30,
            "drifted_features": 2,
            "alerts_created": 1,
        }
    
    async def _run_bias_check(self, job: ScheduledJob) -> Dict:
        """Run bias check job."""
        logger.info(f"Running bias check for model {job.model_id}")
        
        return {
            "status": "completed",
            "protected_attributes_checked": 3,
            "bias_detected": 0,
        }
    
    async def _run_performance_check(self, job: ScheduledJob) -> Dict:
        """Run performance check job."""
        logger.info(f"Running performance check for model {job.model_id}")
        
        return {
            "status": "completed",
            "metrics_checked": 5,
            "baseline_violations": 0,
        }
    
    def create_job(
        self,
        job_type: JobType,
        model_id: Optional[str] = None,
        schedule: Optional[str] = None,
        config: Optional[Dict] = None,
    ) -> ScheduledJob:
        """Create a new scheduled job."""
        from uuid import uuid4
        
        job = ScheduledJob(
            id=str(uuid4()),
            job_type=job_type,
            schedule=schedule or self.DEFAULT_SCHEDULES.get(job_type, "0 * * * *"),
            model_id=model_id,
            enabled=True,
            last_run=None,
            next_run=datetime.utcnow() + timedelta(hours=1),
            status=JobStatus.PENDING,
            config=config or {},
        )
        
        self._jobs[job.id] = job
        logger.info(f"Created job {job.id}: {job_type.value}")
        
        return job
    
    async def run_job(self, job_id: str) -> JobRun:
        """Manually trigger a job run."""
        job = self._jobs.get(job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")
        
        from uuid import uuid4
        
        run = JobRun(
            id=str(uuid4()),
            job_id=job_id,
            job_type=job.job_type,
            started_at=datetime.utcnow(),
            completed_at=None,
            status=JobStatus.RUNNING,
            result=None,
            error=None,
        )
        
        self._runs[run.id] = run
        job.status = JobStatus.RUNNING
        
        try:
            handler = self._handlers.get(job.job_type)
            if handler:
                result = await handler(job)
                run.result = result
                run.status = JobStatus.COMPLETED
                job.status = JobStatus.COMPLETED
            else:
                raise ValueError(f"No handler for job type {job.job_type}")
                
        except Exception as e:
            run.error = str(e)
            run.status = JobStatus.FAILED
            job.status = JobStatus.FAILED
            logger.error(f"Job {job_id} failed: {e}")
        
        run.completed_at = datetime.utcnow()
        job.last_run = run.completed_at
        
        # Schedule next run
        job.next_run = self._calculate_next_run(job.schedule)
        
        return run
    
    def _calculate_next_run(self, schedule: str) -> datetime:
        """Calculate next run time from cron expression."""
        # Simplified - just add 1 hour
        # In production, use croniter library
        return datetime.utcnow() + timedelta(hours=1)
    
    def list_jobs(
        self,
        job_type: Optional[JobType] = None,
        model_id: Optional[str] = None,
    ) -> List[ScheduledJob]:
        """List scheduled jobs."""
        jobs = list(self._jobs.values())
        
        if job_type:
            jobs = [j for j in jobs if j.job_type == job_type]
        
        if model_id:
            jobs = [j for j in jobs if j.model_id == model_id]
        
        return jobs
    
    def get_job_runs(
        self,
        job_id: Optional[str] = None,
        limit: int = 10,
    ) -> List[JobRun]:
        """Get job run history."""
        runs = list(self._runs.values())
        
        if job_id:
            runs = [r for r in runs if r.job_id == job_id]
        
        runs.sort(key=lambda r: r.started_at, reverse=True)
        return runs[:limit]
    
    def enable_job(self, job_id: str) -> bool:
        """Enable a job."""
        job = self._jobs.get(job_id)
        if job:
            job.enabled = True
            return True
        return False
    
    def disable_job(self, job_id: str) -> bool:
        """Disable a job."""
        job = self._jobs.get(job_id)
        if job:
            job.enabled = False
            return True
        return False
    
    def delete_job(self, job_id: str) -> bool:
        """Delete a job."""
        if job_id in self._jobs:
            del self._jobs[job_id]
            return True
        return False


# Singleton scheduler instance
_scheduler: Optional[JobScheduler] = None


def get_scheduler() -> JobScheduler:
    """Get the global job scheduler instance."""
    global _scheduler
    if _scheduler is None:
        _scheduler = JobScheduler()
    return _scheduler
