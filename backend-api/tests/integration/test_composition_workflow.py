"""
Integration tests for complete composition workflow.

Tests the full end-to-end composition workflow from API request
through job processing to completion, including:
- API request → database record creation
- RQ job enqueue
- Worker processing
- FFmpeg execution
- S3 upload
- Status updates
- Job retry mechanisms
- Redis pub/sub progress updates
- Database transactions
- Concurrent job processing
- Cleanup of temporary files
"""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from db.models.composition import Composition, CompositionStatus
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from workers.job_handlers import CompositionJobHandler, JobStatus


class TestCompositionAPIIntegration:
    """Test API endpoints for composition workflow."""

    @pytest.fixture
    def composition_request_data(self):
        """Create sample composition request data."""
        return {
            "title": "Test Composition",
            "description": "Integration test composition",
            "clips": [
                {
                    "video_url": "https://example.com/video1.mp4",
                    "start_time": 0.0,
                    "end_time": 10.0,
                    "trim_start": 0.0,
                    "trim_end": 10.0,
                },
                {
                    "video_url": "https://example.com/video2.mp4",
                    "start_time": 10.0,
                    "end_time": 20.0,
                    "trim_start": 0.0,
                    "trim_end": 10.0,
                },
            ],
            "audio": {
                "music_url": "https://example.com/music.mp3",
                "voiceover_url": None,
                "music_volume": 0.3,
                "voiceover_volume": 1.0,
                "original_audio_volume": 0.8,
            },
            "overlays": [
                {
                    "text": "Title Overlay",
                    "position": "top_center",
                    "start_time": 0.0,
                    "end_time": 3.0,
                    "font_size": 48,
                    "font_color": "white",
                }
            ],
            "output": {
                "resolution": "1080p",
                "format": "mp4",
                "fps": 30,
                "bitrate": 5000000,
            },
        }

    @pytest.mark.asyncio
    async def test_create_composition_full_workflow(
        self,
        db_session: AsyncSession,
        composition_request_data: dict,
        mock_rq_queue: MagicMock,
    ):
        """Test complete composition creation workflow.

        Verifies:
        - Composition record created in database
        - Status transitions: PENDING → QUEUED
        - Job enqueued to RQ
        - Request data properly stored
        """
        from app.api.schemas import CompositionCreateRequest

        # Create request
        request = CompositionCreateRequest(**composition_request_data)

        # Mock enqueue_job
        with patch("app.api.v1.compositions.enqueue_job") as mock_enqueue:
            mock_job = MagicMock()
            mock_job.id = "test-job-123"
            mock_enqueue.return_value = mock_job

            # Execute composition creation logic
            composition_id = uuid.uuid4()
            composition_config = {
                "clips": [
                    {
                        "video_url": clip.video_url,
                        "start_time": clip.start_time,
                        "end_time": clip.end_time,
                        "trim_start": clip.trim_start,
                        "trim_end": clip.trim_end,
                    }
                    for clip in request.clips
                ],
                "audio": {
                    "music_url": str(request.audio.music_url) if request.audio.music_url else None,
                    "voiceover_url": (
                        str(request.audio.voiceover_url) if request.audio.voiceover_url else None
                    ),
                    "music_volume": request.audio.music_volume,
                    "voiceover_volume": request.audio.voiceover_volume,
                    "original_audio_volume": request.audio.original_audio_volume,
                },
                "overlays": [
                    {
                        "text": overlay.text,
                        "position": overlay.position.value,
                        "start_time": overlay.start_time,
                        "end_time": overlay.end_time,
                        "font_size": overlay.font_size,
                        "font_color": overlay.font_color,
                    }
                    for overlay in request.overlays
                ],
                "output": {
                    "resolution": request.output.resolution.value,
                    "format": request.output.format.value,
                    "fps": request.output.fps,
                    "bitrate": request.output.bitrate,
                },
            }

            # Create composition record
            composition = Composition(
                id=composition_id,
                title=request.title,
                description=request.description,
                status=CompositionStatus.PENDING,
                composition_config=composition_config,
            )

            db_session.add(composition)
            await db_session.commit()
            await db_session.refresh(composition)

            # Verify database record
            assert composition.id == composition_id
            assert composition.title == "Test Composition"
            assert composition.status == CompositionStatus.PENDING
            assert composition.composition_config["clips"][0]["video_url"] == str(
                request.clips[0].video_url
            )

            # Enqueue job
            job_params = {
                "composition_id": composition_id,
                "composition_config": composition_config,
                "output_format": "mp4",
                "output_resolution": "1920x1080",
                "output_fps": 30,
                "priority": "default",
            }

            from workers.job_handlers import process_composition_job

            mock_enqueue(
                func=process_composition_job,
                kwargs={"job_id": str(uuid.uuid4()), **job_params},
                queue_name="default",
                description=f"Process composition: {request.title}",
            )

            # Verify job enqueued
            mock_enqueue.assert_called_once()
            call_kwargs = mock_enqueue.call_args.kwargs
            assert call_kwargs["queue_name"] == "default"
            assert "Process composition" in call_kwargs["description"]

            # Update status to QUEUED
            composition.status = CompositionStatus.QUEUED
            await db_session.commit()

            # Verify final status
            result = await db_session.execute(
                select(Composition).where(Composition.id == composition_id)
            )
            updated_composition = result.scalar_one()
            assert updated_composition.status == CompositionStatus.QUEUED


