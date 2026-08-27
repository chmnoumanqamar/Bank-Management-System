"""
Bank Management System - Application Entry Point.
Initializes the database, loads audit logging, seeds demo data, and starts the CLI loop.
"""

import sys
import os

# Ensure project root is in python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import DatabaseManager
from cli.main_menu import MainMenu
from utils.logger import log_event, get_logger

def main():
    """Application bootstrap function."""
    try:
        # 1. Initialize Logger
        logger = get_logger()
        log_event("SYSTEM_STARTUP", "Bank Management System initialized.")

        # 2. Initialize Database & Seed Demo Data
        db_manager = DatabaseManager()
        db_manager.seed_demo_data()

        # 3. Launch Main CLI
        app = MainMenu(db_manager)
        app.run()

    except KeyboardInterrupt:
        print("\n\nApplication closed safely.\nGoodbye!\n")
        sys.exit(0)
    except Exception as ex:
        log_event("SYSTEM_CRASH", f"Unexpected application error: {ex}", level="CRITICAL")
        print(f"\n[!] A fatal system error occurred: {ex}")
        sys.exit(1)

if __name__ == "__main__":
    main()
