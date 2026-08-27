"""
Reports Generation and CSV Export Module.
Calculates real-time financial metrics, summary reports, and exports audit data to CSV.
"""

import csv
import os
from decimal import Decimal
from typing import Dict, Any, List, Optional
from database import DatabaseManager
from config import (
    BASE_DIR,
    CUSTOMER_STATUS_ACTIVE,
    CUSTOMER_STATUS_BLOCKED,
    ACCOUNT_STATUS_ACTIVE,
    ACCOUNT_STATUS_FROZEN,
    ACCOUNT_STATUS_CLOSED,
    ACCOUNT_TYPE_SAVINGS,
    ACCOUNT_TYPE_CURRENT,
    TRANSACTION_TYPE_DEPOSIT,
    TRANSACTION_TYPE_WITHDRAWAL,
    TRANSACTION_TYPE_TRANSFER,
    TRANSACTION_TYPE_TRANSFER_RECEIVED,
    TRANSACTION_STATUS_COMPLETED
)
from utils.logger import log_event

class ReportGenerator:
    """Generates bank-wide business analytics and exports CSV documents."""

    def __init__(self, db: DatabaseManager):
        self.db = db

    def get_dashboard_statistics(self) -> Dict[str, Any]:
        """
        Calculates dynamic real-time dashboard figures from database tables.
        """
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()

            # 1. Customer statistics
            cursor.execute("SELECT COUNT(*) as total FROM customers;")
            total_customers = cursor.fetchone()["total"]

            cursor.execute("SELECT COUNT(*) as active FROM customers WHERE status = ?;", (CUSTOMER_STATUS_ACTIVE,))
            active_customers = cursor.fetchone()["active"]

            cursor.execute("SELECT COUNT(*) as blocked FROM customers WHERE status = ?;", (CUSTOMER_STATUS_BLOCKED,))
            blocked_customers = cursor.fetchone()["blocked"]

            # 2. Account statistics
            cursor.execute("SELECT COUNT(*) as total FROM accounts;")
            total_accounts = cursor.fetchone()["total"]

            cursor.execute("SELECT COUNT(*) as active FROM accounts WHERE status = ?;", (ACCOUNT_STATUS_ACTIVE,))
            active_accounts = cursor.fetchone()["active"]

            cursor.execute("SELECT COUNT(*) as frozen FROM accounts WHERE status = ?;", (ACCOUNT_STATUS_FROZEN,))
            frozen_accounts = cursor.fetchone()["frozen"]

            cursor.execute("SELECT COUNT(*) as closed FROM accounts WHERE status = ?;", (ACCOUNT_STATUS_CLOSED,))
            closed_accounts = cursor.fetchone()["closed"]

            cursor.execute("SELECT COUNT(*) as savings FROM accounts WHERE account_type = ?;", (ACCOUNT_TYPE_SAVINGS,))
            savings_accounts = cursor.fetchone()["savings"]

            cursor.execute("SELECT COUNT(*) as current FROM accounts WHERE account_type = ?;", (ACCOUNT_TYPE_CURRENT,))
            current_accounts = cursor.fetchone()["current"]

            # 3. Financial calculations using exact Decimal summation
            cursor.execute("SELECT balance FROM accounts WHERE status != ?;", (ACCOUNT_STATUS_CLOSED,))
            balances = cursor.fetchall()
            total_bank_balance = sum((Decimal(str(r["balance"])) for r in balances), Decimal("0.00"))

            # Total Deposits
            cursor.execute("""
                SELECT amount FROM transactions
                WHERE transaction_type = ? AND status = ?;
            """, (TRANSACTION_TYPE_DEPOSIT, TRANSACTION_STATUS_COMPLETED))
            deposit_rows = cursor.fetchall()
            total_deposits = sum((Decimal(str(r["amount"])) for r in deposit_rows), Decimal("0.00"))

            # Total Withdrawals
            cursor.execute("""
                SELECT amount FROM transactions
                WHERE transaction_type = ? AND status = ?;
            """, (TRANSACTION_TYPE_WITHDRAWAL, TRANSACTION_STATUS_COMPLETED))
            withdrawal_rows = cursor.fetchall()
            total_withdrawals = sum((Decimal(str(r["amount"])) for r in withdrawal_rows), Decimal("0.00"))

            # Total Transfers
            cursor.execute("""
                SELECT amount FROM transactions
                WHERE transaction_type = ? AND status = ?;
            """, (TRANSACTION_TYPE_TRANSFER, TRANSACTION_STATUS_COMPLETED))
            transfer_rows = cursor.fetchall()
            total_transfers = sum((Decimal(str(r["amount"])) for r in transfer_rows), Decimal("0.00"))

            # Total Transactions Count
            cursor.execute("SELECT COUNT(*) as total FROM transactions;")
            total_transactions = cursor.fetchone()["total"]

            return {
                "total_customers": total_customers,
                "active_customers": active_customers,
                "blocked_customers": blocked_customers,
                "total_accounts": total_accounts,
                "active_accounts": active_accounts,
                "frozen_accounts": frozen_accounts,
                "closed_accounts": closed_accounts,
                "savings_accounts": savings_accounts,
                "current_accounts": current_accounts,
                "total_bank_balance": total_bank_balance,
                "total_deposits": total_deposits,
                "total_withdrawals": total_withdrawals,
                "total_transfers": total_transfers,
                "total_transactions": total_transactions
            }
        finally:
            conn.close()

    def export_customers_csv(self, filename: str = "customers_report.csv") -> str:
        """
        Exports all customer records to a CSV file.
        Returns the absolute filepath of the generated CSV.
        """
        filepath = os.path.join(BASE_DIR, filename)
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, full_name, cnic, phone, email, address, date_of_birth, username, status, created_at
                FROM customers
                ORDER BY id ASC;
            """)
            rows = cursor.fetchall()

            with open(filepath, mode="w", newline="", encoding="utf-8") as csvfile:
                fieldnames = [
                    "Customer ID", "Full Name", "CNIC", "Phone", "Email",
                    "Address", "Date of Birth", "Username", "Status", "Registered Date"
                ]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()

                for row in rows:
                    writer.writerow({
                        "Customer ID": row["id"],
                        "Full Name": row["full_name"],
                        "CNIC": row["cnic"],
                        "Phone": row["phone"],
                        "Email": row["email"],
                        "Address": row["address"],
                        "Date of Birth": row["date_of_birth"],
                        "Username": row["username"],
                        "Status": row["status"],
                        "Registered Date": row["created_at"]
                    })

            log_event("CSV_EXPORT", f"Customer report exported to {filepath}")
            return filepath
        finally:
            conn.close()

    def export_accounts_csv(self, filename: str = "accounts_report.csv") -> str:
        """
        Exports all account records joined with customer details to a CSV file.
        Returns the absolute filepath of the generated CSV.
        """
        filepath = os.path.join(BASE_DIR, filename)
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
                ORDER BY a.id ASC;
            """)
            rows = cursor.fetchall()

            with open(filepath, mode="w", newline="", encoding="utf-8") as csvfile:
                fieldnames = [
                    "Account ID", "Account Number", "Customer ID", "Customer Name",
                    "Customer CNIC", "Account Type", "Balance (PKR)", "Status",
                    "Created At", "Closed At"
                ]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()

                for row in rows:
                    writer.writerow({
                        "Account ID": row["id"],
                        "Account Number": row["account_number"],
                        "Customer ID": row["customer_id"],
                        "Customer Name": row["customer_name"],
                        "Customer CNIC": row["customer_cnic"],
                        "Account Type": row["account_type"],
                        "Balance (PKR)": f"{Decimal(str(row['balance'])):.2f}",
                        "Status": row["status"],
                        "Created At": row["created_at"],
                        "Closed At": row["closed_at"] or "N/A"
                    })

            log_event("CSV_EXPORT", f"Accounts report exported to {filepath}")
            return filepath
        finally:
            conn.close()

    def export_transactions_csv(self, filename: str = "transactions_report.csv") -> str:
        """
        Exports all transactions to a CSV file.
        Returns the absolute filepath of the generated CSV.
        """
        filepath = os.path.join(BASE_DIR, filename)
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
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
                ORDER BY t.id DESC;
            """)
            rows = cursor.fetchall()

            with open(filepath, mode="w", newline="", encoding="utf-8") as csvfile:
                fieldnames = [
                    "ID", "Transaction ID", "Account Number", "Customer Name",
                    "Type", "Amount (PKR)", "Balance Before", "Balance After",
                    "Description", "Related Account", "Date & Time", "Status"
                ]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()

                for row in rows:
                    writer.writerow({
                        "ID": row["id"],
                        "Transaction ID": row["transaction_id"],
                        "Account Number": row["account_number"],
                        "Customer Name": row["customer_name"],
                        "Type": row["transaction_type"],
                        "Amount (PKR)": f"{Decimal(str(row['amount'])):.2f}",
                        "Balance Before": f"{Decimal(str(row['balance_before'])):.2f}",
                        "Balance After": f"{Decimal(str(row['balance_after'])):.2f}",
                        "Description": row["description"] or "",
                        "Related Account": row["related_account"] or "N/A",
                        "Date & Time": row["transaction_date"],
                        "Status": row["status"]
                    })

            log_event("CSV_EXPORT", f"Transactions report exported to {filepath}")
            return filepath
        finally:
            conn.close()