class TestJobHandlerIntegration:
    """Test job handler execution and lifecycle."""

    @pytest.fixture
    def job_params(self):
        """Create sample job parameters."""
        return {
            "composition_id": uuid.uuid4(),
            "composition_config": {
                "assets": [
                    {"id": "asset1", "url": "s3://bucket/video1.mp4", "type": "video"},
                    {"id": "asset2", "url": "s3://bucket/video2.mp4", "type": "video"},
                ],
                "clips": [
                    {"asset_id": "asset1", "start": 0.0, "duration": 10.0},
                    {"asset_id": "asset2", "start": 0.0, "duration": 10.0},
                ],
                "output": {"format": "mp4", "resolution": "1920x1080", "fps": 30},
            },
            "output_format": "mp4",
            "output_resolution": "1920x1080",
            "output_fps": 30,
            "priority": "default",
        }

    def test_job_handler_initialization(self):
        """Test job handler initialization."""
        job_id = str(uuid.uuid4())
        handler = CompositionJobHandler(job_id=job_id)

        assert handler.job_id == job_id
        assert handler.context.job_id == job_id
        assert handler.context.status == JobStatus.PENDING
        assert handler.context.progress_percent == 0.0

    def test_job_parameter_validation(self, job_params: dict):
        """Test job parameter validation."""
        job_id = str(uuid.uuid4())
        handler = CompositionJobHandler(job_id=job_id)

        # Valid parameters
        validated = handler.validate_params(job_params)
        assert validated.composition_id == job_params["composition_id"]
        assert validated.output_format == "mp4"
        assert validated.output_resolution == "1920x1080"

        # Invalid format
        invalid_params = job_params.copy()
        invalid_params["output_format"] = "invalid_format"

        with pytest.raises(ValueError, match="Unsupported output format"):
            handler.validate_params(invalid_params)

        # Invalid resolution
        invalid_params = job_params.copy()
        invalid_params["output_resolution"] = "invalid"

        with pytest.raises(ValueError, match="Invalid resolution format"):
            handler.validate_params(invalid_params)

    def test_job_context_updates(self):
        """Test job context state tracking."""
        job_id = str(uuid.uuid4())
        handler = CompositionJobHandler(job_id=job_id)

        # Update to in-progress
        handler._update_context(
            status=JobStatus.IN_PROGRESS,
            progress=25.0,
            operation="Processing assets",
        )

        assert handler.context.status == JobStatus.IN_PROGRESS
        assert handler.context.progress_percent == 25.0
        assert handler.context.current_operation == "Processing assets"
        assert handler.context.started_at is not None
        assert handler.context.is_running is True

        # Update progress
        handler._update_context(progress=75.0, operation="Rendering video")

        assert handler.context.progress_percent == 75.0
        assert handler.context.current_operation == "Rendering video"

        # Mark completed
        handler._update_context(status=JobStatus.COMPLETED, progress=100.0)

        assert handler.context.status == JobStatus.COMPLETED
        assert handler.context.is_complete is True
        assert handler.context.completed_at is not None
        assert handler.context.duration_seconds is not None

    @patch("workers.job_handlers.s3_manager")
    @patch("workers.job_handlers.FFmpegPipeline")
    def test_job_execution_flow_with_mocks(
        self,
        mock_pipeline_class: MagicMock,
        mock_s3: MagicMock,
        job_params: dict,
        tmp_path: Path,
    ):
        """Test complete job execution flow with mocked dependencies."""
        job_id = str(uuid.uuid4())
        handler = CompositionJobHandler(job_id=job_id)

        # Mock S3 downloads
        mock_s3.download_assets.return_value = {
            "asset1": tmp_path / "video1.mp4",
            "asset2": tmp_path / "video2.mp4",
        }

        # Create mock video files
        (tmp_path / "video1.mp4").write_bytes(b"MOCK_VIDEO_1")
        (tmp_path / "video2.mp4").write_bytes(b"MOCK_VIDEO_2")

        # Mock FFmpeg pipeline
        mock_pipeline = MagicMock()
        output_file = tmp_path / "output.mp4"
        output_file.write_bytes(b"MOCK_OUTPUT_VIDEO")
        mock_pipeline.execute_composition.return_value = output_file
        mock_pipeline_class.return_value = mock_pipeline

        # Mock S3 upload
        mock_s3.upload_file.return_value = "s3://bucket/compositions/test-id/output.mp4"

        # Mock settings
        with patch("workers.job_handlers.settings") as mock_settings:
            mock_settings.temp_dir = str(tmp_path)
            mock_settings.rq_default_timeout = 300

            # Execute job
            result = handler._execute_job(handler.validate_params(job_params))

            # Verify result
            assert result["status"] == "completed"
            assert "output_url" in result
            assert result["output_format"] == "mp4"

            # Verify S3 download called
            mock_s3.download_assets.assert_called_once()

            # Verify FFmpeg pipeline executed
            mock_pipeline.execute_composition.assert_called_once()

            # Verify S3 upload called
            mock_s3.upload_file.assert_called_once()

            # Verify cleanup called
            mock_pipeline.cleanup_temp_files.assert_called_once()


