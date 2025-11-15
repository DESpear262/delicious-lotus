"""RQ job callbacks for updating composition status in database."""

import logging
from typing import Any
from uuid import UUID

from db.models.composition import Composition, CompositionStatus
from rq.job import Job
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.config import settings

logger = logging.getLogger(__name__)


def _get_sync_session() -> Session:
    """Get a synchronous database session.

    Returns:
        Session: Synchronous SQLAlchemy session
    """
    # Convert async database URL to sync
    db_url = str(settings.database_url)
    if db_url.startswith("postgresql+asyncpg://"):
        db_url = db_url.replace("postgresql+asyncpg://", "postgresql+psycopg2://")
    elif db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+psycopg2://")

    engine = create_engine(db_url, pool_pre_ping=True)
    return Session(engine)


def _update_composition_status_sync(
    composition_id: UUID,
    status: CompositionStatus,
    output_url: str | None = None,
    error_message: str | None = None,
) -> None:
    """Update composition status in database (synchronous).

    Args:
        composition_id: ID of composition to update
        status: New composition status
        output_url: Output URL if completed successfully
        error_message: Error message if failed
    """
    session = _get_sync_session()

    try:
        # Query composition
        result = session.execute(select(Composition).where(Composition.id == composition_id))
        composition = result.scalar_one_or_none()

        if not composition:
            logger.error(
                f"Composition {composition_id} not found for status update",
                extra={"composition_id": str(composition_id), "new_status": status.value},
            )
            return

        # Update status
        composition.status = status

        # Update output URL if provided
        if output_url:
            composition.output_url = output_url

        # Update error message if provided
        if error_message:
            composition.error_message = error_message

        # Commit changes
        session.commit()

        logger.info(
            f"Updated composition {composition_id} status to {status.value}",
            extra={
                "composition_id": str(composition_id),
                "status": status.value,
                "has_output_url": output_url is not None,
                "has_error": error_message is not None,
            },
        )

    except Exception as e:
        logger.exception(
            f"Failed to update composition {composition_id} status",
            extra={
                "composition_id": str(composition_id),
                "status": status.value,
                "error": str(e),
            },
        )
        session.rollback()
        raise
    finally:
        session.close()


def on_job_success(job: Job, connection: Any, result: Any, *args: Any, **kwargs: Any) -> None:
    """Callback when job completes successfully.

    This callback is called by RQ after a job completes successfully.
    It updates the composition status to COMPLETED or FAILED in the database.

    Args:
        job: RQ Job instance
        connection: Redis connection
        result: Job execution result
        *args: Additional arguments
        **kwargs: Additional keyword arguments
    """
    logger.info(
        f"Job {job.id} completed",
        extra={"job_id": job.id, "result": str(result)[:200]},
    )

    try:
        composition_id = None

        # First try to get composition_id from result
        if isinstance(result, dict):
            # Check if job actually failed (success=False)
            if result.get("success") is False:
                # Job failed but didn't raise exception - treat as failure
                error_msg = result.get("error", "Job failed without error message")

                # Try to get composition_id from result or job kwargs
                composition_id_str = result.get("composition_id")
                if not composition_id_str and hasattr(job, "kwargs") and job.kwargs:
                    composition_id_str = job.kwargs.get("composition_id")

                if composition_id_str:
                    composition_id = UUID(composition_id_str) if isinstance(composition_id_str, str) else composition_id_str

                    _update_composition_status_sync(
                        composition_id=composition_id,
                        status=CompositionStatus.FAILED,
                        error_message=str(error_msg)[:1000],
                    )

                    logger.info(
                        f"Marked composition {composition_id} as FAILED",
                        extra={"composition_id": str(composition_id), "error": str(error_msg)[:200]},
                    )
                else:
                    logger.warning(
                        f"Job {job.id} failed but composition_id not found",
                        extra={"job_id": job.id, "result": result},
                    )
                return

            # Job succeeded - get composition_id
            composition_id_str = result.get("composition_id")
            if composition_id_str:
                composition_id = UUID(composition_id_str)
                output_url = result.get("result", {}).get("output_url") if result.get("result") else None

                # Update composition status to COMPLETED
                _update_composition_status_sync(
                    composition_id=composition_id,
                    status=CompositionStatus.COMPLETED,
                    output_url=output_url,
                )

                logger.info(
                    f"Marked composition {composition_id} as COMPLETED",
                    extra={"composition_id": str(composition_id)},
                )
            else:
                logger.warning(
                    f"Job {job.id} result missing composition_id",
                    extra={"job_id": job.id, "result": result},
                )
        else:
            logger.warning(
                f"Job {job.id} result format unexpected",
                extra={"job_id": job.id, "result_type": type(result).__name__},
            )

    except Exception as e:
        logger.exception(
            f"Failed to process job success callback for {job.id}",
            extra={"job_id": job.id, "error": str(e)},
        )


def on_job_failure(job: Job, connection: Any, type: Any, value: Any, traceback: Any) -> None:
    """Callback when job fails.

    This callback is called by RQ after a job fails.
    It updates the composition status to FAILED in the database.

    Args:
        job: RQ Job instance
        connection: Redis connection
        type: Exception type
        value: Exception value
        traceback: Exception traceback
    """
    error_msg = str(value) if value else "Unknown error"

    logger.error(
        f"Job {job.id} failed",
        extra={
            "job_id": job.id,
            "error_type": type.__name__ if type else "Unknown",
            "error": error_msg,
        },
    )

    try:
        # Try to extract composition_id from job kwargs
        composition_id = None

        if hasattr(job, "kwargs") and job.kwargs:
            composition_id_value = job.kwargs.get("composition_id")
            if composition_id_value:
                if isinstance(composition_id_value, UUID):
                    composition_id = composition_id_value
                elif isinstance(composition_id_value, str):
                    composition_id = UUID(composition_id_value)

        # If not in kwargs, try to get from job result (might have been set before failure)
        if not composition_id and hasattr(job, "result") and isinstance(job.result, dict):
            composition_id_str = job.result.get("composition_id")
            if composition_id_str:
                composition_id = UUID(composition_id_str)

        if composition_id:
            # Update composition status to FAILED
            _update_composition_status_sync(
                composition_id=composition_id,
                status=CompositionStatus.FAILED,
                error_message=error_msg[:1000],  # Limit error message length
            )

            logger.info(
                f"Marked composition {composition_id} as FAILED",
                extra={"composition_id": str(composition_id), "error": error_msg},
            )
        else:
            logger.warning(
                f"Could not extract composition_id from failed job {job.id}",
                extra={"job_id": job.id},
            )

    except Exception as e:
        logger.exception(
            f"Failed to process job failure callback for {job.id}",
            extra={"job_id": job.id, "error": str(e)},
        )
