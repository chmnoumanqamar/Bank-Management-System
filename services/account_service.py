"""
Account Management Service.
Handles automatic 10-digit account number generation, account creation, balance checks, freeze/unfreeze, and closure.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, Tuple, List, Dict, Any
from database import DatabaseManager
from models.account import Account
from models.customer import Customer
from utils.logger import log_event
from config import (
    ACCOUNT_NUMBER_START,
    ACCOUNT_TYPES,
    ACCOUNT_STATUS_ACTIVE,
    ACCOUNT_STATUS_FROZEN,
    ACCOUNT_STATUS_CLOSED,
    CUSTOMER_STATUS_ACTIVE,
    TRANSACTION_TYPE_DEPOSIT,
    TRANSACTION_STATUS_COMPLETED,
    MIN_INITIAL_DEPOSIT,
    TXN_ID_PREFIX
)

class AccountService:
    """Provides business logic for bank accounts and lifecycle status."""

    def __init__(self, db: DatabaseManager):
        self.db = db

    def generate_next_account_number(self) -> str:
        """
        Generates the next unique sequential 10-digit account number.
        E.g., 1000000001, 1000000002, etc.
        """
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT MAX(CAST(account_number AS INTEGER)) AS max_acc FROM accounts;")
            row = cursor.fetchone()
            max_acc = row["max_acc"]
            if max_acc is None or max_acc < ACCOUNT_NUMBER_START:
                return str(ACCOUNT_NUMBER_START)
            return str(max_acc + 1)
        finally:
            conn.close()

    def generate_transaction_id(self) -> str:
        """Generates a unique transaction identifier: TXNYYYYMMDDXXXX"""
        now = datetime.now()
        date_str = now.strftime("%Y%m%d")
        prefix = f"{TXN_ID_PREFIX}{date_str}"

        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) as cnt FROM transactions
                WHERE transaction_id LIKE ?;
            """, (f"{prefix}%",))
            row = cursor.fetchone()
            seq = (row["cnt"] if row else 0) + 1
            return f"{prefix}{seq:04d}"
        finally:
            conn.close()

    def create_account(
        self,
        customer_id: int,
        account_type: str,
        initial_deposit: Decimal
    ) -> Tuple[bool, str, Optional[Account]]:
        """
        Creates a new bank account for an active customer with an initial deposit.
        
        Returns:
            Tuple of (success: bool, message: str, account: Optional[Account])
        """
        if account_type not in ACCOUNT_TYPES:
            return False, f"Invalid account type. Allowed types are: {', '.join(ACCOUNT_TYPES)}.", None

        if initial_deposit < MIN_INITIAL_DEPOSIT:
            return False, f"Initial deposit must be at least {MIN_INITIAL_DEPOSIT}.", None

        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            # Verify customer exists and is active
            cursor.execute("SELECT * FROM customers WHERE id = ?;", (customer_id,))
            cust_row = cursor.fetchone()
            if not cust_row:
                return False, f"Customer with ID {customer_id} does not exist.", None

            customer = Customer.from_row(cust_row)
            if not customer.is_active:
                return False, f"Cannot create account: Customer '{customer.full_name}' is currently {customer.status}.", None

            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            account_number = self.generate_next_account_number()
            txn_id = self.generate_transaction_id()
            formatted_deposit = str(initial_deposit.quantize(Decimal("0.01")))

            with self.db.transaction() as tx_cursor:
                # 1. Insert account
                tx_cursor.execute("""
                    INSERT INTO accounts (account_number, customer_id, account_type, balance, status, created_at)
                    VALUES (?, ?, ?, ?, ?, ?);
                """, (
                    account_number,
                    customer_id,
                    account_type,
                    formatted_deposit,
                    ACCOUNT_STATUS_ACTIVE,
                    now
                ))
                new_account_id = tx_cursor.lastrowid

                # 2. Insert initial opening deposit transaction
                tx_cursor.execute("""
                    INSERT INTO transactions (
                        transaction_id, account_id, transaction_type,
                        amount, balance_before, balance_after,
                        description, related_account, transaction_date, status
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """, (
                    txn_id,
                    new_account_id,
                    TRANSACTION_TYPE_DEPOSIT,
                    formatted_deposit,
                    "0.00",
                    formatted_deposit,
                    "Account Opening Initial Deposit",
                    None,
                    now,
                    TRANSACTION_STATUS_COMPLETED
                ))

            created_acc = Account(
                id=new_account_id,
                account_number=account_number,
                customer_id=customer_id,
                account_type=account_type,
                balance=initial_deposit,
                status=ACCOUNT_STATUS_ACTIVE,
                created_at=now
            )

            log_event(
                "ACCOUNT_CREATED",
                f"Created {account_type} account {account_number} for customer ID {customer_id} with initial balance {formatted_deposit}."
            )
            return True, f"Account {account_number} successfully created.", created_acc

        except Exception as ex:
            log_event("ACCOUNT_CREATION_ERROR", f"Error creating account for customer ID {customer_id}: {ex}", level="ERROR")
            return False, f"Failed to create account: {ex}", None
        finally:
            conn.close()

    def get_account_by_number(self, account_number: str) -> Optional[Account]:
        """Retrieves account by 10-digit account number."""
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM accounts WHERE account_number = ?;", (str(account_number).strip(),))
            row = cursor.fetchone()
            return Account.from_row(row) if row else None
        finally:
            conn.close()

    def get_account_by_id(self, account_id: int) -> Optional[Account]:
        """Retrieves account by primary key ID."""
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM accounts WHERE id = ?;", (account_id,))
            row = cursor.fetchone()
            return Account.from_row(row) if row else None
        finally:
            conn.close()

    def get_accounts_by_customer_id(self, customer_id: int, include_closed: bool = True) -> List[Account]:
        """Returns all accounts owned by a specific customer."""
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            if include_closed:
                cursor.execute("SELECT * FROM accounts WHERE customer_id = ? ORDER BY id ASC;", (customer_id,))
            else:
                cursor.execute("""
                    SELECT * FROM accounts
                    WHERE customer_id = ? AND status != ?
                    ORDER BY id ASC;
                """, (customer_id, ACCOUNT_STATUS_CLOSED))
            rows = cursor.fetchall()
            return [Account.from_row(r) for r in rows]
        finally:
            conn.close()

    def get_all_accounts(self, status: Optional[str] = None) -> List[Account]:
        """Returns all accounts in the bank, optionally filtered by status."""
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            if status:
                cursor.execute("SELECT * FROM accounts WHERE status = ? ORDER BY id ASC;", (status,))
            else:
                cursor.execute("SELECT * FROM accounts ORDER BY id ASC;")
            rows = cursor.fetchall()
            return [Account.from_row(r) for r in rows]
        finally:
            conn.close()

    def search_accounts(self, query: str) -> List[Dict[str, Any]]:
        """
        Searches accounts joined with customer details across:
        Account Number, Customer ID, Customer Name, CNIC, Type, and Status.
        """
        clean_query = f"%{query.strip().lower()}%" if query else "%"
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    a.id,
                    a.account_number,
                    a.customer_id,
                    c.full_name as customer_name,
                    c.cnic as customer_cnic,
                    a.account_type,
                    a.balance,
                    a.status,
                    a.created_at,
                    a.closed_at
                FROM accounts a
                JOIN customers c ON a.customer_id = c.id
                WHERE lower(a.account_number) LIKE ?
                   OR cast(a.customer_id as text) LIKE ?
                   OR lower(c.full_name) LIKE ?
                   OR lower(c.cnic) LIKE ?
                   OR lower(a.account_type) LIKE ?
                   OR lower(a.status) LIKE ?
                ORDER BY a.id ASC;
            """, (clean_query, clean_query, clean_query, clean_query, clean_query, clean_query))
            rows = cursor.fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def freeze_account(self, account_number: str) -> Tuple[bool, str]:
        """Freezes an active account."""
        account = self.get_account_by_number(account_number)
        if not account:
            return False, f"Account '{account_number}' not found."

        if account.is_closed:
            return False, f"Cannot freeze account '{account_number}': Account is permanently Closed."

        if account.is_frozen:
            return False, f"Account '{account_number}' is already Frozen."

        try:
            with self.db.transaction() as tx_cursor:
                tx_cursor.execute("UPDATE accounts SET status = ? WHERE account_number = ?;", (ACCOUNT_STATUS_FROZEN, account_number))

            log_event("ACCOUNT_FROZEN", f"Account {account_number} has been Frozen.")
            return True, f"Account {account_number} successfully frozen."
        except Exception as ex:
            log_event("ACCOUNT_FREEZE_ERROR", f"Error freezing account {account_number}: {ex}", level="ERROR")
            return False, f"Failed to freeze account: {ex}"

    def unfreeze_account(self, account_number: str) -> Tuple[bool, str]:
        """Unfreezes a frozen account and returns it to Active state."""
        account = self.get_account_by_number(account_number)
        if not account:
            return False, f"Account '{account_number}' not found."

        if account.is_closed:
            return False, f"Cannot unfreeze account '{account_number}': Account is permanently Closed."

        if account.is_active:
            return False, f"Account '{account_number}' is already Active."

        try:
            with self.db.transaction() as tx_cursor:
                tx_cursor.execute("UPDATE accounts SET status = ? WHERE account_number = ?;", (ACCOUNT_STATUS_ACTIVE, account_number))

            log_event("ACCOUNT_UNFROZEN", f"Account {account_number} has been Unfrozen/Activated.")
            return True, f"Account {account_number} successfully activated."
        except Exception as ex:
            log_event("ACCOUNT_UNFREEZE_ERROR", f"Error unfreezing account {account_number}: {ex}", level="ERROR")
            return False, f"Failed to activate account: {ex}"

    def close_account(self, account_number: str) -> Tuple[bool, str]:
        """
        Closes an account.
        Rule: Account must exist, not already closed, and balance MUST be exactly zero.
        """
        account = self.get_account_by_number(account_number)
        if not account:
            return False, f"Account '{account_number}' not found."

        if account.is_closed:
            return False, f"Account '{account_number}' is already Closed."

        if account.balance > Decimal("0.00"):
            return False, (
                f"Account cannot be closed.\n"
                f"Remaining Balance: Rs. {account.balance:,.2f}\n"
                f"Please settle/withdraw the remaining balance first before closing."
            )

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            with self.db.transaction() as tx_cursor:
                tx_cursor.execute("""
                    UPDATE accounts
                    SET status = ?, closed_at = ?
                    WHERE account_number = ?;
                """, (ACCOUNT_STATUS_CLOSED, now, account_number))

            log_event("ACCOUNT_CLOSED", f"Account {account_number} has been Closed.")
            return True, f"Account {account_number} has been successfully closed."
        except Exception as ex:
            log_event("ACCOUNT_CLOSE_ERROR", f"Error closing account {account_number}: {ex}", level="ERROR")
            return False, f"Failed to close account: {ex}"