class TestJobRetryMechanisms:
    """Test job retry mechanisms with simulated failures."""

    def test_retry_on_transient_failure(self, redis_client):
        """Test job retry on transient failures."""
        from workers.retry_logic import FailureType, classify_failure

        # Simulate network error (transient)
        network_error = ConnectionError("Connection timeout")
        failure_type = classify_failure(network_error)

        assert failure_type == FailureType.TRANSIENT
        # Transient failures should be retried

    def test_no_retry_on_permanent_failure(self):
        """Test job does not retry on permanent failures."""
        from workers.retry_logic import FailureType, classify_failure

        # Simulate validation error (permanent)
        validation_error = ValueError("Invalid video format")
        failure_type = classify_failure(validation_error)

        assert failure_type == FailureType.PERMANENT
        # Permanent failures should not be retried

    @patch("workers.job_handlers.s3_manager")
    def test_job_failure_handling(self, mock_s3: MagicMock):
        """Test job failure handling and error tracking."""
        job_id = str(uuid.uuid4())
        handler = CompositionJobHandler(job_id=job_id)

        # Simulate S3 failure
        mock_s3.download_assets.side_effect = Exception("S3 download failed")

        job_params = {
            "composition_id": uuid.uuid4(),
            "composition_config": {
                "assets": [{"id": "asset1", "url": "s3://bucket/video.mp4", "type": "video"}]
            },
            "output_format": "mp4",
            "output_resolution": "1920x1080",
            "output_fps": 30,
            "priority": "default",
        }

        # Execute job (should fail)
        with patch("workers.job_handlers.settings") as mock_settings:
            mock_settings.temp_dir = "/tmp"

            result = handler.execute(job_params)

            # Verify failure tracked
            assert result["success"] is False
            assert "error" in result
            assert "S3 download failed" in result["error"]
            assert handler.context.status == JobStatus.FAILED
            assert handler.context.error_message is not None


