#!/usr/bin/env python
"""Validate configuration settings and feature flags."""
# ruff: noqa: T201, C901
import sys
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def main() -> int:
    """Validate configuration and exit with appropriate code.

    Returns:
        0 if valid, 1 if errors found
    """
    try:
        from app.config import get_settings
        from app.feature_flags import check_feature_dependencies

        print("🔍 Validating configuration...")
        print()

        # Load settings
        settings = get_settings()

        # Print basic info
        print(f"Application: {settings.app_name} v{settings.app_version}")
        print(f"Environment: {settings.environment}")
        print(f"Debug Mode: {settings.debug}")
        print()

        # Validate configuration
        errors = settings.validate_configuration()

        if errors:
            print("❌ Configuration Errors:")
            for error in errors:
                print(f"  - {error}")
            print()
            return 1

        print("✅ Configuration is valid")
        print()

        # Check feature flag dependencies
        print("🚩 Feature Flags:")
        for flag_name, enabled in settings.get_feature_flags().items():
            status = "✓ ENABLED" if enabled else "✗ DISABLED"
            print(f"  {flag_name}: {status}")
        print()

        # Check for warnings
        warnings = check_feature_dependencies()
        if warnings:
            print("⚠️  Warnings:")
            for warning in warnings:
                print(f"  - {warning}")
            print()

        # Print critical settings
        print("🔧 Critical Settings:")
        print(f"  Database Pool Size: {settings.db_pool_size}")
        print(f"  Redis Max Connections: {settings.redis_max_connections}")
        print(f"  Max Concurrent Jobs: {settings.max_concurrent_jobs}")
        print(f"  S3 Bucket: {settings.s3_bucket_name or '(not configured)'}")
        print()

        if settings.is_production:
            print("🔒 Production Mode - Additional Checks:")
            if not settings.s3_bucket_name:
                print("  ⚠️  S3 bucket not configured")
            if not settings.internal_api_keys:
                print("  ⚠️  No internal API keys configured")
            if settings.debug:
                print("  ⚠️  Debug mode should be disabled in production")
            print()

        print("✅ All validation checks passed!")
        return 0

    except Exception as e:
        print(f"❌ Fatal Error: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
