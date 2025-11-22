#!/usr/bin/env python3
"""
AI CLI Setup Script
===================

This script helps set up the AI testing CLI environment.
It checks dependencies, creates a .env file if needed, and verifies API keys.
"""

import os
import sys
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are installed"""
    required_packages = [
        'openai', 'replicate', 'tenacity', 'pydantic', 'python-dotenv',
        'pytest', 'pytest-asyncio'
    ]

    missing = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing.append(package)

    if missing:
        print("ERROR: Missing dependencies:")
        for pkg in missing:
            print(f"  - {pkg}")
        print("\nInstall with: pip install -r requirements.txt")
        return False

    print("SUCCESS: All dependencies installed")
    return True

def setup_env_file():
    """Create .env file if it doesn't exist"""
    env_file = Path('.env')
    env_example = Path('env.example')

    if env_file.exists():
        print("INFO: .env file already exists")
        return True

    if not env_example.exists():
        print("ERROR: env.example file not found")
        return False

    try:
        # Copy env.example to .env
        with open(env_example, 'r') as src, open(env_file, 'w') as dst:
            dst.write(src.read())

        print("SUCCESS: Created .env file from env.example")
        print("WARNING: Please edit .env and add your API keys:")
        print("  - OPENAI_API_KEY")
        print("  - REPLICATE_API_TOKEN")
        return True

    except Exception as e:
        print(f"ERROR: Failed to create .env file: {e}")
        return False

def check_api_keys():
    """Check if API keys are configured"""
    openai_key = os.getenv('OPENAI_API_KEY')
    replicate_token = os.getenv('REPLICATE_API_TOKEN')

    if not openai_key or openai_key.startswith('CHANGE_ME'):
        print("WARNING: OPENAI_API_KEY not configured")
    else:
        print("SUCCESS: OpenAI API key configured")

    if not replicate_token or replicate_token.startswith('CHANGE_ME'):
        print("WARNING: REPLICATE_API_TOKEN not configured")
    else:
        print("SUCCESS: Replicate API token configured")

def main():
    """Main setup function"""
    print("AI Video Generation CLI Setup")
    print("=" * 40)

    # Change to script directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)

    # Check dependencies
    if not check_dependencies():
        sys.exit(1)

    # Setup environment file
    if not setup_env_file():
        sys.exit(1)

    # Load environment and check keys
    from dotenv import load_dotenv
    load_dotenv()
    check_api_keys()

    print("\nSUCCESS: Setup complete!")
    print("\nTo run the CLI:")
    print("  python cli.py              # Interactive mode")
    print("  python cli.py --mock       # Mock mode (no API calls)")
    print("  python cli.py --help       # Show help")

if __name__ == '__main__':
    main()