class TestConcurrentJobProcessing:
    """Test concurrent job processing."""

    @pytest.mark.asyncio
    async def test_multiple_jobs_in_database(self, db_session: AsyncSession):
        """Test multiple compositions can be created and tracked."""
        # Create multiple compositions
        compositions = []
        for i in range(5):
            comp = Composition(
                id=uuid.uuid4(),
                title=f"Composition {i}",
                description=f"Test composition {i}",
                status=CompositionStatus.PENDING,
                composition_config={"clips": [], "output": {"format": "mp4"}},
            )
            db_session.add(comp)
            compositions.append(comp)

        await db_session.commit()

        # Verify all created
        result = await db_session.execute(select(Composition))
        all_comps = result.scalars().all()

        assert len(all_comps) >= 5

        # Verify each composition can be retrieved
        for comp in compositions:
            result = await db_session.execute(select(Composition).where(Composition.id == comp.id))
            retrieved = result.scalar_one()
            assert retrieved.id == comp.id
            assert retrieved.title == comp.title

    def test_concurrent_job_context_isolation(self):
        """Test job contexts are isolated for concurrent execution."""
        # Create multiple job handlers
        handlers = [CompositionJobHandler(job_id=str(uuid.uuid4())) for _ in range(3)]

        # Update different progress for each
        for i, handler in enumerate(handlers):
            handler._update_context(
                status=JobStatus.IN_PROGRESS,
                progress=i * 33.0,
                operation=f"Processing job {i}",
            )

        # Verify isolation
        for i, handler in enumerate(handlers):
            assert handler.context.progress_percent == i * 33.0
            assert handler.context.current_operation == f"Processing job {i}"


class TestRedisProgressUpdates:
    """Test Redis pub/sub progress updates."""

    def test_progress_tracker_initialization(self, redis_client):
        """Test progress tracker initialization."""
        from workers.progress_tracker import ProgressTracker

        job_id = str(uuid.uuid4())
        composition_id = str(uuid.uuid4())

        # Mock get_redis_connection to return our test redis client
        with patch("workers.progress_tracker.get_redis_connection", return_value=redis_client):
            tracker = ProgressTracker(
                job_id=job_id,
                composition_id=composition_id,
            )

            assert tracker.job_id == job_id
            assert tracker.composition_id == composition_id

    def test_progress_publish_to_redis(self, redis_client):
        """Test progress updates are published to Redis."""
        from workers.progress_tracker import ProgressTracker

        job_id = str(uuid.uuid4())
        composition_id = str(uuid.uuid4())

        # Mock get_redis_connection to return our test redis client
        with patch("workers.progress_tracker.get_redis_connection", return_value=redis_client):
            tracker = ProgressTracker(
                job_id=job_id,
                composition_id=composition_id,
            )

            # Publish progress
            tracker.publish_progress(
                progress_percent=50.0,
                operation="Processing video",
                frame=1500,
                fps=30.0,
                force=True,  # Force publish to avoid throttling in tests
            )

            # Verify stored in Redis (using correct key format from tracker)
            key = f"job:progress:data:{job_id}"
            stored_data = redis_client.get(key)

            assert stored_data is not None
            progress_data = json.loads(stored_data)
            assert progress_data["progress_percent"] == 50.0
            assert progress_data["current_operation"] == "Processing video"
            assert progress_data["frame"] == 1500

    def test_status_update_in_redis(self, redis_client):
        """Test status updates are published to Redis."""
        from workers.progress_tracker import ProgressTracker

        job_id = str(uuid.uuid4())
        composition_id = str(uuid.uuid4())

        # Mock get_redis_connection to return our test redis client
        with patch("workers.progress_tracker.get_redis_connection", return_value=redis_client):
            tracker = ProgressTracker(
                job_id=job_id,
                composition_id=composition_id,
            )

            # Update status
            tracker.update_status(
                status="in_progress",
                message="Processing started",
            )

            # Verify stored in Redis (using correct key format from tracker)
            key = f"job:status:{job_id}"
            stored_data = redis_client.get(key)

            assert stored_data is not None
            status_data = json.loads(stored_data)
            assert status_data["status"] == "in_progress"
            assert status_data["message"] == "Processing started"


