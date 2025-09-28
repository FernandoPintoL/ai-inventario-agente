#!/usr/bin/env python3
"""
Development server runner with auto-reload and enhanced logging.
"""

import os
import sys
import uvicorn
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def run_development_server():
    """Run the development server with optimal settings."""

    # Ensure required directories exist
    os.makedirs("logs", exist_ok=True)

    # Check if .env file exists
    env_file = project_root / ".env"
    if not env_file.exists():
        print("WARNING: .env file not found!")
        print("   Please copy .env.example to .env and configure your settings.")
        return

    print("Starting Intelligent Agent Development Server...")
    print("Features enabled:")
    print("   * Auto-reload on file changes")
    print("   * Enhanced logging")
    print("   * API documentation at http://localhost:8000/docs")
    print("   * Health check at http://localhost:8000/api/v1/health")
    print("")

    try:
        uvicorn.run(
            "main:create_application",
            factory=True,
            host="0.0.0.0",
            port=8000,
            reload=True,
            reload_dirs=["app", "config"],
            log_level="debug",
            access_log=True,
            use_colors=True,
        )
    except KeyboardInterrupt:
        print("\nDevelopment server stopped.")
    except Exception as e:
        print(f"ERROR: Failed to start development server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_development_server()