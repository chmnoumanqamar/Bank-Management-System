"""
Comprehensive Automated Test Suite for Bank Management System.
Validates authentication, business rules, financial precision, atomic rollbacks, and report exports.
"""

import os
import unittest
import tempfile
import csv
from decimal import Decimal
from datetime import datetime, date

from database import DatabaseManager
from services.auth_service import AuthService
from services.customer_service import CustomerService
from services.account_service import AccountService
from services.transaction_service import TransactionService
from reports.report_generator import ReportGenerator
from utils.security import hash_password, verify_password
from utils.validators import (
    validate_full_name,
    validate_cnic,
    validate_phone,
    validate_email,
    validate_address,
    validate_date_of_birth,
    validate_username,
    validate_password as val_password,
    validate_amount,
    validate_account_number
)
from config import (
    ACCOUNT_TYPE_SAVINGS,
    ACCOUNT_TYPE_CURRENT,
    ACCOUNT_STATUS_ACTIVE,
    ACCOUNT_STATUS_FROZEN,
    ACCOUNT_STATUS_CLOSED,
    CUSTOMER_STATUS_ACTIVE,
    CUSTOMER_STATUS_BLOCKED,
    TRANSACTION_TYPE_DEPOSIT,
    TRANSACTION_TYPE_WITHDRAWAL,
    TRANSACTION_TYPE_TRANSFER,
    TRANSACTION_TYPE_TRANSFER_RECEIVED
)

