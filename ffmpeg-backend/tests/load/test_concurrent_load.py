"""
Load tests for concurrent job handling using pytest.

These tests verify the system can handle multiple simultaneous jobs
and measure performance metrics.
"""

from __future__ import annotations

import asyncio
import time
from typing import Any

import pytest
from httpx import AsyncClient


class TestConcurrentSimpleCompositions:
    """Test 5 concurrent simple compositions."""

    @pytest.fixture
    def simple_composition_payload(self) -> dict[str, Any]:
        """Simple composition request payload."""
        return {
            "title": "Load Test Simple Composition",
            "description": "Simple 2-clip composition",
            "clips": [
                {
                    "video_url": "https://test-bucket.s3.amazonaws.com/video1.mp4",
                    "start_time": 0.0,
                    "end_time": 5.0,
                    "trim_start": 0.0,
                    "trim_end": 5.0,
                },
                {
                    "video_url": "https://test-bucket.s3.amazonaws.com/video2.mp4",
                    "start_time": 5.0,
                    "end_time": 10.0,
                    "trim_start": 0.0,
                    "trim_end": 5.0,
                },
            ],
            "audio": {
                "music_url": None,
                "voiceover_url": None,
                "music_volume": 0.5,
                "voiceover_volume": 1.0,
                "original_audio_volume": 1.0,
            },
            "overlays": [],
            "output": {
                "resolution": "720p",
                "format": "mp4",
                "fps": 30,
                "bitrate": 2000000,
            },
        }

    @pytest.mark.asyncio
    @pytest.mark.benchmark
    async def test_5_concurrent_simple_compositions(
        self,
        test_app,
        simple_composition_payload: dict,
        benchmark,
    ):
        """Test creating 5 simple compositions concurrently.

        Performance targets:
        - All 5 compositions created within 5 seconds
        - Average response time < 1000ms
        - No failures
        """
        num_compositions = 5

        async def create_composition(client: AsyncClient, payload: dict) -> dict:
            """Create a single composition."""
            start_time = time.time()

            response = await client.post(
                "/api/v1/compositions/",
                json=payload,
            )

            response_time = time.time() - start_time

            assert response.status_code == 202
            data = response.json()

            return {
                "composition_id": data["id"],
                "response_time": response_time,
                "status_code": response.status_code,
            }

        # Benchmark the concurrent creation
        def run_concurrent_test():
            async def _run():
                async with AsyncClient(app=test_app, base_url="http://test") as client:
                    # Create 5 compositions concurrently
                    tasks = [
                        create_composition(client, simple_composition_payload)
                        for _ in range(num_compositions)
                    ]

                    results = await asyncio.gather(*tasks)
                    return results

            return asyncio.run(_run())

        # Run benchmark
        results = benchmark(run_concurrent_test)

        # Verify results
        assert len(results) == num_compositions

        # Verify all succeeded
        for result in results:
            assert result["status_code"] == 202
            assert "composition_id" in result

        # Check response times
        response_times = [r["response_time"] for r in results]
        avg_response_time = sum(response_times) / len(response_times)
        max_response_time = max(response_times)

        print("\nConcurrent Simple Compositions - Performance Metrics:")
        print(f"  Total compositions: {num_compositions}")
        print(f"  Average response time: {avg_response_time:.3f}s")
        print(f"  Max response time: {max_response_time:.3f}s")
        print(f"  Min response time: {min(response_times):.3f}s")

        # Performance assertions
        assert avg_response_time < 1.0, "Average response time should be < 1s"
        assert max_response_time < 2.0, "Max response time should be < 2s"

    @pytest.mark.asyncio
    @pytest.mark.benchmark
    async def test_concurrent_composition_throughput(
        self,
        test_app,
        simple_composition_payload: dict,
    ):
        """Test composition creation throughput over 30 seconds."""
        duration_seconds = 30
        target_throughput = 10  # Target: 10 compositions per second

        created_count = 0
        start_time = time.time()
        errors = []

        async with AsyncClient(app=test_app, base_url="http://test") as client:
            while (time.time() - start_time) < duration_seconds:
                try:
                    response = await client.post(
                        "/api/v1/compositions/",
                        json=simple_composition_payload,
                    )

                    if response.status_code == 202:
                        created_count += 1
                    else:
                        errors.append(f"Status {response.status_code}")

                except Exception as e:
                    errors.append(str(e))

                # Small delay to avoid overwhelming the system
                await asyncio.sleep(0.05)

        elapsed_time = time.time() - start_time
        throughput = created_count / elapsed_time

        print("\nThroughput Test Results:")
        print(f"  Duration: {elapsed_time:.1f}s")
        print(f"  Created: {created_count} compositions")
        print(f"  Throughput: {throughput:.2f} compositions/second")
        print(f"  Errors: {len(errors)}")

        # Verify acceptable throughput
        assert (
            throughput >= target_throughput * 0.8
        ), f"Throughput {throughput:.2f}/s is below 80% of target {target_throughput}/s"