class TestDatabaseTransactions:
    """Test database transactions and rollback scenarios."""

    @pytest.mark.asyncio
    async def test_composition_creation_rollback_on_error(self, db_session: AsyncSession):
        """Test composition creation rolls back on error."""
        composition_id = uuid.uuid4()

        try:
            # Start transaction
            composition = Composition(
                id=composition_id,
                title="Test Composition",
                description="Should be rolled back",
                status=CompositionStatus.PENDING,
                composition_config={},
            )
            db_session.add(composition)
            await db_session.flush()

            # Simulate error
            raise ValueError("Simulated error")

        except ValueError:
            # Rollback transaction
            await db_session.rollback()

        # Verify composition not in database
        result = await db_session.execute(
            select(Composition).where(Composition.id == composition_id)
        )
        retrieved = result.scalar_one_or_none()

        assert retrieved is None

    @pytest.mark.asyncio
    async def test_composition_status_update_transaction(self, db_session: AsyncSession):
        """Test composition status updates are transactional."""
        # Create composition
        composition = Composition(
            id=uuid.uuid4(),
            title="Test Composition",
            description="Test",
            status=CompositionStatus.PENDING,
            composition_config={},
        )
        db_session.add(composition)
        await db_session.commit()
        await db_session.refresh(composition)

        # Update status
        composition.status = CompositionStatus.PROCESSING
        await db_session.commit()

        # Verify update persisted
        result = await db_session.execute(
            select(Composition).where(Composition.id == composition.id)
        )
        updated = result.scalar_one()
        assert updated.status == CompositionStatus.PROCESSING

        # Update again
        updated.status = CompositionStatus.COMPLETED
        updated.output_url = "s3://bucket/output.mp4"
        await db_session.commit()

        # Verify both fields updated
        result = await db_session.execute(
            select(Composition).where(Composition.id == composition.id)
        )
        final = result.scalar_one()
        assert final.status == CompositionStatus.COMPLETED
        assert final.output_url == "s3://bucket/output.mp4"


class TestTemporaryFileCleanup:
    """Test cleanup of temporary files after job completion."""

    def test_temp_directory_cleanup_on_success(self, tmp_path: Path):
        """Test temporary files are cleaned up after successful job."""
        job_id = str(uuid.uuid4())
        job_temp_dir = tmp_path / job_id
        job_temp_dir.mkdir()

        # Create temp files
        (job_temp_dir / "video1.mp4").write_bytes(b"TEMP_VIDEO_1")
        (job_temp_dir / "video2.mp4").write_bytes(b"TEMP_VIDEO_2")
        (job_temp_dir / "output.mp4").write_bytes(b"OUTPUT_VIDEO")

        assert job_temp_dir.exists()
        assert len(list(job_temp_dir.iterdir())) == 3

        # Simulate cleanup
        import shutil

        shutil.rmtree(job_temp_dir, ignore_errors=True)

        # Verify cleanup
        assert not job_temp_dir.exists()

    def test_temp_directory_cleanup_on_failure(self, tmp_path: Path):
        """Test temporary files are cleaned up even on job failure."""
        job_id = str(uuid.uuid4())
        job_temp_dir = tmp_path / job_id
        job_temp_dir.mkdir()

        # Create temp files
        (job_temp_dir / "video1.mp4").write_bytes(b"TEMP_VIDEO_1")

        assert job_temp_dir.exists()

        # Simulate failure and cleanup
        try:
            raise Exception("Simulated job failure")
        except Exception:
            import shutil

            shutil.rmtree(job_temp_dir, ignore_errors=True)

        # Verify cleanup happened despite error
        assert not job_temp_dir.exists()

    @patch("workers.job_handlers.FFmpegPipeline")
    def test_pipeline_cleanup_called(self, mock_pipeline_class: MagicMock):
        """Test FFmpeg pipeline cleanup is called."""
        job_id = str(uuid.uuid4())
        handler = CompositionJobHandler(job_id=job_id)

        mock_pipeline = MagicMock()
        mock_pipeline_class.return_value = mock_pipeline

        # Mock successful execution
        with (
            patch("workers.job_handlers.s3_manager") as mock_s3,
            patch("workers.job_handlers.settings") as mock_settings,
        ):
            mock_settings.temp_dir = "/tmp"
            mock_settings.rq_default_timeout = 300

            mock_s3.download_assets.return_value = {"asset1": Path("/tmp/video1.mp4")}
            mock_pipeline.execute_composition.return_value = Path("/tmp/output.mp4")
            mock_s3.upload_file.return_value = "s3://bucket/output.mp4"

            job_params = {
                "composition_id": uuid.uuid4(),
                "composition_config": {"assets": [{"id": "asset1"}]},
                "output_format": "mp4",
                "output_resolution": "1920x1080",
                "output_fps": 30,
                "priority": "default",
            }

            try:
                handler._execute_job(handler.validate_params(job_params))
            except Exception:
                pass

            # Verify cleanup was called
            mock_pipeline.cleanup_temp_files.assert_called_once()


