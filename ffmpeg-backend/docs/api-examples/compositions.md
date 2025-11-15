# Composition API Examples

Complete examples for working with the Composition API in various languages.

## Table of Contents

- [Creating Compositions](#creating-compositions)
- [Retrieving Composition Status](#retrieving-composition-status)
- [Downloading Results](#downloading-results)
- [Error Handling](#error-handling)
- [WebSocket Subscriptions](#websocket-subscriptions)

## Creating Compositions

### Python Example

```python
import httpx
import asyncio
from typing import Dict, Any

async def create_composition() -> Dict[str, Any]:
    """Create a video composition with multiple clips and overlays."""

    composition_data = {
        "title": "My Awesome Video",
        "clips": [
            {
                "video_url": "https://example.com/clip1.mp4",
                "start_time": 0.0,
                "end_time": 10.0,
                "trim_start": 0.0,
                "trim_end": None
            },
            {
                "video_url": "https://example.com/clip2.mp4",
                "start_time": 10.0,
                "end_time": 20.0,
                "trim_start": 2.0,
                "trim_end": 12.0
            }
        ],
        "audio": {
            "music_url": "https://example.com/background.mp3",
            "music_volume": 0.3,
            "voiceover_url": None,
            "voiceover_volume": 0.7,
            "original_audio_volume": 0.5
        },
        "overlays": [
            {
                "text": "Welcome!",
                "position": "center",
                "start_time": 0.0,
                "end_time": 3.0,
                "font_size": 48,
                "font_color": "#FFFFFF"
            }
        ],
        "output": {
            "resolution": "1080p",
            "format": "mp4",
            "fps": 30,
            "quality": "high"
        }
    }

    async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
        response = await client.post(
            "/api/v1/compositions",
            json=composition_data,
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        return response.json()

# Run the example
if __name__ == "__main__":
    result = asyncio.run(create_composition())
    print(f"Composition created: {result['composition_id']}")
    print(f"Status: {result['status']}")
```

### JavaScript/TypeScript Example

```typescript
interface Composition {
  title: string;
  clips: Array<{
    video_url: string;
    start_time: number;
    end_time: number;
    trim_start?: number;
    trim_end?: number;
  }>;
  audio: {
    music_url?: string;
    voiceover_url?: string;
    music_volume: number;
    voiceover_volume: number;
    original_audio_volume: number;
  };
  overlays: Array<{
    text: string;
    position: 'top-left' | 'top-center' | 'top-right' | 'center' | 'bottom-left' | 'bottom-center' | 'bottom-right';
    start_time: number;
    end_time: number;
    font_size: number;
    font_color: string;
  }>;
  output: {
    resolution: '720p' | '1080p' | '4k';
    format: 'mp4' | 'mov' | 'webm';
    fps: number;
    quality: 'low' | 'medium' | 'high';
  };
}

async function createComposition(): Promise<any> {
  const compositionData: Composition = {
    title: "My Awesome Video",
    clips: [
      {
        video_url: "https://example.com/clip1.mp4",
        start_time: 0.0,
        end_time: 10.0,
        trim_start: 0.0
      },
      {
        video_url: "https://example.com/clip2.mp4",
        start_time: 10.0,
        end_time: 20.0,
        trim_start: 2.0,
        trim_end: 12.0
      }
    ],
    audio: {
      music_url: "https://example.com/background.mp3",
      music_volume: 0.3,
      voiceover_volume: 0.7,
      original_audio_volume: 0.5
    },
    overlays: [
      {
        text: "Welcome!",
        position: "center",
        start_time: 0.0,
        end_time: 3.0,
        font_size: 48,
        font_color: "#FFFFFF"
      }
    ],
    output: {
      resolution: "1080p",
      format: "mp4",
      fps: 30,
      quality: "high"
    }
  };

  try {
    const response = await fetch('http://localhost:8000/api/v1/compositions', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(compositionData),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const result = await response.json();
    console.log(`Composition created: ${result.composition_id}`);
    console.log(`Status: ${result.status}`);
    return result;
  } catch (error) {
    console.error('Error creating composition:', error);
    throw error;
  }
}

// Run the example
createComposition();
```

### cURL Example

```bash
curl -X POST "http://localhost:8000/api/v1/compositions" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "My Awesome Video",
    "clips": [
      {
        "video_url": "https://example.com/clip1.mp4",
        "start_time": 0.0,
        "end_time": 10.0,
        "trim_start": 0.0
      },
      {
        "video_url": "https://example.com/clip2.mp4",
        "start_time": 10.0,
        "end_time": 20.0,
        "trim_start": 2.0,
        "trim_end": 12.0
      }
    ],
    "audio": {
      "music_url": "https://example.com/background.mp3",
      "music_volume": 0.3,
      "voiceover_volume": 0.7,
      "original_audio_volume": 0.5
    },
    "overlays": [
      {
        "text": "Welcome!",
        "position": "center",
        "start_time": 0.0,
        "end_time": 3.0,
        "font_size": 48,
        "font_color": "#FFFFFF"
      }
    ],
    "output": {
      "resolution": "1080p",
      "format": "mp4",
      "fps": 30,
      "quality": "high"
    }
  }'
```

## Retrieving Composition Status

### Python Example

```python
import httpx
import asyncio

async def get_composition_status(composition_id: str) -> dict:
    """Get the current status of a composition."""
    async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
        response = await client.get(f"/api/v1/compositions/{composition_id}")
        response.raise_for_status()
        return response.json()

async def poll_until_complete(composition_id: str, timeout: int = 300):
    """Poll composition status until complete or timeout."""
    import time
    start_time = time.time()

    while time.time() - start_time < timeout:
        status = await get_composition_status(composition_id)

        print(f"Status: {status['status']}")
        if status.get('progress'):
            print(f"Progress: {status['progress']}%")

        if status['status'] == 'completed':
            print("Composition completed!")
            return status
        elif status['status'] == 'failed':
            print(f"Composition failed: {status.get('error_message')}")
            return status

        await asyncio.sleep(5)  # Poll every 5 seconds

    raise TimeoutError("Composition did not complete within timeout period")
```

### JavaScript Example

```javascript
async function pollCompositionStatus(compositionId, timeout = 300000) {
  const startTime = Date.now();
  const pollInterval = 5000; // 5 seconds

  while (Date.now() - startTime < timeout) {
    const response = await fetch(
      `http://localhost:8000/api/v1/compositions/${compositionId}`
    );

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const status = await response.json();
    console.log(`Status: ${status.status}`);

    if (status.progress) {
      console.log(`Progress: ${status.progress}%`);
    }

    if (status.status === 'completed') {
      console.log('Composition completed!');
      return status;
    } else if (status.status === 'failed') {
      console.error(`Composition failed: ${status.error_message}`);
      throw new Error(status.error_message);
    }

    await new Promise(resolve => setTimeout(resolve, pollInterval));
  }

  throw new Error('Composition did not complete within timeout period');
}
```

### cURL Example

```bash
# Check composition status
curl -X GET "http://localhost:8000/api/v1/compositions/{composition_id}"

# Watch for changes (using watch command)
watch -n 5 curl -s "http://localhost:8000/api/v1/compositions/{composition_id}" | jq '.status, .progress'
```

## Downloading Results

### Python Example

```python
import httpx
import asyncio
from pathlib import Path

async def download_composition(composition_id: str, output_path: str):
    """Download completed composition to local file."""
    async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
        # Get download URL
        response = await client.get(f"/api/v1/compositions/{composition_id}/download")
        response.raise_for_status()
        download_data = response.json()

        # Download file
        async with client.stream('GET', download_data['download_url']) as stream:
            stream.raise_for_status()
            with open(output_path, 'wb') as f:
                async for chunk in stream.aiter_bytes():
                    f.write(chunk)

        print(f"Downloaded to: {output_path}")
        print(f"File size: {download_data['file_size']} bytes")
```

### JavaScript Example

```javascript
async function downloadComposition(compositionId, outputPath) {
  // Get download URL
  const response = await fetch(
    `http://localhost:8000/api/v1/compositions/${compositionId}/download`
  );

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  const downloadData = await response.json();

  // Download file (Node.js)
  const fs = require('fs');
  const fileStream = fs.createWriteStream(outputPath);

  const downloadResponse = await fetch(downloadData.download_url);
  const buffer = await downloadResponse.arrayBuffer();

  fileStream.write(Buffer.from(buffer));
  fileStream.end();

  console.log(`Downloaded to: ${outputPath}`);
  console.log(`File size: ${downloadData.file_size} bytes`);
}

// Browser example (download to user's computer)
async function downloadCompositionBrowser(compositionId) {
  const response = await fetch(
    `http://localhost:8000/api/v1/compositions/${compositionId}/download`
  );

  const downloadData = await response.json();

  // Create download link and trigger
  const link = document.createElement('a');
  link.href = downloadData.download_url;
  link.download = `composition_${compositionId}.mp4`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}
```

## WebSocket Subscriptions

### Python Example

```python
import asyncio
import websockets
import json

async def subscribe_to_composition(composition_id: str):
    """Subscribe to real-time composition updates via WebSocket."""
    uri = f"ws://localhost:8000/api/v1/ws/compositions/{composition_id}"

    async with websockets.connect(uri) as websocket:
        print(f"Connected to WebSocket for composition {composition_id}")

        try:
            async for message in websocket:
                data = json.loads(message)

                if data['type'] == 'progress':
                    print(f"Progress: {data['progress']}%")
                    print(f"Stage: {data.get('stage', 'processing')}")
                elif data['type'] == 'status':
                    print(f"Status changed: {data['status']}")
                    if data['status'] == 'completed':
                        print("Composition completed!")
                        break
                    elif data['status'] == 'failed':
                        print(f"Failed: {data.get('error')}")
                        break
                elif data['type'] == 'error':
                    print(f"Error: {data['message']}")
                    break
        except websockets.exceptions.ConnectionClosed:
            print("WebSocket connection closed")

# Run example
asyncio.run(subscribe_to_composition("YOUR_COMPOSITION_ID"))
```

### JavaScript Example

```javascript
function subscribeToComposition(compositionId) {
  const ws = new WebSocket(
    `ws://localhost:8000/api/v1/ws/compositions/${compositionId}`
  );

  ws.onopen = () => {
    console.log(`Connected to WebSocket for composition ${compositionId}`);
  };

  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);

    switch (data.type) {
      case 'progress':
        console.log(`Progress: ${data.progress}%`);
        console.log(`Stage: ${data.stage || 'processing'}`);
        // Update UI progress bar
        updateProgressBar(data.progress);
        break;

      case 'status':
        console.log(`Status changed: ${data.status}`);
        if (data.status === 'completed') {
          console.log('Composition completed!');
          ws.close();
        } else if (data.status === 'failed') {
          console.error(`Failed: ${data.error}`);
          ws.close();
        }
        break;

      case 'error':
        console.error(`Error: ${data.message}`);
        ws.close();
        break;
    }
  };

  ws.onerror = (error) => {
    console.error('WebSocket error:', error);
  };

  ws.onclose = () => {
    console.log('WebSocket connection closed');
  };

  return ws;
}

