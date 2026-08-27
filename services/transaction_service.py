"""
Transaction Management Service.
Handles Deposits, Withdrawals, Atomic Transfers with rollback guarantees, and Transaction History queries.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, Tuple, List, Dict, Any
from database import DatabaseManager
from models.account import Account
from models.transaction import Transaction
from utils.logger import log_event
from config import (
    ACCOUNT_STATUS_ACTIVE,
    TRANSACTION_TYPE_DEPOSIT,
    TRANSACTION_TYPE_WITHDRAWAL,
    TRANSACTION_TYPE_TRANSFER,
    TRANSACTION_TYPE_TRANSFER_RECEIVED,
    TRANSACTION_STATUS_COMPLETED,
    TRANSACTION_STATUS_FAILED,
    MIN_TRANSACTION_AMOUNT,
    TXN_ID_PREFIX
)

class TransactionService:
    """Provides atomic financial operations and audit log queries."""

    def __init__(self, db: DatabaseManager):
        self.db = db

    def generate_transaction_id(self, offset: int = 0) -> str:
        """
        Generates a unique transaction identifier with format: TXNYYYYMMDDXXXX
        Accepts an optional offset for multi-transaction operations in the same tick.
        """
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
            seq = (row["cnt"] if row else 0) + 1 + offset
            return f"{prefix}{seq:04d}"
        finally:
            conn.close()

    def deposit(
        self,
        account_number: str,
        amount: Decimal,
        description: Optional[str] = None
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Executes an atomic deposit to an active bank account.
        
        Returns:
            Tuple of (success: bool, message: str, txn_data: Optional[dict])
        """
        if amount < MIN_TRANSACTION_AMOUNT:
            return False, f"Deposit amount must be at least {MIN_TRANSACTION_AMOUNT}.", None

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        txn_id = self.generate_transaction_id()
        desc = description.strip() if description else "Cash Deposit"

        try:
            with self.db.transaction() as cursor:
                # 1. Fetch latest account state inside transaction
                cursor.execute("""
                    SELECT id, account_number, balance, status
                    FROM accounts
                    WHERE account_number = ?;
                """, (account_number,))
                acc_row = cursor.fetchone()

                if not acc_row:
                    return False, f"Account '{account_number}' not found.", None

                if acc_row["status"] != ACCOUNT_STATUS_ACTIVE:
                    return False, f"Cannot deposit: Account '{account_number}' is {acc_row['status']}.", None

                account_id = acc_row["id"]
                balance_before = Decimal(str(acc_row["balance"]))
                balance_after = (balance_before + amount).quantize(Decimal("0.01"))

                # 2. Update account balance
                cursor.execute("""
                    UPDATE accounts
                    SET balance = ?
                    WHERE id = ?;
                """, (str(balance_after), account_id))

                # 3. Insert transaction log
                cursor.execute("""
                    INSERT INTO transactions (
                        transaction_id, account_id, transaction_type,
                        amount, balance_before, balance_after,
                        description, related_account, transaction_date, status
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """, (
                    txn_id,
                    account_id,
                    TRANSACTION_TYPE_DEPOSIT,
                    str(amount.quantize(Decimal("0.01"))),
                    str(balance_before),
                    str(balance_after),
                    desc,
                    None,
                    now,
                    TRANSACTION_STATUS_COMPLETED
                ))

            log_event(
                "DEPOSIT_COMPLETED",
                f"Deposit of Rs. {amount:,.2f} to Account {account_number}. TXN ID: {txn_id}. New Balance: Rs. {balance_after:,.2f}"
            )
            return True, "Deposit successful.", {
                "transaction_id": txn_id,
                "account_number": account_number,
                "amount": amount,
                "balance_before": balance_before,
                "balance_after": balance_after,
                "date": now
            }

        except Exception as ex:
            log_event("DEPOSIT_FAILED", f"Deposit error on Account {account_number}: {ex}", level="ERROR")
            return False, f"Deposit failed: {ex}", None

    def withdraw(
        self,
        account_number: str,
        amount: Decimal,
        description: Optional[str] = None
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Executes an atomic withdrawal from an active bank account.
        Verifies sufficient funds before deduction.
        
        Returns:
            Tuple of (success: bool, message: str, txn_data: Optional[dict])
        """
        if amount < MIN_TRANSACTION_AMOUNT:
            return False, f"Withdrawal amount must be at least {MIN_TRANSACTION_AMOUNT}.", None

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        txn_id = self.generate_transaction_id()
        desc = description.strip() if description else "Cash Withdrawal"

        try:
            with self.db.transaction() as cursor:
                # 1. Fetch latest account state inside transaction
                cursor.execute("""
                    SELECT id, account_number, balance, status
                    FROM accounts
                    WHERE account_number = ?;
                """, (account_number,))
                acc_row = cursor.fetchone()

                if not acc_row:
                    return False, f"Account '{account_number}' not found.", None

                if acc_row["status"] != ACCOUNT_STATUS_ACTIVE:
                    return False, f"Cannot withdraw: Account '{account_number}' is {acc_row['status']}.", None

                account_id = acc_row["id"]
                balance_before = Decimal(str(acc_row["balance"]))

                if balance_before < amount:
                    return False, f"Transaction failed.\nInsufficient balance.\nCurrent Balance: Rs. {balance_before:,.2f}\nRequested: Rs. {amount:,.2f}", None

                balance_after = (balance_before - amount).quantize(Decimal("0.01"))

                # 2. Update account balance
                cursor.execute("""
                    UPDATE accounts
                    SET balance = ?
                    WHERE id = ?;
                """, (str(balance_after), account_id))

                # 3. Insert transaction log
                cursor.execute("""
                    INSERT INTO transactions (
                        transaction_id, account_id, transaction_type,
                        amount, balance_before, balance_after,
                        description, related_account, transaction_date, status
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """, (
                    txn_id,
                    account_id,
                    TRANSACTION_TYPE_WITHDRAWAL,
                    str(amount.quantize(Decimal("0.01"))),
                    str(balance_before),
                    str(balance_after),
                    desc,
                    None,
                    now,
                    TRANSACTION_STATUS_COMPLETED
                ))

            log_event(
                "WITHDRAWAL_COMPLETED",
                f"Withdrawal of Rs. {amount:,.2f} from Account {account_number}. TXN ID: {txn_id}. Remaining Balance: Rs. {balance_after:,.2f}"
            )
            return True, "Withdrawal successful.", {
                "transaction_id": txn_id,
                "account_number": account_number,
                "amount": amount,
                "balance_before": balance_before,
                "balance_after": balance_after,
                "date": now
            }

        except Exception as ex:
            log_event("WITHDRAWAL_FAILED", f"Withdrawal error on Account {account_number}: {ex}", level="ERROR")
            return False, f"Withdrawal failed: {ex}", None

    def transfer(
        self,
        source_account_number: str,
        destination_account_number: str,
        amount: Decimal,
        description: Optional[str] = None
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Executes an atomic funds transfer between two accounts.
        Guarantees complete rollback if any step encounters an error.
        
        Returns:
            Tuple of (success: bool, message: str, transfer_data: Optional[dict])
        """
        src_num = str(source_account_number).strip()
        dst_num = str(destination_account_number).strip()

        if src_num == dst_num:
            return False, "Source and destination accounts cannot be the same.", None

        if amount < MIN_TRANSACTION_AMOUNT:
            return False, f"Transfer amount must be at least {MIN_TRANSACTION_AMOUNT}.", None

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sender_txn_id = self.generate_transaction_id(offset=0)
        receiver_txn_id = self.generate_transaction_id(offset=1)
        transfer_desc = description.strip() if description else "Account Transfer"

        try:
            with self.db.transaction() as cursor:
                # 1. Fetch Source Account
                cursor.execute("""
                    SELECT id, account_number, balance, status
                    FROM accounts
                    WHERE account_number = ?;
                """, (src_num,))
                src_row = cursor.fetchone()

                if not src_row:
                    return False, f"Source account '{src_num}' does not exist.", None

                if src_row["status"] != ACCOUNT_STATUS_ACTIVE:
                    return False, f"Cannot transfer: Source account '{src_num}' is {src_row['status']}.", None

                src_id = src_row["id"]
                src_bal_before = Decimal(str(src_row["balance"]))

                if src_bal_before < amount:
                    return False, f"Transfer failed.\nInsufficient balance in source account.\nCurrent Balance: Rs. {src_bal_before:,.2f}\nRequested: Rs. {amount:,.2f}", None

                # 2. Fetch Destination Account
                cursor.execute("""
                    SELECT id, account_number, balance, status
                    FROM accounts
                    WHERE account_number = ?;
                """, (dst_num,))
                dst_row = cursor.fetchone()

                if not dst_row:
                    return False, f"Destination account '{dst_num}' does not exist.", None

                if dst_row["status"] != ACCOUNT_STATUS_ACTIVE:
                    return False, f"Cannot transfer: Destination account '{dst_num}' is {dst_row['status']}.", None

                dst_id = dst_row["id"]
                dst_bal_before = Decimal(str(dst_row["balance"]))

                # 3. Calculate new balances
                src_bal_after = (src_bal_before - amount).quantize(Decimal("0.01"))
                dst_bal_after = (dst_bal_before + amount).quantize(Decimal("0.01"))

                # 4. Deduct from Sender
                cursor.execute("""
                    UPDATE accounts
                    SET balance = ?
                    WHERE id = ?;
                """, (str(src_bal_after), src_id))

                # 5. Add to Receiver
                cursor.execute("""
                    UPDATE accounts
                    SET balance = ?
                    WHERE id = ?;
                """, (str(dst_bal_after), dst_id))

                # 6. Insert Sender Transaction Log
                cursor.execute("""
                    INSERT INTO transactions (
                        transaction_id, account_id, transaction_type,
                        amount, balance_before, balance_after,
                        description, related_account, transaction_date, status
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """, (
                    sender_txn_id,
                    src_id,
                    TRANSACTION_TYPE_TRANSFER,
                    str(amount.quantize(Decimal("0.01"))),
                    str(src_bal_before),
                    str(src_bal_after),
                    transfer_desc,
                    dst_num,
                    now,
                    TRANSACTION_STATUS_COMPLETED
                ))

                # 7. Insert Receiver Transaction Log
                cursor.execute("""
                    INSERT INTO transactions (
                        transaction_id, account_id, transaction_type,
                        amount, balance_before, balance_after,
                        description, related_account, transaction_date, status
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """, (
                    receiver_txn_id,
                    dst_id,
                    TRANSACTION_TYPE_TRANSFER_RECEIVED,
                    str(amount.quantize(Decimal("0.01"))),
                    str(dst_bal_before),
                    str(dst_bal_after),
                    transfer_desc,
                    src_num,
                    now,
                    TRANSACTION_STATUS_COMPLETED
                ))

            log_event(
                "TRANSFER_COMPLETED",
                f"Transfer Rs. {amount:,.2f} from {src_num} to {dst_num}. Sender TXN: {sender_txn_id}, Receiver TXN: {receiver_txn_id}"
            )
            return True, "Transfer completed successfully.", {
                "sender_txn_id": sender_txn_id,
                "receiver_txn_id": receiver_txn_id,
                "source_account": src_num,
                "destination_account": dst_num,
                "amount": amount,
                "new_source_balance": src_bal_after,
                "date": now
            }

        except Exception as ex:
            log_event("TRANSFER_FAILED", f"Transfer failed between {src_num} and {dst_num}: {ex}", level="ERROR")
            return False, f"Transfer failed and changes were rolled back: {ex}", None

    def get_transactions_for_account(
        self,
        account_id: int,
        txn_type: Optional[str] = None,
        search_txn_id: Optional[str] = None
    ) -> List[Transaction]:
        """Returns transaction history for a specific account with optional type or ID filters."""
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            params: List[Any] = [account_id]
            sql = "SELECT * FROM transactions WHERE account_id = ?"

            if txn_type:
                sql += " AND transaction_type = ?"
                params.append(txn_type)

            if search_txn_id:
                sql += " AND lower(transaction_id) LIKE ?"
                params.append(f"%{search_txn_id.strip().lower()}%")

            sql += " ORDER BY id DESC;"
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            return [Transaction.from_row(r) for r in rows]
        finally:
            conn.close()

    def get_all_transactions(
        self,
        query: Optional[str] = None,
        txn_type: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Bank-wide transaction history for admin inquiries with joins on account and customer tables.
        """
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            sql = """
                SELECT 
                    t.id,
                    t.transaction_id,
                    a.account_number,
                    c.full_name as customer_name,
                    t.transaction_type,
                    t.amount,
                    t.balance_before,
                    t.balance_after,
                    t.description,
                    t.related_account,
                    t.transaction_date,
                    t.status
                FROM transactions t
                JOIN accounts a ON t.account_id = a.id
                JOIN customers c ON a.customer_id = c.id
                WHERE 1=1
            """
            params: List[Any] = []

            if txn_type:
                sql += " AND t.transaction_type = ?"
                params.append(txn_type)

            if status:
                sql += " AND t.status = ?"
                params.append(status)

            if query:
                clean_q = f"%{query.strip().lower()}%"
                sql += """
                    AND (
                        lower(t.transaction_id) LIKE ?
                        OR lower(a.account_number) LIKE ?
                        OR lower(c.full_name) LIKE ?
                        OR lower(t.description) LIKE ?
                        OR lower(coalesce(t.related_account, '')) LIKE ?
                    )
                """
                params.extend([clean_q, clean_q, clean_q, clean_q, clean_q])

            sql += " ORDER BY t.id DESC;"
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()
