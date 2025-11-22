"""
Locust load testing configuration for FFmpeg Backend API.

Usage:
    # Run load test with 5 concurrent users
    locust -f tests/load/locustfile.py --users 5 --spawn-rate 1 --host http://localhost:8000

    # Run load test for 30 minutes
    locust -f tests/load/locustfile.py --users 5 --spawn-rate 1 --run-time 30m --host http://localhost:8000

    # Run headless mode with specific duration
    locust -f tests/load/locustfile.py --headless --users 10 --spawn-rate 2 --run-time 10m --host http://localhost:8000
"""

import random

from locust import HttpUser, between, task


class CompositionUser(HttpUser):
    """
    Simulates a user creating and monitoring video compositions.

    This user will:
    1. Create compositions (simple and complex)
    2. Poll composition status
    3. Retrieve composition metadata
    4. Download completed compositions
    """

    # Wait 1-3 seconds between tasks
    wait_time = between(1, 3)

    # Track created compositions
    composition_ids: list[str] = []

    def on_start(self):
        """Called when a user starts."""
        self.composition_ids = []
        print(f"Starting user {self.environment.runner.user_count}")

    @task(5)
    def create_simple_composition(self):
        """Create a simple 2-clip composition (most common scenario)."""
        payload = {
            "title": f"Load Test Simple - {random.randint(1000, 9999)}",
            "description": "Simple composition for load testing",
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

        with self.client.post(
            "/api/v1/compositions/",
            json=payload,
            catch_response=True,
        ) as response:
            if response.status_code == 202:
                composition_data = response.json()
                composition_id = composition_data.get("id")
                if composition_id:
                    self.composition_ids.append(composition_id)
                response.success()
            else:
                response.failure(f"Failed to create composition: {response.status_code}")

    @task(2)
    def create_complex_composition(self):
        """Create a complex composition with multiple clips and overlays."""
        # Create 5 clips
        clips = []
        for i in range(5):
            clips.append(
                {
                    "video_url": f"https://test-bucket.s3.amazonaws.com/video{i}.mp4",
                    "start_time": i * 3.0,
                    "end_time": (i + 1) * 3.0,
                    "trim_start": 0.0,
                    "trim_end": 3.0,
                }
            )

        payload = {
            "title": f"Load Test Complex - {random.randint(1000, 9999)}",
            "description": "Complex composition for load testing",
            "clips": clips,
            "audio": {
                "music_url": "https://test-bucket.s3.amazonaws.com/music.mp3",
                "voiceover_url": None,
                "music_volume": 0.3,
                "voiceover_volume": 1.0,
                "original_audio_volume": 0.8,
            },
            "overlays": [
                {
                    "text": "Load Test",
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

        with self.client.post(
            "/api/v1/compositions/",
            json=payload,
            catch_response=True,
        ) as response:
            if response.status_code == 202:
                composition_data = response.json()
                composition_id = composition_data.get("id")
                if composition_id:
                    self.composition_ids.append(composition_id)
                response.success()
            else:
                response.failure(f"Failed to create complex composition: {response.status_code}")

    @task(10)
    def check_composition_status(self):
        """Poll composition status (most frequent operation)."""
        if not self.composition_ids:
            return

        composition_id = random.choice(self.composition_ids)

        with self.client.get(
            f"/api/v1/compositions/{composition_id}/status",
            name="/api/v1/compositions/[id]/status",
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                status_data = response.json()
                # Verify expected fields
                if "overall_progress" in status_data and "status" in status_data:
                    response.success()
                else:
                    response.failure("Missing expected fields in status response")
            elif response.status_code == 404:
                # Composition might have been cleaned up
                self.composition_ids.remove(composition_id)
                response.success()
            else:
                response.failure(f"Unexpected status code: {response.status_code}")

    @task(3)
    def get_composition_metadata(self):
        """Retrieve detailed composition metadata."""
        if not self.composition_ids:
            return

        composition_id = random.choice(self.composition_ids)

        with self.client.get(
            f"/api/v1/compositions/{composition_id}/metadata",
            name="/api/v1/compositions/[id]/metadata",
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 404:
                # Composition might have been cleaned up
                self.composition_ids.remove(composition_id)
                response.success()
            else:
                response.failure(f"Unexpected status code: {response.status_code}")

    @task(1)
    def attempt_download(self):
        """Attempt to download a composition (less frequent)."""
        if not self.composition_ids:
            return

        composition_id = random.choice(self.composition_ids)

        with self.client.get(
            f"/api/v1/compositions/{composition_id}/download",
            name="/api/v1/compositions/[id]/download",
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                # Successfully got download URL
                response.success()
            elif response.status_code == 400:
                # Composition not completed yet (expected)
                response.success()
            elif response.status_code == 404:
                # Composition not found
                self.composition_ids.remove(composition_id)
                response.success()
            else:
                response.failure(f"Unexpected status code: {response.status_code}")


class HealthCheckUser(HttpUser):
    """Simulates users checking health endpoints."""

    wait_time = between(5, 10)

    @task
    def check_health(self):
        """Check basic health endpoint."""
        self.client.get("/health")

    @task
    def check_detailed_health(self):
        """Check detailed health endpoint."""
        self.client.get("/health/detailed")


# Performance test scenarios


class BurstLoadUser(HttpUser):
    """Simulates burst load - many compositions created quickly."""

    wait_time = between(0.1, 0.5)  # Very short wait time

    @task
    def create_composition_burst(self):
        """Create compositions in rapid succession."""
        payload = {
            "title": f"Burst Test - {random.randint(1000, 9999)}",
            "description": "Burst load test",
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

        self.client.post("/api/v1/compositions/", json=payload)


class SustainedLoadUser(HttpUser):
    """Simulates sustained load over long period."""

    wait_time = between(10, 30)  # Longer wait time for sustained load

    @task(3)
    def create_composition(self):
        """Create composition at steady rate."""
        payload = {
            "title": f"Sustained Test - {random.randint(1000, 9999)}",
            "description": "Sustained load test",
            "clips": [
                {
                    "video_url": "https://test-bucket.s3.amazonaws.com/video1.mp4",
                    "start_time": 0.0,
                    "end_time": 10.0,
                    "trim_start": 0.0,
                    "trim_end": 10.0,
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

        self.client.post("/api/v1/compositions/", json=payload)

    @task(7)
    def check_status(self):
        """Poll status frequently."""
        # In real scenario, would track composition IDs
        # For now, just test health endpoint
        self.client.get("/health")