function updateProgressBar(progress) {
  // Example UI update
  const progressBar = document.getElementById('progress-bar');
  if (progressBar) {
    progressBar.style.width = `${progress}%`;
    progressBar.textContent = `${progress}%`;
  }
}
```

## Error Handling

### Common Error Codes

| Status Code | Error Type | Description |
|-------------|-----------|-------------|
| 400 | Bad Request | Invalid request data or validation error |
| 404 | Not Found | Composition not found |
| 409 | Conflict | Composition already exists or in invalid state |
| 422 | Unprocessable Entity | Validation error with detailed field information |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server error during processing |
| 503 | Service Unavailable | Service temporarily unavailable |

### Error Response Format

```json
{
  "detail": {
    "error_code": "VALIDATION_ERROR",
    "message": "Invalid composition configuration",
    "fields": {
      "clips": ["At least one clip is required"],
      "output.resolution": ["Invalid resolution. Must be one of: 720p, 1080p, 4k"]
    },
    "request_id": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

### Python Error Handling

```python
import httpx
from typing import Dict, Any

async def create_composition_with_error_handling(data: Dict[str, Any]):
    """Create composition with comprehensive error handling."""
    try:
        async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
            response = await client.post("/api/v1/compositions", json=data)
            response.raise_for_status()
            return response.json()

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 400:
            error_detail = e.response.json()
            print(f"Validation error: {error_detail['detail']['message']}")
            if 'fields' in error_detail['detail']:
                for field, errors in error_detail['detail']['fields'].items():
                    print(f"  {field}: {', '.join(errors)}")
        elif e.response.status_code == 429:
            print("Rate limit exceeded. Please wait before retrying.")
        elif e.response.status_code == 503:
            print("Service temporarily unavailable. Please retry later.")
        else:
            print(f"HTTP error {e.response.status_code}: {e.response.text}")
        raise

    except httpx.RequestError as e:
        print(f"Network error: {e}")
        raise

    except Exception as e:
        print(f"Unexpected error: {e}")
        raise
```

### JavaScript Error Handling

```javascript
async function createCompositionWithErrorHandling(data) {
  try {
    const response = await fetch('http://localhost:8000/api/v1/compositions', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const errorDetail = await response.json();

      switch (response.status) {
        case 400:
          console.error(`Validation error: ${errorDetail.detail.message}`);
          if (errorDetail.detail.fields) {
            Object.entries(errorDetail.detail.fields).forEach(([field, errors]) => {
              console.error(`  ${field}: ${errors.join(', ')}`);
            });
          }
          break;

        case 429:
          console.error('Rate limit exceeded. Please wait before retrying.');
          break;

        case 503:
          console.error('Service temporarily unavailable. Please retry later.');
          break;

        default:
          console.error(`HTTP error ${response.status}: ${errorDetail.detail.message}`);
      }

      throw new Error(errorDetail.detail.message);
    }

    return await response.json();
  } catch (error) {
    if (error instanceof TypeError) {
      console.error('Network error:', error.message);
    }
    throw error;
  }
}
```

## Complete Workflow Example

### Python Complete Workflow

```python
import asyncio
import httpx
from typing import Dict, Any

async def complete_composition_workflow():
    """Complete workflow: create, monitor, and download composition."""

    # Step 1: Create composition
    composition_data = {
        "title": "Complete Workflow Example",
        "clips": [
            {
                "video_url": "https://example.com/clip1.mp4",
                "start_time": 0.0,
                "end_time": 10.0
            }
        ],
        "audio": {
            "music_volume": 0.3,
            "voiceover_volume": 0.7,
            "original_audio_volume": 0.5
        },
        "overlays": [],
        "output": {
            "resolution": "1080p",
            "format": "mp4",
            "fps": 30,
            "quality": "high"
        }
    }

    async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
        # Create
        print("Creating composition...")
        create_response = await client.post("/api/v1/compositions", json=composition_data)
        create_response.raise_for_status()
        result = create_response.json()
        composition_id = result['composition_id']
        print(f"Created: {composition_id}")

        # Monitor
        print("Monitoring progress...")
        while True:
            status_response = await client.get(f"/api/v1/compositions/{composition_id}")
            status_response.raise_for_status()
            status = status_response.json()

            print(f"Status: {status['status']}, Progress: {status.get('progress', 0)}%")

            if status['status'] == 'completed':
                break
            elif status['status'] == 'failed':
                raise Exception(f"Composition failed: {status.get('error_message')}")

            await asyncio.sleep(5)

        # Download
        print("Downloading result...")
        download_response = await client.get(f"/api/v1/compositions/{composition_id}/download")
        download_response.raise_for_status()
        download_data = download_response.json()

        print(f"Download URL: {download_data['download_url']}")
        print(f"Expires at: {download_data['expires_at']}")
        print("Workflow complete!")

if __name__ == "__main__":
    asyncio.run(complete_composition_workflow())
```
