"""
Tests for Clip Assembly Service - PR 303
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

from ..models.clip_assembly import (
    DatabaseClipMetadata,
    GenerationProgress,
    ClipAssemblyRequest,
    ClipAssemblyResponse,
    ClipRetrievalRequest,
    ClipRetrievalResponse,
    ClipStorageStatus
)
from ..models.replicate_client import GenerationStatus, VideoResolution, VideoFormat
from ..services.clip_assembly_service import ClipAssemblyService


class TestClipAssemblyService:
    """Test cases for the ClipAssemblyService"""

    @pytest.fixture
    def mock_redis(self):
        """Mock Redis client"""
        return Mock()

    @pytest.fixture
    def mock_db_connection(self):
        """Mock database connection"""
        return Mock()

    @pytest.fixture
    def service(self, mock_redis, mock_db_connection):
        """Create service with mocked dependencies"""
        with patch('ai.services.clip_assembly_service.redis.from_url', return_value=mock_redis):
            with patch('ai.services.clip_assembly_service.psycopg2.connect', return_value=mock_db_connection):
                service = ClipAssemblyService()
                # Replace the lazy-loaded clients with mocks
                service._redis_client = mock_redis
                service._db_connection = mock_db_connection
                service.db_connection = mock_db_connection  # Override property
                return service

    @pytest.fixture
    def sample_clip(self):
        """Create a sample database clip metadata"""
        return DatabaseClipMetadata(
            clip_id="clip_123",
            generation_id="gen_456",
            scene_id="scene_1",
            sequence_order=0,
            start_time_seconds=0.0,
            end_time_seconds=10.0,
            storage_status=ClipStorageStatus.COMPLETED,
            video_url="https://example.com/video.mp4",
            duration_seconds=10.0,
            resolution=VideoResolution.RES_720P,
            format=VideoFormat.MP4,
            model_used="google/veo-3.1-fast",
            prompt_used="A beautiful sunset over mountains",
            generation_time_seconds=5.0,
            created_at=datetime.utcnow(),
            generation_completed_at=datetime.utcnow()
        )

    @pytest.fixture
    def sample_progress(self):
        """Create sample generation progress"""
        return GenerationProgress(
            generation_id="gen_456",
            status=GenerationStatus.PROCESSING,
            progress_percentage=60.0,
            current_step="generating_clips",
            total_clips=3,
            completed_clips=2,
            failed_clips=0,
            current_clip_index=1,
            started_at=datetime.utcnow(),
            last_updated=datetime.utcnow()
        )

    def test_service_initialization(self):
        """Test that service initializes correctly"""
        with patch('ai.services.clip_assembly_service.redis.from_url'):
            with patch('ai.services.clip_assembly_service.psycopg2.connect') as mock_connect:
                service = ClipAssemblyService()
                assert service.redis_url == "redis://localhost:6379"
                assert service.db_config is not None
                assert 'host' in service.db_config

    @pytest.mark.asyncio
    async def test_assemble_clips_success(self, service, mock_redis, mock_db_connection, sample_clip, sample_progress):
        """Test successful clip assembly"""
        # Setup mocks
        mock_cursor = Mock()
        mock_db_connection.cursor.return_value.__enter__.return_value = mock_cursor
        mock_db_connection.commit = Mock()

        mock_redis.set = Mock(return_value=True)
        mock_redis.expire = Mock(return_value=True)
        mock_redis.zadd = Mock(return_value=True)
        mock_redis.hset = Mock(return_value=True)

        # Create request
        request = ClipAssemblyRequest(
            generation_id="gen_456",
            clips=[sample_clip],
            progress=sample_progress,
            total_expected_clips=3
        )

        # Execute
        response = await service.assemble_clips(request)

        # Verify
        assert isinstance(response, ClipAssemblyResponse)
        assert response.generation_id == "gen_456"
        assert response.clips_stored == 1
        assert response.success is True
        assert response.stored_clip_ids == ["clip_123"]

        # Verify database call
        mock_cursor.execute.assert_called()
        mock_db_connection.commit.assert_called()

        # Verify Redis calls
        assert mock_redis.set.called
        assert mock_redis.expire.called
        assert mock_redis.zadd.called
        assert mock_redis.hset.called

    @pytest.mark.asyncio
    async def test_assemble_clips_database_error(self, service, mock_redis, mock_db_connection, sample_clip):
        """Test clip assembly with database error"""
        # Setup mock to raise exception
        mock_cursor = Mock()
        mock_cursor.execute.side_effect = Exception("Database error")
        mock_db_connection.cursor.return_value.__enter__.return_value = mock_cursor

        request = ClipAssemblyRequest(
            generation_id="gen_456",
            clips=[sample_clip],
            progress=GenerationProgress(generation_id="gen_456"),
            total_expected_clips=1
        )

        response = await service.assemble_clips(request)

        assert response.success is False
        assert len(response.errors) > 0
        assert "Database error" in str(response.errors)

    def test_retrieve_clips_success(self, service, mock_redis, mock_db_connection, sample_clip):
        """Test successful clip retrieval"""
        # Setup database mock
        mock_cursor = Mock()
        mock_db_connection.cursor.return_value.__enter__.return_value = mock_cursor

        # Mock the row data (simulating RealDictCursor)
        mock_cursor.fetchall.return_value = [{
            'clip_id': sample_clip.clip_id,
            'generation_id': sample_clip.generation_id,
            'scene_id': sample_clip.scene_id,
            'sequence_order': sample_clip.sequence_order,
            'start_time_seconds': sample_clip.start_time_seconds,
            'end_time_seconds': sample_clip.end_time_seconds,
            'storage_status': sample_clip.storage_status.value,
            'video_url': sample_clip.video_url,
            'duration_seconds': sample_clip.duration_seconds,
            'resolution': sample_clip.resolution.value,
            'format': sample_clip.format.value,
            'model_used': sample_clip.model_used,
            'prompt_used': sample_clip.prompt_used,
            'generation_time_seconds': sample_clip.generation_time_seconds,
            'created_at': sample_clip.created_at
        }]

        # Setup Redis mock for progress
        progress_data = {
            'generation_id': 'gen_456',
            'status': 'processing',
            'progress_percentage': 60.0,
            'current_step': 'generating_clips',
            'total_clips': 3,
            'completed_clips': 2,
            'failed_clips': 0,
            'current_clip_index': 1,
            'started_at': datetime.utcnow().isoformat(),
            'last_updated': datetime.utcnow().isoformat()
        }
        mock_redis.get.return_value = json.dumps(progress_data)

        # Execute
        request = ClipRetrievalRequest(generation_id="gen_456")
        response = service.retrieve_clips(request)

        # Verify
        assert isinstance(response, ClipRetrievalResponse)
        assert response.generation_id == "gen_456"
        assert len(response.clips) == 1
        assert response.total_clips == 1
        assert response.successful_clips == 1
        assert response.failed_clips == 0
        assert response.progress is not None

    def test_retrieve_clips_no_progress(self, service, mock_redis, mock_db_connection):
        """Test clip retrieval when no progress data exists in Redis"""
        # Setup database mock
        mock_cursor = Mock()
        mock_db_connection.cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.fetchall.return_value = []

        # Setup Redis to return None
        mock_redis.get.return_value = None

        request = ClipRetrievalRequest(generation_id="gen_456")
        response = service.retrieve_clips(request)

        assert response.progress is None
        assert len(response.clips) == 0

    def test_update_progress(self, service, mock_redis, sample_progress):
        """Test progress update in Redis"""
        service._update_progress(sample_progress)

        # Verify Redis calls
        assert mock_redis.set.called
        assert mock_redis.expire.called

        # Check that data was JSON serialized
        call_args = mock_redis.set.call_args
        progress_data = json.loads(call_args[0][1])  # Second argument is the JSON data
        assert progress_data['generation_id'] == 'gen_456'
        assert progress_data['status'] == 'processing'
        assert progress_data['progress_percentage'] == 60.0

    def test_get_progress(self, service, mock_redis, sample_progress):
        """Test progress retrieval from Redis"""
        progress_data = {
            'generation_id': sample_progress.generation_id,
            'status': sample_progress.status.value,
            'progress_percentage': sample_progress.progress_percentage,
            'current_step': sample_progress.current_step,
            'total_clips': sample_progress.total_clips,
            'completed_clips': sample_progress.completed_clips,
            'failed_clips': sample_progress.failed_clips,
            'current_clip_index': sample_progress.current_clip_index,
            'started_at': sample_progress.started_at.isoformat() if sample_progress.started_at else None,
            'last_updated': sample_progress.last_updated.isoformat()
        }
        mock_redis.get.return_value = json.dumps(progress_data)

        result = service._get_progress("gen_456")

        assert result is not None
        assert result.generation_id == 'gen_456'
        assert result.status == GenerationStatus.PROCESSING
        assert result.progress_percentage == 60.0

    def test_get_progress_invalid_json(self, service, mock_redis):
        """Test progress retrieval with invalid JSON"""
        mock_redis.get.return_value = "invalid json"

        result = service._get_progress("gen_456")

        assert result is None

    def test_update_clip_ordering(self, service, mock_redis, sample_clip):
        """Test clip ordering update in Redis"""
        clips = [sample_clip]

        service._update_clip_ordering("gen_456", clips)

        # Verify Redis calls for sorted set and hash
        assert mock_redis.zadd.called
        assert mock_redis.hset.called
        assert mock_redis.expire.called

    def test_get_clip_ordering(self, service, mock_redis):
        """Test retrieving clip ordering"""
        mock_redis.zrange.return_value = ['clip_1', 'clip_2', 'clip_3']

        ordering = service.get_clip_ordering("gen_456")

        assert ordering == ['clip_1', 'clip_2', 'clip_3']
        mock_redis.zrange.assert_called_with('generation:gen_456:clips', 0, -1)

    def test_update_clip_status(self, service, mock_db_connection):
        """Test updating clip status"""
        mock_cursor = Mock()
        mock_db_connection.cursor.return_value.__enter__.return_value = mock_cursor

        service.update_clip_status("clip_123", ClipStorageStatus.FAILED, "Network error")

        # Verify database call
        mock_cursor.execute.assert_called()
        assert "FAILED" in str(mock_cursor.execute.call_args)
        assert "Network error" in str(mock_cursor.execute.call_args)

        mock_db_connection.commit.assert_called()

    def test_cleanup_generation(self, service, mock_redis, mock_db_connection):
        """Test generation cleanup"""
        # Setup mock data
        mock_cursor = Mock()
        mock_db_connection.cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.fetchall.return_value = [('clip_1',), ('clip_2',)]

        service.cleanup_generation("gen_456")

        # Verify Redis cleanup
        expected_deletions = [
            'generation:gen_456:progress',
            'generation:gen_456:clips'
        ]
        for key in expected_deletions:
            mock_redis.delete.assert_any_call(key)

        # Verify individual clip cleanup
        mock_redis.delete.assert_any_call('clip:clip_1')
        mock_redis.delete.assert_any_call('clip:clip_2')


class TestClipAssemblyIntegration:
    """Integration tests for the complete clip assembly workflow"""

    @pytest.mark.asyncio
    async def test_full_clip_lifecycle(self, service, mock_redis, mock_db_connection, sample_clip, sample_progress):
        """Test complete clip lifecycle: store -> retrieve -> update -> cleanup"""
        # Setup mocks
        mock_cursor = Mock()
        mock_db_connection.cursor.return_value.__enter__.return_value = mock_cursor
        mock_db_connection.commit = Mock()

        # Step 1: Store clips
        request = ClipAssemblyRequest(
            generation_id="gen_integration",
            clips=[sample_clip],
            progress=sample_progress,
            total_expected_clips=1
        )

        store_response = await service.assemble_clips(request)
        assert store_response.success is True
        assert store_response.clips_stored == 1

        # Step 2: Retrieve clips
        retrieval_request = ClipRetrievalRequest(generation_id="gen_integration")
        retrieve_response = service.retrieve_clips(retrieval_request)

        assert len(retrieve_response.clips) == 1
        assert retrieve_response.clips[0].clip_id == sample_clip.clip_id
        assert retrieve_response.progress is not None

        # Step 3: Update clip status
        service.update_clip_status(sample_clip.clip_id, ClipStorageStatus.FAILED, "Test failure")

        # Step 4: Verify status update (mock verification)
        update_calls = [call for call in mock_cursor.execute.call_args_list if 'FAILED' in str(call)]
        assert len(update_calls) > 0

        # Step 5: Cleanup generation
        service.cleanup_generation("gen_integration")

        # Verify cleanup calls
        cleanup_calls = mock_redis.delete.call_args_list
        expected_keys = ['generation:gen_integration:progress', 'generation:gen_integration:clips']
        for key in expected_keys:
            assert any(key in str(call) for call in cleanup_calls)

    @pytest.mark.asyncio
    async def test_multiple_clips_assembly(self, service, mock_redis, mock_db_connection):
        """Test assembling multiple clips with proper ordering"""
        # Setup mocks
        mock_cursor = Mock()
        mock_db_connection.cursor.return_value.__enter__.return_value = mock_cursor
        mock_db_connection.commit = Mock()

        # Create multiple clips
        clips = []
        for i in range(3):
            clip = DatabaseClipMetadata(
                clip_id=f"clip_{i}",
                generation_id="gen_multi",
                scene_id=f"scene_{i}",
                sequence_order=i,
                start_time_seconds=i * 10.0,
                end_time_seconds=(i + 1) * 10.0,
                storage_status=ClipStorageStatus.COMPLETED,
                video_url=f"https://example.com/clip_{i}.mp4",
                duration_seconds=10.0,
                resolution=VideoResolution.RES_720P,
                format=VideoFormat.MP4,
                model_used="google/veo-3.1-fast",
                prompt_used=f"Prompt for scene {i}",
                generation_time_seconds=5.0,
                created_at=datetime.utcnow(),
                generation_completed_at=datetime.utcnow()
            )
            clips.append(clip)

        # Create progress
        progress = GenerationProgress(
            generation_id="gen_multi",
            status=GenerationStatus.PROCESSING,
            progress_percentage=100.0,
            current_step="completed",
            total_clips=3,
            completed_clips=3,
            failed_clips=0,
            current_clip_index=2,
            started_at=datetime.utcnow(),
            last_updated=datetime.utcnow()
        )

        # Store clips
        request = ClipAssemblyRequest(
            generation_id="gen_multi",
            clips=clips,
            progress=progress,
            total_expected_clips=3
        )

        response = await service.assemble_clips(request)

        assert response.success is True
        assert response.clips_stored == 3
        assert len(response.stored_clip_ids) == 3

        # Verify ordering in Redis (zadd should be called for each clip with correct scores)
        zadd_calls = mock_redis.zadd.call_args_list
        assert len(zadd_calls) == 3

        # Check that scores match sequence_order
        for i, call in enumerate(zadd_calls):
            args, kwargs = call
            score = kwargs.get('mapping', {}).get(f'clip_{i}', args[2] if len(args) > 2 else None)
            # The score should be the sequence_order (i)
            assert score == i

    def test_clip_ordering_persistence(self, service, mock_redis, mock_db_connection):
        """Test that clip ordering is maintained across storage and retrieval"""
        # Setup database mock to return clips in wrong order
        mock_cursor = Mock()
        mock_db_connection.cursor.return_value.__enter__.return_value = mock_cursor

        # Return clips in reverse order (simulating DB storage order)
        mock_cursor.fetchall.return_value = [
            {
                'clip_id': 'clip_2', 'generation_id': 'gen_order', 'scene_id': 'scene_2',
                'sequence_order': 2, 'start_time_seconds': 20.0, 'end_time_seconds': 30.0,
                'storage_status': 'completed', 'video_url': 'url_2', 'duration_seconds': 10.0,
                'resolution': '720p', 'format': 'mp4', 'model_used': 'test', 'prompt_used': 'prompt_2',
                'generation_time_seconds': 5.0, 'created_at': datetime.utcnow()
            },
            {
                'clip_id': 'clip_0', 'generation_id': 'gen_order', 'scene_id': 'scene_0',
                'sequence_order': 0, 'start_time_seconds': 0.0, 'end_time_seconds': 10.0,
                'storage_status': 'completed', 'video_url': 'url_0', 'duration_seconds': 10.0,
                'resolution': '720p', 'format': 'mp4', 'model_used': 'test', 'prompt_used': 'prompt_0',
                'generation_time_seconds': 5.0, 'created_at': datetime.utcnow()
            },
            {
                'clip_id': 'clip_1', 'generation_id': 'gen_order', 'scene_id': 'scene_1',
                'sequence_order': 1, 'start_time_seconds': 10.0, 'end_time_seconds': 20.0,
                'storage_status': 'completed', 'video_url': 'url_1', 'duration_seconds': 10.0,
                'resolution': '720p', 'format': 'mp4', 'model_used': 'test', 'prompt_used': 'prompt_1',
                'generation_time_seconds': 5.0, 'created_at': datetime.utcnow()
            }
        ]

        # Setup Redis to return correct ordering
        mock_redis.zrange.return_value = ['clip_0', 'clip_1', 'clip_2']

        # Retrieve clips
        request = ClipRetrievalRequest(generation_id="gen_order", order_by_sequence=True)
        response = service.retrieve_clips(request)

        # Verify clips are returned in sequence order
        assert len(response.clips) == 3
        assert response.clips[0].clip_id == 'clip_0'
        assert response.clips[1].clip_id == 'clip_1'
        assert response.clips[2].clip_id == 'clip_2'

        # Verify sequence orders
        assert response.clips[0].sequence_order == 0
        assert response.clips[1].sequence_order == 1
        assert response.clips[2].sequence_order == 2

    @pytest.mark.asyncio
    async def test_error_handling_and_recovery(self, service, mock_redis, mock_db_connection, sample_clip):
        """Test error handling and recovery in clip assembly"""
        # Setup database to fail on first attempt
        mock_cursor = Mock()
        mock_db_connection.cursor.return_value.__enter__.return_value = mock_cursor

        # First call fails
        mock_cursor.execute.side_effect = [Exception("Connection lost"), None]
        mock_db_connection.commit.side_effect = [None, None]

        request = ClipAssemblyRequest(
            generation_id="gen_error_test",
            clips=[sample_clip],
            progress=GenerationProgress(generation_id="gen_error_test"),
            total_expected_clips=1
        )

        # This should fail due to database error
        response = await service.assemble_clips(request)
        assert response.success is False

        # Reset for successful retry
        mock_cursor.execute.side_effect = None

        # Retry should succeed
        response = await service.assemble_clips(request)
        assert response.success is True

    def test_progress_tracking_accuracy(self, service, mock_redis):
        """Test that progress tracking accurately reflects clip status"""
        # Create progress with specific values
        progress = GenerationProgress(
            generation_id="gen_progress_test",
            status=GenerationStatus.PROCESSING,
            progress_percentage=0.0,  # Will be updated
            current_step="initializing",
            total_clips=5,
            completed_clips=2,
            failed_clips=1,
            current_clip_index=3,
            started_at=datetime.utcnow(),
            last_updated=datetime.utcnow()
        )

        # Progress should update automatically
        progress.update_progress()
        expected_percentage = (2 / 5) * 100  # 40%
        assert progress.progress_percentage == expected_percentage

        # Store and retrieve progress
        service._update_progress(progress)
        retrieved = service._get_progress("gen_progress_test")

        assert retrieved is not None
        assert retrieved.progress_percentage == expected_percentage
        assert retrieved.total_clips == 5
        assert retrieved.completed_clips == 2
        assert retrieved.failed_clips == 1

    def test_clip_status_transitions(self, service, mock_db_connection):
        """Test proper clip status transitions"""
        mock_cursor = Mock()
        mock_db_connection.cursor.return_value.__enter__.return_value = mock_cursor

        clip_id = "test_clip_status"

        # Start as pending
        service.update_clip_status(clip_id, ClipStorageStatus.PENDING)
        assert "PENDING" in str(mock_cursor.execute.call_args)

        # Move to generating
        service.update_clip_status(clip_id, ClipStorageStatus.GENERATING)
        assert "GENERATING" in str(mock_cursor.execute.call_args)

        # Complete successfully
        service.update_clip_status(clip_id, ClipStorageStatus.COMPLETED)
        assert "COMPLETED" in str(mock_cursor.execute.call_args)

        # Verify all status updates were committed
        assert mock_db_connection.commit.call_count == 3

    def test_database_table_creation(self, service, mock_db_connection):
        """Test that tables are created on first database access"""
        mock_cursor = Mock()
        mock_db_connection.cursor.return_value.__enter__.return_value = mock_cursor

        # Trigger table creation by accessing db_connection property
        _ = service.db_connection

        # Verify table creation SQL was executed
        mock_cursor.execute.assert_called()
        sql = str(mock_cursor.execute.call_args[0][0])
        assert "CREATE TABLE IF NOT EXISTS clips" in sql
        assert "CREATE TABLE IF NOT EXISTS generations" in sql

    def test_clip_validation(self, sample_clip):
        """Test clip validation methods"""
        # Test successful clip
        assert sample_clip.is_successful() is True

        # Test failed clip
        failed_clip = sample_clip.copy()
        failed_clip.error_message = "Generation failed"
        assert failed_clip.is_successful() is False

        # Test summary generation
        summary = sample_clip.get_summary()
        assert "clip_123" in summary
        assert "10.0s" in summary
        assert "720p" in summary

    def test_progress_calculations(self, sample_progress):
        """Test progress calculation methods"""
        # Test initial progress
        assert sample_progress.progress_percentage == 60.0

        # Test progress update
        sample_progress.completed_clips = 3
        sample_progress.update_progress()
        assert sample_progress.progress_percentage == 100.0

        # Test summary
        summary = sample_progress.get_summary()
        assert "gen_456" in summary
        assert "60.0%" in summary
