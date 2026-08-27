"""
Bank Management System Configuration
Defines application-wide constants, database paths, and styling settings.
"""

import os
from pathlib import Path
from decimal import Decimal

# Base Paths
BASE_DIR = Path(__file__).resolve().parent
DB_FILE = BASE_DIR / "bank_management.db"
LOG_FILE = BASE_DIR / "bank_management.log"
REPORTS_DIR = BASE_DIR / "exported_reports"

# Application Settings
APP_NAME = "BANK MANAGEMENT SYSTEM"
APP_VERSION = "2.0.0"
CURRENCY_SYMBOL = "Rs."

# Security Configuration
PBKDF2_ITERATIONS = 100000
SALT_BYTES = 32
HASH_ALGORITHM = "sha256"

# Banking Rules & Constraints
MIN_INITIAL_DEPOSIT = Decimal("100.00")
MIN_TRANSACTION_AMOUNT = Decimal("1.00")
ACCOUNT_NUMBER_START = 1000000001
TXN_ID_PREFIX = "TXN"

# Customer Statuses
CUSTOMER_STATUS_ACTIVE = "Active"
CUSTOMER_STATUS_BLOCKED = "Blocked"
CUSTOMER_STATUSES = [CUSTOMER_STATUS_ACTIVE, CUSTOMER_STATUS_BLOCKED]

# Account Types
ACCOUNT_TYPE_SAVINGS = "Savings"
ACCOUNT_TYPE_CURRENT = "Current"
ACCOUNT_TYPES = [ACCOUNT_TYPE_SAVINGS, ACCOUNT_TYPE_CURRENT]

# Account Statuses
ACCOUNT_STATUS_ACTIVE = "Active"
ACCOUNT_STATUS_FROZEN = "Frozen"
ACCOUNT_STATUS_CLOSED = "Closed"
ACCOUNT_STATUSES = [ACCOUNT_STATUS_ACTIVE, ACCOUNT_STATUS_FROZEN, ACCOUNT_STATUS_CLOSED]

# Transaction Types
TRANSACTION_TYPE_DEPOSIT = "Deposit"
TRANSACTION_TYPE_WITHDRAWAL = "Withdrawal"
TRANSACTION_TYPE_TRANSFER = "Transfer"
TRANSACTION_TYPE_TRANSFER_RECEIVED = "Transfer Received"
TRANSACTION_TYPES = [
    TRANSACTION_TYPE_DEPOSIT,
    TRANSACTION_TYPE_WITHDRAWAL,
    TRANSACTION_TYPE_TRANSFER,
    TRANSACTION_TYPE_TRANSFER_RECEIVED,
]

# Transaction Statuses
TRANSACTION_STATUS_COMPLETED = "Completed"
TRANSACTION_STATUS_FAILED = "Failed"

# Default Demo Credentials
DEMO_ADMIN_USERNAME = "admin"
DEMO_ADMIN_PASSWORD = "admin123"
DEMO_ADMIN_NAME = "System Administrator"
DEMO_ADMIN_EMAIL = "admin@bankmanagement.com"
