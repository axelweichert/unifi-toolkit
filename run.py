#!/usr/bin/env python3
"""
UI Toolkit - Application Entry Point

This script starts the UI Toolkit web application.
It checks for required environment variables and starts the FastAPI server.
"""
import os
import sys
from pathlib import Path

# Check if .env file exists
env_file = Path(__file__).parent / ".env"
if not env_file.exists():
    print("=" * 70)
    print("ERROR: .env file not found!")
    print("=" * 70)
    print()
    print("Please create a .env file in the project root directory.")
    print("You can copy .env.example as a starting point:")
    print()
    print("  cp .env.example .env")
    print()
    print("Then edit .env and set the required values:")
    print("  - ENCRYPTION_KEY (required)")
    print("  - UniFi controller settings (optional, can configure via web UI)")
    print()
    print("=" * 70)
    sys.exit(1)

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv(env_file)
except ImportError:
    print("WARNING: python-dotenv not installed, .env file will not be loaded")
    print("Install it with: pip install python-dotenv")

# Check for required environment variables
encryption_key = os.getenv("ENCRYPTION_KEY")
if not encryption_key:
    print("=" * 70)
    print("ERROR: ENCRYPTION_KEY not set in .env file!")
    print("=" * 70)
    print()
    print("The ENCRYPTION_KEY is required to encrypt sensitive data.")
    print("Generate a new key with:")
    print()
    print("  python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\"")
    print()
    print("Then add it to your .env file:")
    print()
    print("  ENCRYPTION_KEY=your_generated_key_here")
    print()
    print("=" * 70)
    sys.exit(1)

# Run database migrations before starting the app
# This runs in a normal synchronous context, avoiding any async/uvicorn complications
def run_migrations():
    """Run Alembic migrations before uvicorn starts."""
    try:
        from alembic.config import Config
        from alembic import command

        print("Running database migrations...")
        alembic_cfg = Config("alembic.ini")
        command.upgrade(alembic_cfg, "head")
        print("Database migrations completed successfully")

    except Exception as e:
        error_msg = str(e).lower()

        # Check for common schema sync issues
        schema_sync_errors = [
            "already exists",
            "duplicate column",
            "table already exists",
            "unique constraint failed",
        ]

        is_schema_sync_issue = any(err in error_msg for err in schema_sync_errors)

        if is_schema_sync_issue:
            print(f"Migration detected schema sync issue: {e}")
            print("Attempting to synchronize migration history...")

            try:
                from alembic.config import Config
                from alembic import command

                alembic_cfg = Config("alembic.ini")
                command.stamp(alembic_cfg, "head")
                print("Migration history synchronized with current schema")
            except Exception as stamp_error:
                print(f"Failed to synchronize migration history: {stamp_error}")
        else:
            print(f"Migration warning: {e}")
            print("The application will continue, but some features may not work correctly.")

    # Always run schema repair after migrations to catch cases where
    # stamping to head skipped actual column additions
    _repair_schema()


def _repair_schema():
    """
    Check for and add missing columns that migrations may have skipped.

    This handles the case where init_db's create_all creates new tables,
    causing alembic to fail with 'already exists' and stamp to head,
    skipping ADD COLUMN operations on existing tables.
    """
    import sqlite3
    from pathlib import Path

    db_path = Path("./data/unifi_toolkit.db")
    if not db_path.exists():
        return  # No database yet, nothing to repair

    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # Get existing columns for threats_events
        cursor.execute("PRAGMA table_info(threats_events)")
        existing_columns = {row[1] for row in cursor.fetchall()}

        if not existing_columns:
            conn.close()
            return  # Table doesn't exist yet

        # Check for missing columns and add them
        missing_columns = {
            'ignored': "ALTER TABLE threats_events ADD COLUMN ignored BOOLEAN NOT NULL DEFAULT 0",
            'ignored_by_rule_id': "ALTER TABLE threats_events ADD COLUMN ignored_by_rule_id INTEGER",
        }

        for col_name, sql in missing_columns.items():
            if col_name not in existing_columns:
                print(f"Schema repair: adding missing column '{col_name}' to threats_events")
                cursor.execute(sql)

        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Schema repair warning: {e}")


# Start the application
if __name__ == "__main__":
    import uvicorn
    from shared.config import get_settings
    from app import __version__ as app_version
    from tools.wifi_stalker import __version__ as stalker_version
    from tools.threat_watch import __version__ as threat_watch_version
    from tools.network_pulse import __version__ as pulse_version

    # Run migrations FIRST, before any uvicorn/async stuff
    run_migrations()

    settings = get_settings()

    print("=" * 70)
    print("Starting UI Toolkit...")
    print("=" * 70)
    print()
    print(f"Version: {app_version}")
    print(f"Log Level: {settings.log_level}")
    print(f"Database: {settings.database_url}")
    print()

    # Display deployment mode
    deployment_type = settings.deployment_type.upper()
    if deployment_type == "PRODUCTION":
        print(f"Deployment: PRODUCTION (authentication enabled)")
        if settings.domain:
            print(f"Domain: {settings.domain}")
    else:
        print(f"Deployment: LOCAL (authentication disabled)")
    print()

    print("Available tools:")
    print(f"  - Wi-Fi Stalker v{stalker_version}")
    print(f"  - Threat Watch v{threat_watch_version}")
    print(f"  - Network Pulse v{pulse_version}")
    print()

    if deployment_type == "PRODUCTION":
        print("Access via your configured domain with HTTPS")
    else:
        print(f"Access the dashboard at: http://localhost:{settings.app_port}")
        print(f"Wi-Fi Stalker at: http://localhost:{settings.app_port}/stalker/")
        print(f"Threat Watch at: http://localhost:{settings.app_port}/threats/")
        print(f"Network Pulse at: http://localhost:{settings.app_port}/pulse/")
    print()
    print("Press Ctrl+C to stop the server")
    print("=" * 70)
    print()

    # Configure logging level
    log_level = settings.log_level.lower()

    # Start uvicorn server
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.app_port,
        reload=False,  # Set to True for development
        log_level=log_level,
        access_log=True
    )
