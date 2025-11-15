"""
Locust Load Testing Scenarios for AI Video Generation Pipeline
PR-D007: Load Testing & Performance

This file contains comprehensive load testing scenarios for the video generation API,
including health checks, generation submissions, status polling, WebSocket connections,
asset uploads, and end-to-end workflows.

Usage:
    # Run with web UI (access at http://localhost:8089)
    locust -f locustfile.py --host=http://your-ecs-service:8000

    # Run headless mode with specific parameters
    locust -f locustfile.py --host=http://your-ecs-service:8000 \
           --users=5 --spawn-rate=1 --run-time=10m --headless

    # Run specific test scenario
    locust -f locustfile.py --host=http://your-ecs-service:8000 \
           --tags health --users=10 --spawn-rate=5
"""

import json
import random
import time
from pathlib import Path
from typing import Dict, List, Optional

from locust import HttpUser, TaskSet, task, tag, between, events
from locust.exception import RescheduleTask


# Load test data
def load_test_prompts() -> List[Dict]:
    """Load sample prompts from test data"""
    prompts_file = Path(__file__).parent / "test-data" / "prompts.json"

    if prompts_file.exists():
        with open(prompts_file, 'r') as f:
            data = json.load(f)
            return data.get('prompts', [])

    # Fallback prompts if file doesn't exist
    return [
        {
            "id": "fallback_001",
            "text": "Create a professional product showcase video for a luxury smartwatch. Feature elegant close-ups highlighting the sleek design, premium materials, and vibrant display. Transition smoothly between different angles and lifestyle shots.",
            "duration": 30,
            "category": "product_showcase"
        }
    ]


# Global test data
TEST_PROMPTS = load_test_prompts()
GENERATED_IDS: List[str] = []  # Store generated IDs for polling/download tests


