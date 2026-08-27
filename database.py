"""
Database Management Module.
Handles SQLite connection lifecycle, PRAGMA foreign keys, schema initialization, and transactional safety.
"""

import sqlite3
from contextlib import contextmanager
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Generator, Optional, Union

from config import (
    DB_FILE,
    DEMO_ADMIN_USERNAME,
    DEMO_ADMIN_PASSWORD,
    DEMO_ADMIN_NAME,
    DEMO_ADMIN_EMAIL,
    CUSTOMER_STATUS_ACTIVE,
    ACCOUNT_TYPE_SAVINGS,
    ACCOUNT_TYPE_CURRENT,
    ACCOUNT_STATUS_ACTIVE,
    TRANSACTION_TYPE_DEPOSIT,
    TRANSACTION_STATUS_COMPLETED
)
from utils.logger import log_event
from utils.security import hash_password

class DatabaseManager:
    """Manages SQLite connections, schema initialization, and transactional execution."""

    def __init__(self, db_path: Optional[Union[str, Path]] = None):
        self.db_path = str(db_path) if db_path else str(DB_FILE)
        self.initialize_schema()

    def get_connection(self) -> sqlite3.Connection:
        """Returns a new SQLite connection with foreign keys enabled and row factory configured."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    @contextmanager
    def transaction(self) -> Generator[sqlite3.Cursor, None, None]:
        """
        Transactional context manager.
        Commits changes upon successful block completion, rolls back completely on any exception.
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            yield cursor
            conn.commit()
        except Exception as ex:
            conn.rollback()
            log_event("DATABASE_TRANSACTION_ROLLBACK", f"Transaction rolled back due to: {ex}", level="ERROR")
            raise
        finally:
            conn.close()

    def initialize_schema(self):
        """Creates the required database tables if they do not exist."""
        with self.transaction() as cursor:
            # 1. Admins Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS admins (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    salt TEXT NOT NULL,
                    full_name TEXT NOT NULL,
                    email TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
            """)

            # 2. Customers Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS customers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    full_name TEXT NOT NULL,
                    cnic TEXT UNIQUE NOT NULL,
                    phone TEXT NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    address TEXT NOT NULL,
                    date_of_birth TEXT NOT NULL,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    salt TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'Active',
                    created_at TEXT NOT NULL
                );
            """)

            # 3. Accounts Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS accounts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    account_number TEXT UNIQUE NOT NULL,
                    customer_id INTEGER NOT NULL REFERENCES customers(id) ON DELETE RESTRICT,
                    account_type TEXT NOT NULL,
                    balance TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'Active',
                    created_at TEXT NOT NULL,
                    closed_at TEXT
                );
            """)

            # 4. Transactions Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    transaction_id TEXT UNIQUE NOT NULL,
                    account_id INTEGER NOT NULL REFERENCES accounts(id) ON DELETE RESTRICT,
                    transaction_type TEXT NOT NULL,
                    amount TEXT NOT NULL,
                    balance_before TEXT NOT NULL,
                    balance_after TEXT NOT NULL,
                    description TEXT,
                    related_account TEXT,
                    transaction_date TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'Completed'
                );
            """)

            # Indexes for faster queries
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_customers_cnic ON customers(cnic);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_customers_username ON customers(username);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_accounts_number ON accounts(account_number);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_accounts_customer_id ON accounts(customer_id);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_transactions_txn_id ON transactions(transaction_id);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_transactions_acc_id ON transactions(account_id);")

        log_event("DATABASE_INITIALIZED", f"Database schema verified at {self.db_path}")

    def seed_demo_data(self):
        """Seeds initial admin and sample customer accounts if database is fresh."""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with self.transaction() as cursor:
            # Check if admin already exists
            cursor.execute("SELECT COUNT(*) as count FROM admins WHERE username = ?", (DEMO_ADMIN_USERNAME,))
            if cursor.fetchone()["count"] == 0:
                pwd_hash, salt = hash_password(DEMO_ADMIN_PASSWORD)
                cursor.execute("""
                    INSERT INTO admins (username, password_hash, salt, full_name, email, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (DEMO_ADMIN_USERNAME, pwd_hash, salt, DEMO_ADMIN_NAME, DEMO_ADMIN_EMAIL, now))
                log_event("DEMO_DATA", f"Default admin '{DEMO_ADMIN_USERNAME}' created.")

            # Check if customers exist
            cursor.execute("SELECT COUNT(*) as count FROM customers;")
            if cursor.fetchone()["count"] == 0:
                # Customer 1: Muhammad Ali
                c1_hash, c1_salt = hash_password("customer123")
                cursor.execute("""
                    INSERT INTO customers (full_name, cnic, phone, email, address, date_of_birth, username, password_hash, salt, status, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    "Muhammad Ali",
                    "42101-1234567-1",
                    "03001234567",
                    "muhammad.ali@example.com",
                    "House 12, Street 4, F-7/2, Islamabad",
                    "1994-05-14",
                    "m_ali",
                    c1_hash,
                    c1_salt,
                    CUSTOMER_STATUS_ACTIVE,
                    now
                ))
                c1_id = cursor.lastrowid

                # Account 1 for Muhammad Ali
                cursor.execute("""
                    INSERT INTO accounts (account_number, customer_id, account_type, balance, status, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, ("1000000001", c1_id, ACCOUNT_TYPE_SAVINGS, "50000.00", ACCOUNT_STATUS_ACTIVE, now))
                acc1_id = cursor.lastrowid

                # Initial deposit transaction for Account 1
                cursor.execute("""
                    INSERT INTO transactions (transaction_id, account_id, transaction_type, amount, balance_before, balance_after, description, related_account, transaction_date, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    "TXN202608270001",
                    acc1_id,
                    TRANSACTION_TYPE_DEPOSIT,
                    "50000.00",
                    "0.00",
                    "50000.00",
                    "Initial Account Opening Deposit",
                    None,
                    now,
                    TRANSACTION_STATUS_COMPLETED
                ))

                # Customer 2: Fatima Zahra
                c2_hash, c2_salt = hash_password("customer123")
                cursor.execute("""
                    INSERT INTO customers (full_name, cnic, phone, email, address, date_of_birth, username, password_hash, salt, status, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    "Fatima Zahra",
                    "35202-9876543-2",
                    "03219876543",
                    "fatima.z@example.com",
                    "Flat 304, Gulberg Heights, Lahore",
                    "1998-11-20",
                    "f_zahra",
                    c2_hash,
                    c2_salt,
                    CUSTOMER_STATUS_ACTIVE,
                    now
                ))
                c2_id = cursor.lastrowid

                # Account 2 for Fatima Zahra
                cursor.execute("""
                    INSERT INTO accounts (account_number, customer_id, account_type, balance, status, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, ("1000000002", c2_id, ACCOUNT_TYPE_CURRENT, "75000.00", ACCOUNT_STATUS_ACTIVE, now))
                acc2_id = cursor.lastrowid

                # Initial deposit transaction for Account 2
                cursor.execute("""
                    INSERT INTO transactions (transaction_id, account_id, transaction_type, amount, balance_before, balance_after, description, related_account, transaction_date, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    "TXN202608270002",
                    acc2_id,
                    TRANSACTION_TYPE_DEPOSIT,
                    "75000.00",
                    "0.00",
                    "75000.00",
                    "Initial Account Opening Deposit",
                    None,
                    now,
                    TRANSACTION_STATUS_COMPLETED
                ))

                log_event("DEMO_DATA", "Sample customers and accounts seeded successfully.")
