#!/usr/bin/env python3
"""
Test real video generation from Replicate
"""
import asyncio
import sys
from pathlib import Path

# Add ai directory to path
ai_dir = Path(__file__).parent / 'ai'
sys.path.insert(0, str(ai_dir))

from cli import AIModuleTester

async def test_real_video():
    """Test real video generation"""
    tester = AIModuleTester(use_mock=False)

    print("Testing REAL video generation from Replicate API...")
    print("=" * 60)

    # Test with a simple prompt
    await tester.run_complete_video_pipeline("Create a professional video about innovation")

    # Check what files were created
    test_storage_dir = Path(__file__).parent / 'test-storage'
    if test_storage_dir.exists():
        files = list(test_storage_dir.glob("*.mp4"))
        print(f"\nFiles created: {len(files)}")
        for file_path in files:
            size = file_path.stat().st_size
            print(f"  - {file_path.name}: {size} bytes")

            # Check content
            with open(file_path, 'rb') as f:
                content = f.read(500)
                if b'ftypmp41' in content and len(content) > 1000:
                    print("    [REAL] Contains actual video data from Replicate!")
                elif b'GENERATED_MICRO_PROMPT' in content:
                    print("    [FALLBACK] Contains micro-prompt content (service worked)")
                else:
                    print("    [UNKNOWN] Unknown content type")

if __name__ == "__main__":
    asyncio.run(test_real_video())
