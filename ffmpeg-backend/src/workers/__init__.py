"""Worker package for background job processing."""

from .cleanup_handler import CleanupJobHandler, CleanupReport, run_cleanup_job
from .ffmpeg_pipeline import FFmpegPipeline, FFmpegProgress, FFmpegProgressParser
from .job_handlers import (
    CompositionJobHandler,
    CompositionJobParams,
    JobContext,
    JobStatus,
    process_composition_job,
)
from .progress_tracker import ProgressSubscriber, ProgressTracker, ProgressUpdate
from .redis_pool import get_redis_connection, redis_connection_manager
from .retry_logic import (
    FailureType,
    JobTimeoutError,
    MaxRetriesExceededError,
    classify_failure,
    exponential_backoff,
    retry_with_backoff,
    should_retry,
    with_timeout,
)
from .s3_manager import S3Manager, s3_manager
from .worker import (
    QUEUE_DEFAULT,
    QUEUE_HIGH,
    QUEUE_LOW,
    QUEUE_PRIORITY,
    VideoWorker,
    create_queues,
    create_worker,
    enqueue_job,
    start_worker,
)

__all__ = [
    "get_redis_connection",
    "redis_connection_manager",
    "VideoWorker",
    "start_worker",
    "create_worker",
    "create_queues",
    "enqueue_job",
    "QUEUE_HIGH",
    "QUEUE_DEFAULT",
    "QUEUE_LOW",
    "QUEUE_PRIORITY",
    "CompositionJobHandler",
    "CompositionJobParams",
    "JobContext",
    "JobStatus",
    "process_composition_job",
    "FFmpegPipeline",
    "FFmpegProgress",
    "FFmpegProgressParser",
    "S3Manager",
    "s3_manager",
    "ProgressTracker",
    "ProgressSubscriber",
    "ProgressUpdate",
    "retry_with_backoff",
    "with_timeout",
    "exponential_backoff",
    "classify_failure",
    "should_retry",
    "FailureType",
    "JobTimeoutError",
    "MaxRetriesExceededError",
    "CleanupJobHandler",
    "CleanupReport",
    "run_cleanup_job",
]
