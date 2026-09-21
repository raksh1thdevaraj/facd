"""Asynchronous task runner interface and FastAPI BackgroundTasks execution adapter."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Optional

from fastapi import BackgroundTasks

from app.database import SessionLocal
from app.services.pipeline_orchestrator import VerificationPipelineOrchestrator

logger = logging.getLogger(__name__)


class AsyncTaskRunner(ABC):
    """Abstract interface for dispatching asynchronous verification pipeline jobs."""

    @abstractmethod
    def dispatch(
        self, certificate_id: str, background_tasks: Optional[BackgroundTasks] = None
    ) -> None:
        """Dispatch certificate verification pipeline for background execution."""
        pass


class FastAPIBackgroundTaskRunner(AsyncTaskRunner):
    """Executes verification pipeline in background threads using FastAPI BackgroundTasks."""

    def __init__(self) -> None:
        self.orchestrator = VerificationPipelineOrchestrator()

    def dispatch(
        self, certificate_id: str, background_tasks: Optional[BackgroundTasks] = None
    ) -> None:
        """Schedule pipeline execution on BackgroundTasks or run synchronously as fallback."""
        if background_tasks is not None:
            background_tasks.add_task(self._execute_job, certificate_id)
        else:
            self._execute_job(certificate_id)

    def _execute_job(self, certificate_id: str) -> None:
        """Worker function running in a separate thread with dedicated database session."""
        db = SessionLocal()
        try:
            logger.info(
                "Starting background verification pipeline for certificate: %s", certificate_id
            )
            self.orchestrator.run_pipeline(certificate_id=certificate_id, db=db)
            logger.info(
                "Successfully completed verification pipeline for certificate: %s", certificate_id
            )
        except Exception as e:
            logger.error("Background job failed for certificate %s: %s", certificate_id, e)
        finally:
            db.close()


def get_task_runner() -> AsyncTaskRunner:
    """Dependency provider returning active AsyncTaskRunner implementation."""
    return FastAPIBackgroundTaskRunner()