class TestBankingSystem(unittest.TestCase):
    """Test suite covering all core banking operations and security requirements."""

    def setUp(self):
        """Creates a temporary database and service stack for isolated testing."""
        self.temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.temp_db.close()
        self.db_path = self.temp_db.name

        self.db = DatabaseManager(self.db_path)
        self.db.seed_demo_data()

        self.auth_service = AuthService(self.db)
        self.customer_service = CustomerService(self.db)
        self.account_service = AccountService(self.db)
        self.transaction_service = TransactionService(self.db)
        self.report_generator = ReportGenerator(self.db)

    def tearDown(self):
        """Cleans up temporary database file after tests."""
        if os.path.exists(self.db_path):
            try:
                os.remove(self.db_path)
            except Exception:
                pass

    # =========================================================================
    # 1. Security & Hashing Tests
    # =========================================================================
    def test_password_hashing_and_verification(self):
        """Tests that password hashing generates unique salts and verifies correctly."""
        password = "SecurePassword123!"
        hash1, salt1 = hash_password(password)
        hash2, salt2 = hash_password(password)

        # Hashes and salts must be unique across invocations
        self.assertNotEqual(salt1, salt2)
        self.assertNotEqual(hash1, hash2)

        # Correct password verification
        self.assertTrue(verify_password(password, hash1, salt1))
        self.assertTrue(verify_password(password, hash2, salt2))

        # Incorrect password verification
        self.assertFalse(verify_password("WrongPassword", hash1, salt1))
        self.assertFalse(verify_password("", hash1, salt1))

    # =========================================================================
    # 2. Input Validation Tests
    # =========================================================================
    def test_validators(self):
        """Tests all input validators with valid and boundary/invalid inputs."""
        # Name
        self.assertTrue(validate_full_name("Ahmed Ali")[0])
        self.assertTrue(validate_full_name("Dr. M. Tariq")[0])
        self.assertFalse(validate_full_name("")[0])
        self.assertFalse(validate_full_name("A123")[0])

        # CNIC
        self.assertTrue(validate_cnic("42101-1234567-1")[0])
        self.assertTrue(validate_cnic("4210112345671")[0])  # Normalized
        self.assertFalse(validate_cnic("42101-1234567")[0])  # Missing digit
        self.assertFalse(validate_cnic("ABCDE-1234567-1")[0])

        # Phone
        self.assertTrue(validate_phone("03001234567")[0])
        self.assertTrue(validate_phone("+923001234567")[0])
        self.assertFalse(validate_phone("0211234567")[0])  # Landline

        # Email
        self.assertTrue(validate_email("user@example.com")[0])
        self.assertFalse(validate_email("invalid-email")[0])

        # Date of Birth
        self.assertTrue(validate_date_of_birth("1995-05-15")[0])
        self.assertFalse(validate_date_of_birth("2026-01-01")[0])  # Under 18
        self.assertFalse(validate_date_of_birth("invalid-date")[0])

        # Monetary Amount
        valid, val, _ = validate_amount("5000.50")
        self.assertTrue(valid)
        self.assertEqual(val, Decimal("5000.50"))

        self.assertFalse(validate_amount("-100")[0])  # Negative
        self.assertFalse(validate_amount("0")[0])     # Zero
        self.assertFalse(validate_amount("50.123")[0]) # More than 2 decimal digits
        self.assertFalse(validate_amount("abc")[0])

        # Account Number
        self.assertTrue(validate_account_number("1000000001")[0])
        self.assertFalse(validate_account_number("10000")[0])
        self.assertFalse(validate_account_number("100000000A")[0])

    # =========================================================================
    # 3. Authentication Tests
    # =========================================================================
    def test_admin_authentication(self):
        """Tests admin login with correct and incorrect credentials."""
        # Success
        success, msg, admin = self.auth_service.login_admin("admin", "admin123")
        self.assertTrue(success)
        self.assertIsNotNone(admin)
        self.assertEqual(admin["username"], "admin")

        # Wrong password
        success, msg, admin = self.auth_service.login_admin("admin", "wrongpass")
        self.assertFalse(success)
        self.assertIsNone(admin)

        # Wrong username
        success, msg, admin = self.auth_service.login_admin("nonexistent", "admin123")
        self.assertFalse(success)

    def test_customer_authentication_and_blocking(self):
        """Tests customer login, session handling, and blocked customer prevention."""
        # Seeded demo customer: m_ali / customer123
        success, msg, customer = self.auth_service.login_customer("m_ali", "customer123")
        self.assertTrue(success)
        self.assertIsNotNone(customer)
        self.assertEqual(customer.username, "m_ali")

        # Password failure
        success, msg, _ = self.auth_service.login_customer("m_ali", "wrongpassword")
        self.assertFalse(success)

        # Block customer and verify login is prevented
        self.customer_service.set_customer_status(customer.id, CUSTOMER_STATUS_BLOCKED)
        success, msg, _ = self.auth_service.login_customer("m_ali", "customer123")
        self.assertFalse(success)
        self.assertIn("BLOCKED", msg)

        # Unblock customer and verify login works again
        self.customer_service.set_customer_status(customer.id, CUSTOMER_STATUS_ACTIVE)
        success, msg, _ = self.auth_service.login_customer("m_ali", "customer123")
        self.assertTrue(success)

    # =========================================================================
    # 4. Customer Management Tests
    # =========================================================================
    def test_customer_registration_and_uniqueness(self):
        """Tests new customer registration and unique constraints on CNIC, username, email."""
        success, msg, new_id = self.customer_service.register_customer(
            full_name="Hamza Khan",
            cnic="37405-1234567-9",
            phone="03331234567",
            email="hamza.khan@example.com",
            address="Street 10, Rawalpindi",
            date_of_birth="1992-03-21",
            username="hamza_k",
            password="Password123"
        )
        self.assertTrue(success)
        self.assertIsNotNone(new_id)

        # Duplicate CNIC
        success_dup_cnic, _, _ = self.customer_service.register_customer(
            full_name="Hamza Duplicate",
            cnic="37405-1234567-9",
            phone="03337654321",
            email="different@example.com",
            address="Street 11",
            date_of_birth="1992-03-21",
            username="hamza_diff",
            password="Password123"
        )
        self.assertFalse(success_dup_cnic)

        # Duplicate Username
        success_dup_user, _, _ = self.customer_service.register_customer(
            full_name="Hamza Dup User",
            cnic="37405-9999999-9",
            phone="03337654321",
            email="diff2@example.com",
            address="Street 11",
            date_of_birth="1992-03-21",
            username="hamza_k",
            password="Password123"
        )
        self.assertFalse(success_dup_user)

    def test_customer_profile_update(self):
        """Tests updating customer profile fields."""
        cust = self.customer_service.get_customer_by_username("m_ali")
        self.assertIsNotNone(cust)

        success, msg = self.customer_service.update_customer_profile(
            customer_id=cust.id,
            phone="03009999999",
            address="New Address, Lahore"
        )
        self.assertTrue(success)

        updated = self.customer_service.get_customer_by_id(cust.id)
        self.assertEqual(updated.phone, "03009999999")
        self.assertEqual(updated.address, "New Address, Lahore")

    # =========================================================================
    # 5. Account Management & Banking Rules Tests
    # =========================================================================
    def test_account_creation_and_rules(self):
        """Tests account creation, sequential account numbers, and status controls."""
        cust = self.customer_service.get_customer_by_username("m_ali")

        # Create Savings Account
        success, msg, new_acc = self.account_service.create_account(
            customer_id=cust.id,
            account_type=ACCOUNT_TYPE_SAVINGS,
            initial_deposit=Decimal("15000.00")
        )
        self.assertTrue(success)
        self.assertEqual(new_acc.balance, Decimal("15000.00"))
        self.assertEqual(len(new_acc.account_number), 10)

        # Initial deposit below minimum
        success_low, _, _ = self.account_service.create_account(
            customer_id=cust.id,
            account_type=ACCOUNT_TYPE_CURRENT,
            initial_deposit=Decimal("10.00")
        )
        self.assertFalse(success_low)

    def test_account_freeze_and_unfreeze(self):
        """Tests freezing and unfreezing an account."""
        acc_num = "1000000001"
        success, msg = self.account_service.freeze_account(acc_num)
        self.assertTrue(success)

        acc = self.account_service.get_account_by_number(acc_num)
        self.assertTrue(acc.is_frozen)

        # Deposit while frozen must fail
        dep_success, dep_msg, _ = self.transaction_service.deposit(acc_num, Decimal("500.00"))
        self.assertFalse(dep_success)

        # Unfreeze
        success_unf, _ = self.account_service.unfreeze_account(acc_num)
        self.assertTrue(success_unf)

        acc = self.account_service.get_account_by_number(acc_num)
        self.assertTrue(acc.is_active)

    def test_account_closure_rules(self):
        """Tests that account cannot be closed if balance > 0, and can be closed once balance is 0."""
        acc_num = "1000000001"
        acc = self.account_service.get_account_by_number(acc_num)

        # Attempt close with remaining balance (50,000.00)
        self.assertGreater(acc.balance, Decimal("0.00"))
        success, msg = self.account_service.close_account(acc_num)
        self.assertFalse(success)
        self.assertIn("settle", msg.lower())

        # Withdraw entire balance
        w_success, _, _ = self.transaction_service.withdraw(acc_num, acc.balance)
        self.assertTrue(w_success)

        # Now close account
        success_close, _ = self.account_service.close_account(acc_num)
        self.assertTrue(success_close)

        acc_closed = self.account_service.get_account_by_number(acc_num)
        self.assertTrue(acc_closed.is_closed)

    # =========================================================================
    # 6. Financial Transactions & Atomic Integrity Tests
    # =========================================================================
    def test_deposit_and_withdrawal(self):
        """Tests deposit and withdrawal operations with balance precision."""
        acc_num = "1000000001"
        acc_initial = self.account_service.get_account_by_number(acc_num)
        initial_bal = acc_initial.balance

        # 1. Deposit Rs. 10,000.00
        deposit_amt = Decimal("10000.00")
        success, msg, data = self.transaction_service.deposit(acc_num, deposit_amt)
        self.assertTrue(success)
        self.assertEqual(data["balance_after"], initial_bal + deposit_amt)

        # 2. Withdraw Rs. 5,000.00
        withdraw_amt = Decimal("5000.00")
        w_success, w_msg, w_data = self.transaction_service.withdraw(acc_num, withdraw_amt)
        self.assertTrue(w_success)
        self.assertEqual(w_data["balance_after"], initial_bal + deposit_amt - withdraw_amt)

        # 3. Overdraft / Insufficient balance rejection
        excess_amt = Decimal("1000000.00")
        ex_success, ex_msg, _ = self.transaction_service.withdraw(acc_num, excess_amt)
        self.assertFalse(ex_success)
        self.assertIn("Insufficient", ex_msg)

    def test_atomic_transfer(self):
        """Tests double-entry atomic funds transfer between two accounts."""
        src_acc_num = "1000000001" # Initial: 50,000.00
        dst_acc_num = "1000000002" # Initial: 75,000.00

        src_initial = self.account_service.get_account_by_number(src_acc_num).balance
        dst_initial = self.account_service.get_account_by_number(dst_acc_num).balance

        transfer_amt = Decimal("20000.00")
        success, msg, data = self.transaction_service.transfer(
            source_account_number=src_acc_num,
            destination_account_number=dst_acc_num,
            amount=transfer_amt,
            description="Bill Payment Transfer"
        )
        self.assertTrue(success)

        src_after = self.account_service.get_account_by_number(src_acc_num).balance
        dst_after = self.account_service.get_account_by_number(dst_acc_num).balance

        self.assertEqual(src_after, src_initial - transfer_amt)
        self.assertEqual(dst_after, dst_initial + transfer_amt)

        # Verify transaction logs for both accounts
        src_txns = self.transaction_service.get_transactions_for_account(
            self.account_service.get_account_by_number(src_acc_num).id
        )
        dst_txns = self.transaction_service.get_transactions_for_account(
            self.account_service.get_account_by_number(dst_acc_num).id
        )

        self.assertTrue(any(t.transaction_type == TRANSACTION_TYPE_TRANSFER for t in src_txns))
        self.assertTrue(any(t.transaction_type == TRANSACTION_TYPE_TRANSFER_RECEIVED for t in dst_txns))

    def test_transfer_failure_and_rollback(self):
        """Tests that a failed transfer rolls back completely and alters zero balances."""
        src_acc_num = "1000000001"
        dst_acc_num = "1000000002"

        # Freeze destination account
        self.account_service.freeze_account(dst_acc_num)

        src_before = self.account_service.get_account_by_number(src_acc_num).balance
        dst_before = self.account_service.get_account_by_number(dst_acc_num).balance

        # Transfer must fail
        success, msg, _ = self.transaction_service.transfer(
            source_account_number=src_acc_num,
            destination_account_number=dst_acc_num,
            amount=Decimal("10000.00")
        )
        self.assertFalse(success)

        # Check balances remained 100% untouched
        src_after = self.account_service.get_account_by_number(src_acc_num).balance
        dst_after = self.account_service.get_account_by_number(dst_acc_num).balance

        self.assertEqual(src_before, src_after)
        self.assertEqual(dst_before, dst_after)

    # =========================================================================
    # 7. Reports & CSV Export Tests
    # =========================================================================
    def test_reports_and_csv_export(self):
        """Tests dashboard statistics calculation and CSV generation."""
        stats = self.report_generator.get_dashboard_statistics()
        self.assertGreaterEqual(stats["total_customers"], 2)
        self.assertGreaterEqual(stats["total_accounts"], 2)
        self.assertGreaterEqual(stats["total_bank_balance"], Decimal("125000.00"))

        # Test CSV export
        cust_csv = self.report_generator.export_customers_csv("test_customers.csv")
        self.assertTrue(os.path.exists(cust_csv))
        with open(cust_csv, mode="r", encoding="utf-8") as f:
            reader = csv.reader(f)
            headers = next(reader)
            self.assertIn("Customer ID", headers)

        acc_csv = self.report_generator.export_accounts_csv("test_accounts.csv")
        self.assertTrue(os.path.exists(acc_csv))

        txn_csv = self.report_generator.export_transactions_csv("test_transactions.csv")
        self.assertTrue(os.path.exists(txn_csv))

        # Cleanup test CSVs
        for fpath in [cust_csv, acc_csv, txn_csv]:
            if os.path.exists(fpath):
                os.remove(fpath)

if __name__ == "__main__":
    unittest.main()