class TestConcurrentComplexCompositions:
    """Test 5 concurrent complex compositions."""

    @pytest.fixture
    def complex_composition_payload(self) -> dict[str, Any]:
        """Complex composition with 10 clips, audio, and overlays."""
        clips = []
        for i in range(10):
            clips.append(
                {
                    "video_url": f"https://test-bucket.s3.amazonaws.com/video{i}.mp4",
                    "start_time": i * 3.0,
                    "end_time": (i + 1) * 3.0,
                    "trim_start": 0.0,
                    "trim_end": 3.0,
                }
            )

        return {
            "title": "Load Test Complex Composition",
            "description": "10 clips with audio and overlays",
            "clips": clips,
            "audio": {
                "music_url": "https://test-bucket.s3.amazonaws.com/music.mp3",
                "voiceover_url": "https://test-bucket.s3.amazonaws.com/voice.mp3",
                "music_volume": 0.3,
                "voiceover_volume": 1.0,
                "original_audio_volume": 0.8,
            },
            "overlays": [
                {
                    "text": "Opening Title",
                    "position": "top_center",
                    "start_time": 0.0,
                    "end_time": 3.0,
                    "font_size": 48,
                    "font_color": "white",
                },
                {
                    "text": "Middle",
                    "position": "bottom_center",
                    "start_time": 15.0,
                    "end_time": 18.0,
                    "font_size": 36,
                    "font_color": "yellow",
                },
                {
                    "text": "End Credits",
                    "position": "center",
                    "start_time": 27.0,
                    "end_time": 30.0,
                    "font_size": 40,
                    "font_color": "white",
                },
            ],
            "output": {
                "resolution": "1080p",
                "format": "mp4",
                "fps": 30,
                "bitrate": 5000000,
            },
        }

    @pytest.mark.asyncio
    @pytest.mark.benchmark
    async def test_5_concurrent_complex_compositions(
        self,
        test_app,
        complex_composition_payload: dict,
        benchmark,
    ):
        """Test creating 5 complex compositions concurrently.

        Performance targets:
        - All 5 compositions created within 10 seconds
        - Average response time < 2000ms
        - No failures
        """
        num_compositions = 5

        async def create_composition(client: AsyncClient, payload: dict) -> dict:
            """Create a single complex composition."""
            start_time = time.time()

            response = await client.post(
                "/api/v1/compositions/",
                json=payload,
            )

            response_time = time.time() - start_time

            assert response.status_code == 202
            data = response.json()

            return {
                "composition_id": data["id"],
                "response_time": response_time,
                "status_code": response.status_code,
            }

        # Benchmark the concurrent creation
        def run_concurrent_test():
            async def _run():
                async with AsyncClient(app=test_app, base_url="http://test") as client:
                    tasks = [
                        create_composition(client, complex_composition_payload)
                        for _ in range(num_compositions)
                    ]

                    results = await asyncio.gather(*tasks)
                    return results

            return asyncio.run(_run())

        # Run benchmark
        results = benchmark(run_concurrent_test)

        # Verify results
        assert len(results) == num_compositions

        response_times = [r["response_time"] for r in results]
        avg_response_time = sum(response_times) / len(response_times)

        print("\nConcurrent Complex Compositions - Performance Metrics:")
        print(f"  Total compositions: {num_compositions}")
        print(f"  Average response time: {avg_response_time:.3f}s")
        print(f"  Max response time: {max(response_times):.3f}s")

        # Performance assertions (complex compositions may take longer)
        assert avg_response_time < 2.0, "Average response time should be < 2s"