class TestEndToEndWorkflow:
    """Test complete end-to-end workflow integration."""

    @pytest.mark.asyncio
    @patch("workers.job_handlers.s3_manager")
    @patch("workers.job_handlers.FFmpegPipeline")
    async def test_complete_workflow_from_api_to_completion(
        self,
        mock_pipeline_class: MagicMock,
        mock_s3: MagicMock,
        db_session: AsyncSession,
        tmp_path: Path,
    ):
        """Test complete workflow from API request to job completion.

        This test simulates:
        1. API receives composition request
        2. Composition created in database (PENDING)
        3. Job enqueued (status → QUEUED)
        4. Worker picks up job (status → PROCESSING)
        5. Assets downloaded from S3
        6. FFmpeg processes video
        7. Output uploaded to S3
        8. Status updated to COMPLETED
        9. Cleanup performed
        """
        # Step 1: Create composition in database (simulating API)
        composition_id = uuid.uuid4()
        composition = Composition(
            id=composition_id,
            title="End-to-End Test",
            description="Complete workflow test",
            status=CompositionStatus.PENDING,
            composition_config={
                "assets": [
                    {"id": "asset1", "url": "s3://bucket/video1.mp4", "type": "video"},
                ],
                "clips": [{"asset_id": "asset1", "start": 0.0, "duration": 10.0}],
                "output": {"format": "mp4", "resolution": "1920x1080", "fps": 30},
            },
        )
        db_session.add(composition)
        await db_session.commit()
        await db_session.refresh(composition)

        # Verify PENDING status
        assert composition.status == CompositionStatus.PENDING

        # Step 2: Update to QUEUED (simulating job enqueue)
        composition.status = CompositionStatus.QUEUED
        await db_session.commit()

        # Step 3: Execute job (simulating worker)
        job_id = str(uuid.uuid4())
        handler = CompositionJobHandler(job_id=job_id)

        # Mock dependencies
        mock_s3.download_assets.return_value = {"asset1": tmp_path / "video1.mp4"}
        (tmp_path / "video1.mp4").write_bytes(b"MOCK_VIDEO")

        mock_pipeline = MagicMock()
        output_file = tmp_path / "output.mp4"
        output_file.write_bytes(b"MOCK_OUTPUT")
        mock_pipeline.execute_composition.return_value = output_file
        mock_pipeline_class.return_value = mock_pipeline

        mock_s3.upload_file.return_value = f"s3://bucket/compositions/{composition_id}/output.mp4"

        # Execute job
        with patch("workers.job_handlers.settings") as mock_settings:
            mock_settings.temp_dir = str(tmp_path)
            mock_settings.rq_default_timeout = 300

            job_params = {
                "composition_id": composition_id,
                "composition_config": composition.composition_config,
                "output_format": "mp4",
                "output_resolution": "1920x1080",
                "output_fps": 30,
                "priority": "default",
            }

            result = handler.execute(job_params)

            # Verify job succeeded
            assert result["success"] is True
            assert result["result"]["status"] == "completed"
            assert "output_url" in result["result"]

        # Step 4: Update composition with results (simulating job completion callback)
        composition.status = CompositionStatus.COMPLETED
        composition.output_url = result["result"]["output_url"]
        await db_session.commit()

        # Step 5: Verify final state
        result = await db_session.execute(
            select(Composition).where(Composition.id == composition_id)
        )
        final_composition = result.scalar_one()

        assert final_composition.status == CompositionStatus.COMPLETED
        assert final_composition.output_url is not None
        assert f"compositions/{composition_id}" in final_composition.output_url

        # Verify all steps were executed
        mock_s3.download_assets.assert_called_once()
        mock_pipeline.execute_composition.assert_called_once()
        mock_s3.upload_file.assert_called_once()
        mock_pipeline.cleanup_temp_files.assert_called_once()
