"""
Authentication and Session Service.
Handles admin/customer logins, password verification, password updates, and session states.
"""

from typing import Optional, Tuple, Dict, Any
from database import DatabaseManager
from models.customer import Customer
from utils.security import verify_password, hash_password
from utils.logger import log_event
from config import CUSTOMER_STATUS_BLOCKED

class AuthService:
    """Provides authentication and password management services."""

    def __init__(self, db: DatabaseManager):
        self.db = db
        self.current_user: Optional[Any] = None
        self.current_role: Optional[str] = None  # "ADMIN" | "CUSTOMER"

    @property
    def is_authenticated(self) -> bool:
        """Returns True if a user is currently logged in."""
        return self.current_user is not None

    def login_admin(self, username: str, password: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Authenticates an administrator with username and password.
        
        Returns:
            Tuple of (success: bool, message: str, admin_info: Optional[dict])
        """
        if not username or not password:
            return False, "Username and password are required.", None

        clean_username = username.strip().lower()

        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, username, password_hash, salt, full_name, email, created_at
                FROM admins
                WHERE lower(username) = ?;
            """, (clean_username,))
            row = cursor.fetchone()

            if not row:
                log_event("ADMIN_LOGIN_FAILED", f"Admin login failed: Username '{clean_username}' not found.", level="WARNING")
                return False, "Invalid admin username or password.", None

            stored_hash = row["password_hash"]
            stored_salt = row["salt"]

            if not verify_password(password, stored_hash, stored_salt):
                log_event("ADMIN_LOGIN_FAILED", f"Admin login failed: Invalid password for '{clean_username}'.", level="WARNING")
                return False, "Invalid admin username or password.", None

            admin_data = {
                "id": row["id"],
                "username": row["username"],
                "full_name": row["full_name"],
                "email": row["email"],
                "created_at": row["created_at"]
            }

            self.current_user = admin_data
            self.current_role = "ADMIN"
            log_event("ADMIN_LOGIN_SUCCESS", f"Admin '{clean_username}' logged in successfully.")
            return True, "Admin login successful.", admin_data

        except Exception as ex:
            log_event("ADMIN_LOGIN_ERROR", f"Error during admin login: {ex}", level="ERROR")
            return False, "A system error occurred during login. Please try again.", None
        finally:
            conn.close()

    def login_customer(self, username: str, password: str) -> Tuple[bool, str, Optional[Customer]]:
        """
        Authenticates a customer with username and password.
        
        Returns:
            Tuple of (success: bool, message: str, customer: Optional[Customer])
        """
        if not username or not password:
            return False, "Username and password are required.", None

        clean_username = username.strip().lower()

        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM customers
                WHERE lower(username) = ?;
            """, (clean_username,))
            row = cursor.fetchone()

            if not row:
                log_event("CUSTOMER_LOGIN_FAILED", f"Customer login failed: Username '{clean_username}' not found.", level="WARNING")
                return False, "Invalid customer username or password.", None

            customer = Customer.from_row(row)

            if not verify_password(password, customer.password_hash, customer.salt):
                log_event("CUSTOMER_LOGIN_FAILED", f"Customer login failed: Invalid password for '{clean_username}'.", level="WARNING")
                return False, "Invalid customer username or password.", None

            if customer.is_blocked:
                log_event("CUSTOMER_LOGIN_BLOCKED", f"Blocked customer '{clean_username}' attempted login.", level="WARNING")
                return False, "Your customer profile is currently BLOCKED. Please contact branch administration.", None

            self.current_user = customer
            self.current_role = "CUSTOMER"
            log_event("CUSTOMER_LOGIN_SUCCESS", f"Customer '{clean_username}' (ID: {customer.id}) logged in successfully.")
            return True, "Login successful.", customer

        except Exception as ex:
            log_event("CUSTOMER_LOGIN_ERROR", f"Error during customer login: {ex}", level="ERROR")
            return False, "A system error occurred during login. Please try again.", None
        finally:
            conn.close()

    def change_customer_password(
        self,
        customer_id: int,
        current_password: str,
        new_password: str
    ) -> Tuple[bool, str]:
        """
        Changes customer password after verifying existing password and hashing the new one.
        """
        if not current_password or not new_password:
            return False, "Current and new passwords cannot be empty."

        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT password_hash, salt, username FROM customers WHERE id = ?", (customer_id,))
            row = cursor.fetchone()

            if not row:
                return False, "Customer record not found."

            if not verify_password(current_password, row["password_hash"], row["salt"]):
                return False, "Incorrect current password."

            new_hash, new_salt = hash_password(new_password)

            with self.db.transaction() as tx_cursor:
                tx_cursor.execute("""
                    UPDATE customers
                    SET password_hash = ?, salt = ?
                    WHERE id = ?;
                """, (new_hash, new_salt, customer_id))

            log_event("PASSWORD_CHANGED", f"Customer ID {customer_id} ({row['username']}) successfully changed password.")
            return True, "Password changed successfully."

        except Exception as ex:
            log_event("PASSWORD_CHANGE_ERROR", f"Error changing password for customer ID {customer_id}: {ex}", level="ERROR")
            return False, f"Failed to change password: {ex}"
        finally:
            conn.close()

    def logout(self):
        """Clears active session."""
        if self.current_user:
            user_desc = (
                self.current_user.get("username")
                if isinstance(self.current_user, dict)
                else getattr(self.current_user, "username", "Unknown")
            )
            log_event("USER_LOGOUT", f"User '{user_desc}' ({self.current_role}) logged out.")
        self.current_user = None
        self.current_role = None