class TestMixedWorkload:
    """Test mixed workload with different job types."""

    @pytest.mark.asyncio
    async def test_mixed_simple_and_complex_compositions(self, test_app):
        """Test mixed workload: 3 simple + 2 complex compositions."""
        simple_payload = {
            "title": "Mixed Test - Simple",
            "description": "Simple composition",
            "clips": [
                {
                    "video_url": "https://test-bucket.s3.amazonaws.com/video1.mp4",
                    "start_time": 0.0,
                    "end_time": 5.0,
                    "trim_start": 0.0,
                    "trim_end": 5.0,
                }
            ],
            "audio": {
                "music_url": None,
                "voiceover_url": None,
                "music_volume": 0.5,
                "voiceover_volume": 1.0,
                "original_audio_volume": 1.0,
            },
            "overlays": [],
            "output": {
                "resolution": "720p",
                "format": "mp4",
                "fps": 30,
                "bitrate": 2000000,
            },
        }

        complex_payload = {
            "title": "Mixed Test - Complex",
            "description": "Complex composition",
            "clips": [
                {
                    "video_url": f"https://test-bucket.s3.amazonaws.com/video{i}.mp4",
                    "start_time": i * 3.0,
                    "end_time": (i + 1) * 3.0,
                    "trim_start": 0.0,
                    "trim_end": 3.0,
                }
                for i in range(5)
            ],
            "audio": {
                "music_url": "https://test-bucket.s3.amazonaws.com/music.mp3",
                "voiceover_url": None,
                "music_volume": 0.3,
                "voiceover_volume": 1.0,
                "original_audio_volume": 0.8,
            },
            "overlays": [
                {
                    "text": "Overlay",
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

        async with AsyncClient(app=test_app, base_url="http://test") as client:
            # Create mixed workload
            tasks = []

            # 3 simple compositions
            for _ in range(3):
                tasks.append(client.post("/api/v1/compositions/", json=simple_payload))

            # 2 complex compositions
            for _ in range(2):
                tasks.append(client.post("/api/v1/compositions/", json=complex_payload))

            # Execute all concurrently
            start_time = time.time()
            responses = await asyncio.gather(*tasks)
            elapsed_time = time.time() - start_time

            # Verify all succeeded
            for response in responses:
                assert response.status_code == 202

            print("\nMixed Workload Test:")
            print("  Simple compositions: 3")
            print("  Complex compositions: 2")
            print(f"  Total time: {elapsed_time:.3f}s")
            print(f"  Average time per request: {elapsed_time / 5:.3f}s")

            # Verify acceptable performance
            assert elapsed_time < 10.0, "Mixed workload should complete within 10s"


class TestSystemMetrics:
    """Test system metrics during load."""

    @pytest.mark.asyncio
    async def test_memory_usage_during_load(self, test_app):
        """Test memory usage remains acceptable during concurrent load."""
        import psutil

        process = psutil.Process()

        # Get baseline memory
        baseline_memory = process.memory_info().rss / 1024 / 1024  # MB

        simple_payload = {
            "title": "Memory Test",
            "description": "Test memory usage",
            "clips": [
                {
                    "video_url": "https://test-bucket.s3.amazonaws.com/video1.mp4",
                    "start_time": 0.0,
                    "end_time": 5.0,
                    "trim_start": 0.0,
                    "trim_end": 5.0,
                }
            ],
            "audio": {
                "music_url": None,
                "voiceover_url": None,
                "music_volume": 0.5,
                "voiceover_volume": 1.0,
                "original_audio_volume": 1.0,
            },
            "overlays": [],
            "output": {
                "resolution": "720p",
                "format": "mp4",
                "fps": 30,
                "bitrate": 2000000,
            },
        }

        async with AsyncClient(app=test_app, base_url="http://test") as client:
            # Create 20 compositions
            tasks = [client.post("/api/v1/compositions/", json=simple_payload) for _ in range(20)]

            await asyncio.gather(*tasks)

            # Check memory after load
            current_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = current_memory - baseline_memory

            print("\nMemory Usage Test:")
            print(f"  Baseline memory: {baseline_memory:.2f} MB")
            print(f"  Current memory: {current_memory:.2f} MB")
            print(f"  Memory increase: {memory_increase:.2f} MB")

            # Verify memory increase is reasonable (< 500MB for 20 compositions)
            assert memory_increase < 500, f"Memory increase {memory_increase:.2f}MB is too high"

    @pytest.mark.asyncio
    async def test_response_time_consistency(self, test_app):
        """Test response times remain consistent under load."""
        simple_payload = {
            "title": "Response Time Test",
            "description": "Test response time consistency",
            "clips": [
                {
                    "video_url": "https://test-bucket.s3.amazonaws.com/video1.mp4",
                    "start_time": 0.0,
                    "end_time": 5.0,
                    "trim_start": 0.0,
                    "trim_end": 5.0,
                }
            ],
            "audio": {
                "music_url": None,
                "voiceover_url": None,
                "music_volume": 0.5,
                "voiceover_volume": 1.0,
                "original_audio_volume": 1.0,
            },
            "overlays": [],
            "output": {
                "resolution": "720p",
                "format": "mp4",
                "fps": 30,
                "bitrate": 2000000,
            },
        }

        response_times = []

        async with AsyncClient(app=test_app, base_url="http://test") as client:
            # Send 50 requests and measure response times
            for _ in range(50):
                start_time = time.time()
                response = await client.post("/api/v1/compositions/", json=simple_payload)
                response_time = time.time() - start_time

                assert response.status_code == 202
                response_times.append(response_time)

        # Calculate statistics
        avg_time = sum(response_times) / len(response_times)
        min_time = min(response_times)
        max_time = max(response_times)

        # Calculate 95th percentile
        sorted_times = sorted(response_times)
        p95_index = int(len(sorted_times) * 0.95)
        p95_time = sorted_times[p95_index]

        print("\nResponse Time Consistency Test (50 requests):")
        print(f"  Average: {avg_time:.3f}s")
        print(f"  Min: {min_time:.3f}s")
        print(f"  Max: {max_time:.3f}s")
        print(f"  95th percentile: {p95_time:.3f}s")

        # Verify consistency
        # Max response time should not be more than 3x average
        assert max_time < (avg_time * 3), "Response times are too inconsistent"

        # 95th percentile should be < 2s
        assert p95_time < 2.0, "95th percentile response time is too high"
