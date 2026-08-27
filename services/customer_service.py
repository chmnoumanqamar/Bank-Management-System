"""
Customer Management Service.
Provides registration, lookup, search, profile updates, blocking/unblocking, and deletion.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, Tuple, List, Dict, Any
from database import DatabaseManager
from models.customer import Customer
from utils.security import hash_password
from utils.logger import log_event
from config import (
    CUSTOMER_STATUS_ACTIVE,
    CUSTOMER_STATUS_BLOCKED,
    ACCOUNT_STATUS_ACTIVE,
    ACCOUNT_STATUS_FROZEN
)

class CustomerService:
    """Handles customer records, searches, status transitions, and profile modifications."""

    def __init__(self, db: DatabaseManager):
        self.db = db

    def register_customer(
        self,
        full_name: str,
        cnic: str,
        phone: str,
        email: str,
        address: str,
        date_of_birth: str,
        username: str,
        password: str
    ) -> Tuple[bool, str, Optional[int]]:
        """
        Registers a new customer in the system.
        
        Returns:
            Tuple of (success: bool, message: str, new_customer_id: Optional[int])
        """
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        clean_username = username.strip().lower()
        clean_cnic = cnic.strip()
        clean_email = email.strip().lower()

        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()

            # Check uniqueness of CNIC
            cursor.execute("SELECT id FROM customers WHERE cnic = ?;", (clean_cnic,))
            if cursor.fetchone():
                return False, f"A customer with CNIC '{clean_cnic}' is already registered.", None

            # Check uniqueness of Username
            cursor.execute("SELECT id FROM customers WHERE lower(username) = ?;", (clean_username,))
            if cursor.fetchone():
                return False, f"Username '{clean_username}' is already taken. Please choose another.", None

            # Check uniqueness of Email
            cursor.execute("SELECT id FROM customers WHERE lower(email) = ?;", (clean_email,))
            if cursor.fetchone():
                return False, f"Email address '{clean_email}' is already in use.", None

            # Hash password
            pwd_hash, salt = hash_password(password)

            with self.db.transaction() as tx_cursor:
                tx_cursor.execute("""
                    INSERT INTO customers (
                        full_name, cnic, phone, email, address,
                        date_of_birth, username, password_hash, salt,
                        status, created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """, (
                    full_name.strip(),
                    clean_cnic,
                    phone.strip(),
                    clean_email,
                    address.strip(),
                    date_of_birth.strip(),
                    clean_username,
                    pwd_hash,
                    salt,
                    CUSTOMER_STATUS_ACTIVE,
                    now
                ))
                new_id = tx_cursor.lastrowid

            log_event("CUSTOMER_REGISTERED", f"Customer '{full_name}' (ID: {new_id}, User: {clean_username}) registered successfully.")
            return True, "Customer registered successfully.", new_id

        except Exception as ex:
            log_event("CUSTOMER_REGISTRATION_ERROR", f"Error registering customer: {ex}", level="ERROR")
            return False, f"Registration failed due to a system error: {ex}", None
        finally:
            conn.close()

    def get_customer_by_id(self, customer_id: int) -> Optional[Customer]:
        """Retrieves a customer by primary key ID."""
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM customers WHERE id = ?;", (customer_id,))
            row = cursor.fetchone()
            return Customer.from_row(row) if row else None
        finally:
            conn.close()

    def get_customer_by_username(self, username: str) -> Optional[Customer]:
        """Retrieves a customer by username (case-insensitive)."""
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM customers WHERE lower(username) = ?;", (username.strip().lower(),))
            row = cursor.fetchone()
            return Customer.from_row(row) if row else None
        finally:
            conn.close()

    def get_customer_by_cnic(self, cnic: str) -> Optional[Customer]:
        """Retrieves a customer by CNIC."""
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM customers WHERE cnic = ?;", (cnic.strip(),))
            row = cursor.fetchone()
            return Customer.from_row(row) if row else None
        finally:
            conn.close()

    def get_all_customers(self, status: Optional[str] = None) -> List[Customer]:
        """Returns all customers, optionally filtered by status."""
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            if status:
                cursor.execute("SELECT * FROM customers WHERE status = ? ORDER BY id ASC;", (status,))
            else:
                cursor.execute("SELECT * FROM customers ORDER BY id ASC;")
            rows = cursor.fetchall()
            return [Customer.from_row(r) for r in rows]
        finally:
            conn.close()

    def search_customers(self, query: str) -> List[Customer]:
        """
        Searches customers across ID, Full Name, CNIC, Phone, and Username.
        """
        if not query or not query.strip():
            return self.get_all_customers()

        clean_query = f"%{query.strip().lower()}%"
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM customers
                WHERE cast(id as text) LIKE ?
                   OR lower(full_name) LIKE ?
                   OR lower(cnic) LIKE ?
                   OR lower(phone) LIKE ?
                   OR lower(username) LIKE ?
                ORDER BY id ASC;
            """, (clean_query, clean_query, clean_query, clean_query, clean_query))
            rows = cursor.fetchall()
            return [Customer.from_row(r) for r in rows]
        finally:
            conn.close()

    def update_customer_profile(
        self,
        customer_id: int,
        full_name: Optional[str] = None,
        phone: Optional[str] = None,
        email: Optional[str] = None,
        address: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Updates profile information for a customer.
        """
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM customers WHERE id = ?;", (customer_id,))
            current = cursor.fetchone()
            if not current:
                return False, "Customer not found."

            # Check email uniqueness if changing email
            if email and email.strip().lower() != current["email"].lower():
                clean_email = email.strip().lower()
                cursor.execute("SELECT id FROM customers WHERE lower(email) = ? AND id != ?;", (clean_email, customer_id))
                if cursor.fetchone():
                    return False, f"Email '{clean_email}' is already used by another customer."

            new_name = full_name.strip() if full_name else current["full_name"]
            new_phone = phone.strip() if phone else current["phone"]
            new_email = email.strip().lower() if email else current["email"]
            new_address = address.strip() if address else current["address"]

            with self.db.transaction() as tx_cursor:
                tx_cursor.execute("""
                    UPDATE customers
                    SET full_name = ?, phone = ?, email = ?, address = ?
                    WHERE id = ?;
                """, (new_name, new_phone, new_email, new_address, customer_id))

            log_event("CUSTOMER_PROFILE_UPDATED", f"Customer ID {customer_id} updated profile details.")
            return True, "Profile details updated successfully."

        except Exception as ex:
            log_event("CUSTOMER_UPDATE_ERROR", f"Error updating customer ID {customer_id}: {ex}", level="ERROR")
            return False, f"Failed to update profile: {ex}"
        finally:
            conn.close()

    def set_customer_status(self, customer_id: int, status: str) -> Tuple[bool, str]:
        """Blocks or unblocks a customer."""
        if status not in [CUSTOMER_STATUS_ACTIVE, CUSTOMER_STATUS_BLOCKED]:
            return False, f"Invalid customer status '{status}'."

        customer = self.get_customer_by_id(customer_id)
        if not customer:
            return False, "Customer not found."

        try:
            with self.db.transaction() as tx_cursor:
                tx_cursor.execute("UPDATE customers SET status = ? WHERE id = ?;", (status, customer_id))

            action_name = "UNBLOCKED" if status == CUSTOMER_STATUS_ACTIVE else "BLOCKED"
            log_event(f"CUSTOMER_{action_name}", f"Customer ID {customer_id} ({customer.username}) status set to {status}.")
            return True, f"Customer successfully {status.lower()}."
        except Exception as ex:
            log_event("CUSTOMER_STATUS_ERROR", f"Error updating customer status: {ex}", level="ERROR")
            return False, f"Failed to update status: {ex}"

    def delete_customer(self, customer_id: int) -> Tuple[bool, str]:
        """
        Deletes a customer if and only if they have no active accounts and zero balances.
        """
        customer = self.get_customer_by_id(customer_id)
        if not customer:
            return False, "Customer not found."

        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            # Check for accounts
            cursor.execute("SELECT id, account_number, balance, status FROM accounts WHERE customer_id = ?;", (customer_id,))
            accounts = cursor.fetchall()

            for acc in accounts:
                if acc["status"] in [ACCOUNT_STATUS_ACTIVE, ACCOUNT_STATUS_FROZEN]:
                    return False, f"Cannot delete customer. Active/Frozen account '{acc['account_number']}' must be closed first."
                if Decimal(str(acc["balance"])) > Decimal("0.00"):
                    return False, f"Cannot delete customer. Account '{acc['account_number']}' has a non-zero balance of {acc['balance']}."

            with self.db.transaction() as tx_cursor:
                # If all accounts are closed and settled, delete records
                tx_cursor.execute("DELETE FROM accounts WHERE customer_id = ?;", (customer_id,))
                tx_cursor.execute("DELETE FROM customers WHERE id = ?;", (customer_id,))

            log_event("CUSTOMER_DELETED", f"Customer ID {customer_id} ({customer.username}) deleted.")
            return True, f"Customer '{customer.full_name}' and settled accounts removed successfully."
        except Exception as ex:
            log_event("CUSTOMER_DELETE_ERROR", f"Error deleting customer ID {customer_id}: {ex}", level="ERROR")
            return False, f"Failed to delete customer: {ex}"
        finally:
            conn.close()