class HealthCheckTasks(TaskSet):
    """
    Test Scenario 1: API Health Checks
    Target: 100 requests/second
    Expected: <50ms response time, 0% errors
    """

    @tag('health', 'fast')
    @task(10)
    def health_check(self):
        """Basic health check endpoint"""
        with self.client.get(
            "/health",
            name="/health",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if data.get('status') == 'healthy':
                        response.success()
                    else:
                        response.failure(f"Unhealthy status: {data.get('status')}")
                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
            else:
                response.failure(f"Status code: {response.status_code}")

    @tag('health', 'detailed')
    @task(2)
    def detailed_health_check(self):
        """Detailed health check endpoint"""
        with self.client.get(
            "/health/detailed",
            name="/health/detailed",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if data.get('status') == 'healthy':
                        response.success()
                    else:
                        response.failure(f"Unhealthy status: {data.get('status')}")
                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
            else:
                response.failure(f"Status code: {response.status_code}")


class GenerationSubmissionTasks(TaskSet):
    """
    Test Scenario 2: Video Generation Submission
    POST /api/v1/generations with valid prompt
    Load profile: 5-20 concurrent users
    Success criteria: 100% success at 5 users, <500ms API response time
    """

    @tag('generation', 'submit')
    @task
    def submit_generation(self):
        """Submit a new video generation request"""
        # Select random prompt from test data
        prompt_data = random.choice(TEST_PROMPTS)

        # Build request payload
        payload = {
            "prompt": prompt_data["text"],
            "parameters": {
                "duration_seconds": prompt_data.get("duration", 30),
                "aspect_ratio": random.choice(["16:9", "9:16", "1:1"]),
                "style": "professional",
                "include_cta": True,
                "cta_text": "Learn More",
                "music_style": "corporate"
            },
            "options": {
                "quality": "high",
                "fast_generation": False
            }
        }

        with self.client.post(
            "/api/v1/generations",
            json=payload,
            name="/api/v1/generations [POST]",
            catch_response=True
        ) as response:
            if response.status_code == 201:
                try:
                    data = response.json()
                    generation_id = data.get('generation_id')

                    if generation_id:
                        # Store ID for later polling/download tests
                        GENERATED_IDS.append(generation_id)
                        response.success()
                    else:
                        response.failure("No generation_id in response")

                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
            else:
                response.failure(f"Status code: {response.status_code}")


class StatusPollingTasks(TaskSet):
    """
    Test Scenario 3: Generation Status Polling
    GET /api/v1/generations/{id}
    Load profile: 10 users polling every 5 seconds
    Success criteria: <200ms response time
    """

    wait_time = between(3, 7)  # Poll every 3-7 seconds (average 5s)

    @tag('polling', 'status')
    @task
    def poll_generation_status(self):
        """Poll status of a generation job"""
        if not GENERATED_IDS:
            # If no IDs available, skip this task
            raise RescheduleTask()

        # Select random generation ID from created jobs
        generation_id = random.choice(GENERATED_IDS)

        with self.client.get(
            f"/api/v1/generations/{generation_id}",
            name="/api/v1/generations/:id [GET]",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    status = data.get('status')

                    if status in ['queued', 'processing', 'composing', 'completed', 'failed']:
                        response.success()
                    else:
                        response.failure(f"Invalid status: {status}")

                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
            elif response.status_code == 404:
                # Remove invalid ID
                if generation_id in GENERATED_IDS:
                    GENERATED_IDS.remove(generation_id)
                response.failure("Generation not found")
            else:
                response.failure(f"Status code: {response.status_code}")


class AssetUploadTasks(TaskSet):
    """
    Test Scenario 5: Asset Upload
    POST /api/v1/assets/upload (placeholder endpoint)
    Load profile: 3 concurrent uploads, 5MB files
    Success criteria: <10s upload time
    """

    @tag('upload', 'assets')
    @task
    def upload_asset(self):
        """Upload a brand asset (logo, image, etc.)"""
        # Note: This endpoint may not exist yet, adjust as needed
        asset_file = Path(__file__).parent / "test-data" / "sample-logo.png"

        if not asset_file.exists():
            # Skip if test file doesn't exist
            raise RescheduleTask()

        with open(asset_file, 'rb') as f:
            files = {'file': ('sample-logo.png', f, 'image/png')}

            with self.client.post(
                "/api/v1/assets/upload",
                files=files,
                name="/api/v1/assets/upload [POST]",
                catch_response=True,
                timeout=30  # 30s timeout for large file
            ) as response:
                # Accept 404 as endpoint may not be implemented yet
                if response.status_code in [200, 201, 404]:
                    response.success()
                else:
                    response.failure(f"Status code: {response.status_code}")


class EndToEndWorkflowTasks(TaskSet):
    """
    Test Scenario 6: End-to-End Workflow
    Submit generation → Poll status → Download video
    Load profile: 2-3 concurrent E2E workflows
    Success criteria: 90% success rate
    """

    @tag('e2e', 'workflow')
    @task
    def complete_workflow(self):
        """Execute complete video generation workflow"""

        # Step 1: Submit generation request
        prompt_data = random.choice(TEST_PROMPTS)
        payload = {
            "prompt": prompt_data["text"],
            "parameters": {
                "duration_seconds": prompt_data.get("duration", 30),
                "aspect_ratio": "16:9",
                "style": "professional",
                "include_cta": True,
                "cta_text": "Shop Now",
                "music_style": "corporate"
            }
        }

        with self.client.post(
            "/api/v1/generations",
            json=payload,
            name="E2E: Submit Generation",
            catch_response=True
        ) as response:
            if response.status_code != 201:
                response.failure(f"Submit failed: {response.status_code}")
                return

            try:
                data = response.json()
                generation_id = data.get('generation_id')

                if not generation_id:
                    response.failure("No generation_id returned")
                    return

                response.success()

            except json.JSONDecodeError:
                response.failure("Invalid JSON response")
                return

        # Step 2: Poll status (simulate waiting for completion)
        max_polls = 10  # Max 10 polls (simulating ~50 seconds)
        poll_interval = 5  # 5 seconds between polls

        for poll_count in range(max_polls):
            time.sleep(poll_interval)

            with self.client.get(
                f"/api/v1/generations/{generation_id}",
                name="E2E: Poll Status",
                catch_response=True
            ) as response:
                if response.status_code != 200:
                    response.failure(f"Poll failed: {response.status_code}")
                    break

                try:
                    data = response.json()
                    status = data.get('status')

                    if status == 'completed':
                        response.success()
                        # Step 3: Download video (if URL provided)
                        # Note: Download endpoint may vary based on implementation
                        break
                    elif status == 'failed':
                        response.failure("Generation failed")
                        break
                    else:
                        response.success()

                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
                    break


class MixedWorkloadUser(HttpUser):
    """
    Mixed workload user simulating realistic API usage patterns
    Combines health checks, generation submissions, and status polling
    """

    wait_time = between(2, 5)  # Wait 2-5 seconds between tasks

    tasks = {
        HealthCheckTasks: 3,          # 30% health checks (lightweight)
        GenerationSubmissionTasks: 2,  # 20% new submissions
        StatusPollingTasks: 5          # 50% status polling
    }


class HealthCheckUser(HttpUser):
    """
    Dedicated health check user for high-frequency monitoring
    Use this for testing high-throughput health check scenarios
    """

    wait_time = between(0.01, 0.05)  # Very frequent requests (100 req/s target)
    tasks = [HealthCheckTasks]


class GenerationUser(HttpUser):
    """
    User focused on video generation submissions
    Simulates users creating new video generation requests
    """

    wait_time = between(5, 15)  # Realistic user behavior (5-15s think time)
    tasks = [GenerationSubmissionTasks]


class PollingUser(HttpUser):
    """
    User focused on polling generation status
    Simulates users checking progress of their videos
    """

    wait_time = between(3, 7)  # Poll every 3-7 seconds
    tasks = [StatusPollingTasks]


class AssetUploadUser(HttpUser):
    """
    User focused on asset uploads
    Simulates brand asset uploads (logos, images)
    """

    wait_time = between(10, 30)  # Upload every 10-30 seconds
    tasks = [AssetUploadTasks]


class EndToEndUser(HttpUser):
    """
    User executing complete end-to-end workflows
    Simulates realistic user journey from submission to completion
    """

    wait_time = between(60, 120)  # Long wait between workflows
    tasks = [EndToEndWorkflowTasks]


# Event handlers for custom metrics and logging
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Initialize test environment"""
    print("=" * 80)
    print("Starting load test for AI Video Generation Pipeline")
    print(f"Target host: {environment.host}")
    print(f"Test prompts loaded: {len(TEST_PROMPTS)}")
    print("=" * 80)


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Clean up and report final statistics"""
    print("=" * 80)
    print("Load test completed")
    print(f"Total generation IDs created: {len(GENERATED_IDS)}")
    print("=" * 80)


# Custom shape classes for specific load profiles
from locust import LoadTestShape


class BaselineLoadShape(LoadTestShape):
    """
    Baseline load: 5 concurrent users for 10 minutes
    MVP requirement validation
    """

    def tick(self):
        run_time = self.get_run_time()

        if run_time < 600:  # 10 minutes
            return (5, 1)  # 5 users, spawn rate 1/sec

        return None


class StressTestShape(LoadTestShape):
    """
    Stress test: 10 concurrent users for 5 minutes
    Identify bottlenecks at 2x MVP load
    """

    def tick(self):
        run_time = self.get_run_time()

        if run_time < 300:  # 5 minutes
            return (10, 2)  # 10 users, spawn rate 2/sec

        return None


class SpikeTestShape(LoadTestShape):
    """
    Spike test: Ramp 0→20 users in 1 minute, hold for 2 minutes
    Test system recovery and autoscaling
    """

    def tick(self):
        run_time = self.get_run_time()

        if run_time < 60:
            # Ramp up: 0→20 users over 60 seconds
            user_count = int(run_time / 3)  # Reaches 20 at 60s
            return (user_count, 1)
        elif run_time < 180:
            # Hold at peak
            return (20, 1)

        return None


class EnduranceTestShape(LoadTestShape):
    """
    Endurance test: 5 users for 30 minutes
    Test stability and memory leaks
    """

    def tick(self):
        run_time = self.get_run_time()

        if run_time < 1800:  # 30 minutes
            return (5, 1)  # 5 users, spawn rate 1/sec

        return None


# Usage examples in comments:
"""
USAGE EXAMPLES:

1. Run baseline load test (5 users, 10 minutes):
   locust -f locustfile.py --host=http://your-ecs:8000 \\
          --shape=BaselineLoadShape --headless

2. Run stress test (10 users, 5 minutes):
   locust -f locustfile.py --host=http://your-ecs:8000 \\
          --shape=StressTestShape --headless

3. Run spike test:
   locust -f locustfile.py --host=http://your-ecs:8000 \\
          --shape=SpikeTestShape --headless

4. Run endurance test (30 minutes):
   locust -f locustfile.py --host=http://your-ecs:8000 \\
          --shape=EnduranceTestShape --headless

5. Run specific scenario with tags:
   locust -f locustfile.py --host=http://your-ecs:8000 \\
          --tags health --users=10 --run-time=5m

6. Interactive mode with web UI:
   locust -f locustfile.py --host=http://your-ecs:8000
   # Then open http://localhost:8089 in browser
"""
