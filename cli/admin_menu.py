"""
Admin CLI Menu.
Implements the administrative dashboard, customer management, account administration,
transaction auditing, and reporting workflows.
"""

from decimal import Decimal
from typing import Dict, Any, Optional

from database import DatabaseManager
from services.auth_service import AuthService
from services.customer_service import CustomerService
from services.account_service import AccountService
from services.transaction_service import TransactionService
from reports.report_generator import ReportGenerator
from utils.security import get_hidden_input
from utils.validators import (
    validate_full_name,
    validate_cnic,
    validate_phone,
    validate_email,
    validate_address,
    validate_date_of_birth,
    validate_username,
    validate_password,
    validate_amount,
    validate_account_number
)
from utils.helpers import (
    print_header,
    print_sub_header,
    print_separator,
    print_table,
    print_success,
    print_error,
    print_warning,
    print_info,
    format_currency,
    format_date_pretty,
    prompt_confirmation,
    pause_for_user
)
from config import (
    ACCOUNT_TYPE_SAVINGS,
    ACCOUNT_TYPE_CURRENT,
    ACCOUNT_TYPES,
    CUSTOMER_STATUS_ACTIVE,
    CUSTOMER_STATUS_BLOCKED,
    ACCOUNT_STATUS_ACTIVE,
    ACCOUNT_STATUS_FROZEN,
    ACCOUNT_STATUS_CLOSED,
    MIN_INITIAL_DEPOSIT
)

class AdminMenu:
    """Handles the Administrator command line interface."""

    def __init__(
        self,
        auth_service: AuthService,
        customer_service: CustomerService,
        account_service: AccountService,
        transaction_service: TransactionService,
        report_generator: ReportGenerator
    ):
        self.auth_service = auth_service
        self.customer_service = customer_service
        self.account_service = account_service
        self.transaction_service = transaction_service
        self.report_generator = report_generator

    def display(self):
        """Main loop for the Admin Menu."""
        admin_data = self.auth_service.current_user
        admin_name = admin_data.get("full_name", "Administrator") if isinstance(admin_data, dict) else "Administrator"

        while self.auth_service.is_authenticated and self.auth_service.current_role == "ADMIN":
            print_header("BANK MANAGEMENT SYSTEM - ADMIN MENU", width=60)
            print(f" Logged in as: {admin_name} | Role: System Administrator\n")
            print(" 1.  Dashboard")
            print(" 2.  Add Customer")
            print(" 3.  View Customers")
            print(" 4.  Search Customer")
            print(" 5.  Update Customer")
            print(" 6.  Block Customer")
            print(" 7.  Unblock Customer")
            print(" 8.  Create Account")
            print(" 9.  View Accounts")
            print(" 10. Search Account")
            print(" 11. Freeze Account")
            print(" 12. Unfreeze Account")
            print(" 13. Close Account")
            print(" 14. View Transactions")
            print(" 15. Reports & CSV Export")
            print(" 16. Logout")
            print_separator(60)

            choice = input("Enter your choice (1-16): ").strip()

            if choice == "1":
                self.show_dashboard()
            elif choice == "2":
                self.add_customer()
            elif choice == "3":
                self.view_customers()
            elif choice == "4":
                self.search_customer()
            elif choice == "5":
                self.update_customer()
            elif choice == "6":
                self.block_customer()
            elif choice == "7":
                self.unblock_customer()
            elif choice == "8":
                self.create_account()
            elif choice == "9":
                self.view_accounts()
            elif choice == "10":
                self.search_account()
            elif choice == "11":
                self.freeze_account()
            elif choice == "12":
                self.unfreeze_account()
            elif choice == "13":
                self.close_account()
            elif choice == "14":
                self.view_transactions()
            elif choice == "15":
                self.reports_submenu()
            elif choice == "16":
                self.auth_service.logout()
                print_success("Admin logged out successfully.")
                pause_for_user()
                break
            else:
                print_error("Invalid option. Please choose a number between 1 and 16.")
                pause_for_user()

    def show_dashboard(self):
        """Displays real-time dynamic statistics across the entire banking system."""
        stats = self.report_generator.get_dashboard_statistics()

        print_header("ADMIN DASHBOARD", width=60)
        print(f" Total Customers   : {stats['total_customers']}")
        print(f"   - Active        : {stats['active_customers']}")
        print(f"   - Blocked       : {stats['blocked_customers']}")
        print_separator(60)
        print(f" Total Accounts    : {stats['total_accounts']}")
        print(f"   - Active        : {stats['active_accounts']}")
        print(f"   - Frozen        : {stats['frozen_accounts']}")
        print(f"   - Closed        : {stats['closed_accounts']}")
        print(f"   - Savings Types : {stats['savings_accounts']}")
        print(f"   - Current Types : {stats['current_accounts']}")
        print_separator(60)
        print(f" Total Bank Balance: {format_currency(stats['total_bank_balance'])}")
        print(f" Total Deposits    : {format_currency(stats['total_deposits'])}")
        print(f" Total Withdrawals : {format_currency(stats['total_withdrawals'])}")
        print(f" Total Transfers   : {format_currency(stats['total_transfers'])}")
        print(f" Total Transactions: {stats['total_transactions']}")
        print_separator(60)
        pause_for_user()

    def add_customer(self):
        """Handles administrative customer registration workflow."""
        print_header("ADD NEW CUSTOMER", width=60)

        # 1. Full Name
        while True:
            name_input = input("Enter Full Name: ").strip()
            valid, res = validate_full_name(name_input)
            if valid:
                full_name = res
                break
            print_error(res)

        # 2. CNIC
        while True:
            cnic_input = input("Enter CNIC (e.g. 42101-1234567-1): ").strip()
            valid, res = validate_cnic(cnic_input)
            if valid:
                cnic = res
                break
            print_error(res)

        # 3. Phone
        while True:
            phone_input = input("Enter Phone Number (e.g. 03001234567): ").strip()
            valid, res = validate_phone(phone_input)
            if valid:
                phone = res
                break
            print_error(res)

        # 4. Email
        while True:
            email_input = input("Enter Email Address: ").strip()
            valid, res = validate_email(email_input)
            if valid:
                email = res
                break
            print_error(res)

        # 5. Address
        while True:
            address_input = input("Enter Residential Address: ").strip()
            valid, res = validate_address(address_input)
            if valid:
                address = res
                break
            print_error(res)

        # 6. Date of Birth
        while True:
            dob_input = input("Enter Date of Birth (YYYY-MM-DD): ").strip()
            valid, res = validate_date_of_birth(dob_input)
            if valid:
                dob = res
                break
            print_error(res)

        # 7. Username
        while True:
            username_input = input("Enter Desired Username: ").strip()
            valid, res = validate_username(username_input)
            if valid:
                username = res
                break
            print_error(res)

        # 8. Password
        while True:
            password = get_hidden_input("Enter Password: ")
            valid, msg = validate_password(password)
            if not valid:
                print_error(msg)
                continue
            confirm = get_hidden_input("Confirm Password: ")
            if password != confirm:
                print_error("Passwords do not match. Please try again.")
                continue
            break

        print_sub_header("Review Customer Details", width=60)
        print(f" Name        : {full_name}")
        print(f" CNIC        : {cnic}")
        print(f" Phone       : {phone}")
        print(f" Email       : {email}")
        print(f" Address     : {address}")
        print(f" DOB         : {dob}")
        print(f" Username    : {username}")

        if not prompt_confirmation("\nConfirm registration of this customer? (Y/N): "):
            print_warning("Customer registration cancelled.")
            pause_for_user()
            return

        success, msg, new_id = self.customer_service.register_customer(
            full_name=full_name,
            cnic=cnic,
            phone=phone,
            email=email,
            address=address,
            date_of_birth=dob,
            username=username,
            password=password
        )

        if success:
            print_success(f"{msg} Customer ID: {new_id}")
        else:
            print_error(msg)

        pause_for_user()

    def view_customers(self):
        """Renders all registered customers in a tabular format."""
        print_header("REGISTERED CUSTOMERS", width=60)
        customers = self.customer_service.get_all_customers()

        headers = ["ID", "Full Name", "CNIC", "Phone", "Email", "Username", "Status", "Registered Date"]
        rows = [
            [
                c.id,
                c.full_name,
                c.cnic,
                c.phone,
                c.email,
                c.username,
                c.status,
                format_date_pretty(c.created_at)
            ]
            for c in customers
        ]

        print_table(headers, rows)
        pause_for_user()

    def search_customer(self):
        """Allows searching customers by keyword across ID, Name, CNIC, Phone, or Username."""
        print_header("SEARCH CUSTOMER", width=60)
        query = input("Enter search term (ID, Name, CNIC, Phone, or Username): ").strip()

        if not query:
            print_warning("Search term cannot be empty.")
            pause_for_user()
            return

        results = self.customer_service.search_customers(query)
        if not results:
            print_warning("No customer found matching the search criteria.")
            pause_for_user()
            return

        headers = ["ID", "Full Name", "CNIC", "Phone", "Email", "Username", "Status"]
        rows = [
            [c.id, c.full_name, c.cnic, c.phone, c.email, c.username, c.status]
            for c in results
        ]
        print_table(headers, rows)
        pause_for_user()

    def update_customer(self):
        """Updates customer profile details."""
        print_header("UPDATE CUSTOMER DETAILS", width=60)
        ident = input("Enter Customer ID or CNIC to update: ").strip()

        customer = None
        if ident.isdigit():
            customer = self.customer_service.get_customer_by_id(int(ident))
        if not customer:
            customer = self.customer_service.get_customer_by_cnic(ident)

        if not customer:
            print_error("Customer record not found.")
            pause_for_user()
            return

        print_sub_header(f"Current Details for Customer #{customer.id} ({customer.full_name})", width=60)
        print(f" Full Name   : {customer.full_name}")
        print(f" CNIC        : {customer.cnic} (Cannot be modified directly)")
        print(f" Phone       : {customer.phone}")
        print(f" Email       : {customer.email}")
        print(f" Address     : {customer.address}")
        print(f" Status      : {customer.status}")
        print_separator(60)
        print("Leave field blank and press Enter to keep current value.\n")

        # 1. Name
        new_name_input = input(f"New Full Name [{customer.full_name}]: ").strip()
        new_name = None
        if new_name_input:
            valid, res = validate_full_name(new_name_input)
            if not valid:
                print_error(res)
                pause_for_user()
                return
            new_name = res

        # 2. Phone
        new_phone_input = input(f"New Phone [{customer.phone}]: ").strip()
        new_phone = None
        if new_phone_input:
            valid, res = validate_phone(new_phone_input)
            if not valid:
                print_error(res)
                pause_for_user()
                return
            new_phone = res

        # 3. Email
        new_email_input = input(f"New Email [{customer.email}]: ").strip()
        new_email = None
        if new_email_input:
            valid, res = validate_email(new_email_input)
            if not valid:
                print_error(res)
                pause_for_user()
                return
            new_email = res

        # 4. Address
        new_addr_input = input(f"New Address [{customer.address}]: ").strip()
        new_addr = None
        if new_addr_input:
            valid, res = validate_address(new_addr_input)
            if not valid:
                print_error(res)
                pause_for_user()
                return
            new_addr = res

        if not any([new_name, new_phone, new_email, new_addr]):
            print_info("No changes were made.")
            pause_for_user()
            return

        if not prompt_confirmation("\nConfirm these profile updates? (Y/N): "):
            print_warning("Profile update cancelled.")
            pause_for_user()
            return

        success, msg = self.customer_service.update_customer_profile(
            customer_id=customer.id,
            full_name=new_name,
            phone=new_phone,
            email=new_email,
            address=new_addr
        )

        if success:
            print_success(msg)
        else:
            print_error(msg)

        pause_for_user()

    def block_customer(self):
        """Blocks a customer profile."""
        print_header("BLOCK CUSTOMER", width=60)
        ident = input("Enter Customer ID or CNIC to block: ").strip()

        customer = None
        if ident.isdigit():
            customer = self.customer_service.get_customer_by_id(int(ident))
        if not customer:
            customer = self.customer_service.get_customer_by_cnic(ident)

        if not customer:
            print_error("Customer not found.")
            pause_for_user()
            return

        if customer.is_blocked:
            print_warning(f"Customer '{customer.full_name}' is already Blocked.")
            pause_for_user()
            return

        print_sub_header(f"Customer Details: {customer.full_name} (ID: {customer.id})", width=60)
        print(f" CNIC    : {customer.cnic}")
        print(f" Username: {customer.username}")
        print(f" Status  : {customer.status}")
        print_warning("Blocking this customer will immediately prevent them from logging in.")

        if not prompt_confirmation(f"Are you sure you want to BLOCK customer #{customer.id}? (Y/N): "):
            print_info("Operation cancelled.")
            pause_for_user()
            return

        success, msg = self.customer_service.set_customer_status(customer.id, CUSTOMER_STATUS_BLOCKED)
        if success:
            print_success(msg)
        else:
            print_error(msg)

        pause_for_user()

    def unblock_customer(self):
        """Unblocks a blocked customer profile."""
        print_header("UNBLOCK CUSTOMER", width=60)
        ident = input("Enter Customer ID or CNIC to unblock: ").strip()

        customer = None
        if ident.isdigit():
            customer = self.customer_service.get_customer_by_id(int(ident))
        if not customer:
            customer = self.customer_service.get_customer_by_cnic(ident)

        if not customer:
            print_error("Customer not found.")
            pause_for_user()
            return

        if customer.is_active:
            print_warning(f"Customer '{customer.full_name}' is already Active.")
            pause_for_user()
            return

        print_sub_header(f"Customer Details: {customer.full_name} (ID: {customer.id})", width=60)
        print(f" CNIC    : {customer.cnic}")
        print(f" Username: {customer.username}")
        print(f" Status  : {customer.status}")

        if not prompt_confirmation(f"Confirm UNBLOCKING customer #{customer.id}? (Y/N): "):
            print_info("Operation cancelled.")
            pause_for_user()
            return

        success, msg = self.customer_service.set_customer_status(customer.id, CUSTOMER_STATUS_ACTIVE)
        if success:
            print_success(msg)
        else:
            print_error(msg)

        pause_for_user()

    def create_account(self):
        """Creates a new bank account with an initial deposit."""
        print_header("CREATE BANK ACCOUNT", width=60)
        cust_id_input = input("Enter Customer ID: ").strip()

        if not cust_id_input.isdigit():
            print_error("Customer ID must be a positive integer.")
            pause_for_user()
            return

        customer = self.customer_service.get_customer_by_id(int(cust_id_input))
        if not customer:
            print_error(f"Customer with ID {cust_id_input} not found.")
            pause_for_user()
            return

        if not customer.is_active:
            print_error(f"Cannot create account: Customer '{customer.full_name}' is {customer.status}.")
            pause_for_user()
            return

        print_sub_header(f"Customer: {customer.full_name} | CNIC: {customer.cnic}", width=60)
        print("Select Account Type:")
        print(f" 1. {ACCOUNT_TYPE_SAVINGS}")
        print(f" 2. {ACCOUNT_TYPE_CURRENT}")

        type_choice = input("Enter choice (1 or 2): ").strip()
        if type_choice == "1":
            account_type = ACCOUNT_TYPE_SAVINGS
        elif type_choice == "2":
            account_type = ACCOUNT_TYPE_CURRENT
        else:
            print_error("Invalid account type selection.")
            pause_for_user()
            return

        # Initial Deposit
        while True:
            dep_input = input(f"Enter Initial Deposit amount (Min {format_currency(MIN_INITIAL_DEPOSIT)}): ").strip()
            valid, amount, msg = validate_amount(dep_input, min_val=MIN_INITIAL_DEPOSIT)
            if valid:
                break
            print_error(msg)

        print_sub_header("ACCOUNT CREATION SUMMARY", width=60)
        print(f" Customer        : {customer.full_name} (ID: {customer.id})")
        print(f" Account Type    : {account_type}")
        print(f" Initial Deposit : {format_currency(amount)}")

        if not prompt_confirmation("\nConfirm account creation? (Y/N): "):
            print_warning("Account creation cancelled.")
            pause_for_user()
            return

        success, msg, new_acc = self.account_service.create_account(
            customer_id=customer.id,
            account_type=account_type,
            initial_deposit=amount
        )

        if success and new_acc:
            print_success(f"{msg}\n Account Number: {new_acc.account_number}\n Balance       : {format_currency(new_acc.balance)}")
        else:
            print_error(msg)

        pause_for_user()

    def view_accounts(self):
        """Displays all bank accounts across all customers."""
        print_header("ALL BANK ACCOUNTS", width=60)
        accounts_data = self.account_service.search_accounts("")

        headers = ["Acc Number", "Customer Name", "CNIC", "Type", "Balance", "Status", "Created On", "Closed On"]
        rows = [
            [
                a["account_number"],
                a["customer_name"],
                a["customer_cnic"],
                a["account_type"],
                format_currency(Decimal(str(a["balance"]))),
                a["status"],
                format_date_pretty(a["created_at"]),
                format_date_pretty(a["closed_at"]) if a["closed_at"] else "-"
            ]
            for a in accounts_data
        ]

        print_table(headers, rows)
        pause_for_user()

    def search_account(self):
        """Searches accounts by Account Number, Customer Name, CNIC, Type, or Status."""
        print_header("SEARCH ACCOUNTS", width=60)
        query = input("Enter search term (Account #, Customer Name, CNIC, Type, Status): ").strip()

        if not query:
            print_warning("Search term cannot be empty.")
            pause_for_user()
            return

        results = self.account_service.search_accounts(query)
        if not results:
            print_warning("No accounts found matching your query.")
            pause_for_user()
            return

        headers = ["Acc Number", "Customer Name", "CNIC", "Type", "Balance", "Status"]
        rows = [
            [
                a["account_number"],
                a["customer_name"],
                a["customer_cnic"],
                a["account_type"],
                format_currency(Decimal(str(a["balance"]))),
                a["status"]
            ]
            for a in results
        ]
        print_table(headers, rows)
        pause_for_user()

    def freeze_account(self):
        """Freezes an active account."""
        print_header("FREEZE ACCOUNT", width=60)
        acc_num = input("Enter 10-Digit Account Number to freeze: ").strip()

        account = self.account_service.get_account_by_number(acc_num)
        if not account:
            print_error(f"Account '{acc_num}' not found.")
            pause_for_user()
            return

        print_sub_header(f"Account Details: {account.account_number}", width=60)
        print(f" Account Type : {account.account_type}")
        print(f" Current Status: {account.status}")
        print(f" Balance       : {format_currency(account.balance)}")

        if account.is_frozen:
            print_warning(f"Account '{acc_num}' is already Frozen.")
            pause_for_user()
            return

        if account.is_closed:
            print_error(f"Account '{acc_num}' is Closed and cannot be modified.")
            pause_for_user()
            return

        if not prompt_confirmation(f"Are you sure you want to freeze account {account.account_number}?\n(Y/N): "):
            print_info("Operation cancelled.")
            pause_for_user()
            return

        success, msg = self.account_service.freeze_account(account.account_number)
        if success:
            print_success(msg)
        else:
            print_error(msg)

        pause_for_user()

    def unfreeze_account(self):
        """Unfreezes a frozen account."""
        print_header("UNFREEZE ACCOUNT", width=60)
        acc_num = input("Enter 10-Digit Account Number to unfreeze: ").strip()

        account = self.account_service.get_account_by_number(acc_num)
        if not account:
            print_error(f"Account '{acc_num}' not found.")
            pause_for_user()
            return

        print_sub_header(f"Account Details: {account.account_number}", width=60)
        print(f" Account Type : {account.account_type}")
        print(f" Current Status: {account.status}")
        print(f" Balance       : {format_currency(account.balance)}")

        if account.is_active:
            print_warning(f"Account '{acc_num}' is already Active.")
            pause_for_user()
            return

        if account.is_closed:
            print_error(f"Account '{acc_num}' is permanently Closed and cannot be reopened.")
            pause_for_user()
            return

        if not prompt_confirmation(f"Confirm unfreezing/activating account {account.account_number}? (Y/N): "):
            print_info("Operation cancelled.")
            pause_for_user()
            return

        success, msg = self.account_service.unfreeze_account(account.account_number)
        if success:
            print_success(msg)
        else:
            print_error(msg)

        pause_for_user()

    def close_account(self):
        """Closes an account provided its balance is settled to exactly zero."""
        print_header("CLOSE ACCOUNT", width=60)
        acc_num = input("Enter 10-Digit Account Number to close: ").strip()

        account = self.account_service.get_account_by_number(acc_num)
        if not account:
            print_error(f"Account '{acc_num}' not found.")
            pause_for_user()
            return

        print_sub_header(f"Account Details: {account.account_number}", width=60)
        print(f" Type    : {account.account_type}")
        print(f" Status  : {account.status}")
        print(f" Balance : {format_currency(account.balance)}")

        if account.is_closed:
            print_warning(f"Account '{acc_num}' is already Closed.")
            pause_for_user()
            return

        if account.balance > Decimal("0.00"):
            print_error(
                f"Account cannot be closed.\n\n"
                f"Remaining Balance: {format_currency(account.balance)}\n\n"
                f"Please settle/withdraw the balance completely before closing."
            )
            pause_for_user()
            return

        if not prompt_confirmation(f"Confirm account closure for {account.account_number}? (Y/N): "):
            print_info("Account closure cancelled.")
            pause_for_user()
            return

        success, msg = self.account_service.close_account(account.account_number)
        if success:
            print_success(msg)
        else:
            print_error(msg)

        pause_for_user()

    def view_transactions(self):
        """Audits bank-wide transactions with search and filter capabilities."""
        print_header("BANK TRANSACTIONS AUDIT", width=60)
        print(" 1. View All Recent Transactions")
        print(" 2. Filter by Transaction Type")
        print(" 3. Search by Account / Customer / TXN ID")
        print(" 4. Back")

        sub_choice = input("\nEnter choice (1-4): ").strip()
        txn_type = None
        search_query = None

        if sub_choice == "1":
            pass
        elif sub_choice == "2":
            print("\nSelect Type:")
            print(" 1. Deposit")
            print(" 2. Withdrawal")
            print(" 3. Transfer")
            print(" 4. Transfer Received")
            t_choice = input("Enter type (1-4): ").strip()
            type_map = {"1": "Deposit", "2": "Withdrawal", "3": "Transfer", "4": "Transfer Received"}
            txn_type = type_map.get(t_choice)
            if not txn_type:
                print_error("Invalid type.")
                pause_for_user()
                return
        elif sub_choice == "3":
            search_query = input("Enter search keyword: ").strip()
        elif sub_choice == "4":
            return
        else:
            print_error("Invalid choice.")
            pause_for_user()
            return

        records = self.transaction_service.get_all_transactions(query=search_query, txn_type=txn_type)
        headers = ["TXN ID", "Acc Number", "Customer", "Type", "Amount", "Balance After", "Related Acc", "Date & Time"]
        rows = [
            [
                r["transaction_id"],
                r["account_number"],
                r["customer_name"],
                r["transaction_type"],
                format_currency(Decimal(str(r["amount"]))),
                format_currency(Decimal(str(r["balance_after"]))),
                r["related_account"] or "-",
                format_date_pretty(r["transaction_date"])
            ]
            for r in records
        ]

        print_table(headers, rows)
        pause_for_user()

    def reports_submenu(self):
        """Admin reports and CSV export submenu."""
        while True:
            print_header("REPORTS & CSV EXPORT", width=60)
            print(" 1. Customer Report")
            print(" 2. Account Report")
            print(" 3. Financial Summary Report")
            print(" 4. Transaction Report")
            print(" 5. Export All Reports to CSV")
            print(" 6. Back to Admin Menu")
            print_separator(60)

            rep_choice = input("Enter your choice (1-6): ").strip()

            if rep_choice == "1":
                self.show_customer_report()
            elif rep_choice == "2":
                self.show_account_report()
            elif rep_choice == "3":
                self.show_financial_report()
            elif rep_choice == "4":
                self.show_transaction_report()
            elif rep_choice == "5":
                self.export_csv_reports()
            elif rep_choice == "6":
                break
            else:
                print_error("Invalid option. Please choose between 1 and 6.")
                pause_for_user()

    def show_customer_report(self):
        """Displays customer demographic summary and detailed listing."""
        stats = self.report_generator.get_dashboard_statistics()
        customers = self.customer_service.get_all_customers()

        print_header("CUSTOMER REPORT", width=60)
        print(f" Total Registered Customers : {stats['total_customers']}")
        print(f" Active Customers           : {stats['active_customers']}")
        print(f" Blocked Customers          : {stats['blocked_customers']}")
        print_separator(60)

        headers = ["ID", "Full Name", "CNIC", "Phone", "Email", "Status"]
        rows = [[c.id, c.full_name, c.cnic, c.phone, c.email, c.status] for c in customers]
        print_table(headers, rows)
        pause_for_user()

    def show_account_report(self):
        """Displays account distribution and balance summary."""
        stats = self.report_generator.get_dashboard_statistics()
        accounts = self.account_service.search_accounts("")

        print_header("ACCOUNT REPORT", width=60)
        print(f" Total Accounts   : {stats['total_accounts']}")
        print(f" Active Accounts  : {stats['active_accounts']}")
        print(f" Frozen Accounts  : {stats['frozen_accounts']}")
        print(f" Closed Accounts  : {stats['closed_accounts']}")
        print(f" Savings Accounts : {stats['savings_accounts']}")
        print(f" Current Accounts : {stats['current_accounts']}")
        print_separator(60)

        headers = ["Acc Number", "Customer Name", "Type", "Balance", "Status"]
        rows = [
            [
                a["account_number"],
                a["customer_name"],
                a["account_type"],
                format_currency(Decimal(str(a["balance"]))),
                a["status"]
            ]
            for a in accounts
        ]
        print_table(headers, rows)
        pause_for_user()

    def show_financial_report(self):
        """Displays aggregate financial health metrics."""
        stats = self.report_generator.get_dashboard_statistics()

        print_header("FINANCIAL HEALTH REPORT", width=60)
        print(f" Total Bank Vault Balance  : {format_currency(stats['total_bank_balance'])}")
        print(f" Cumulative Deposits       : {format_currency(stats['total_deposits'])}")
        print(f" Cumulative Withdrawals    : {format_currency(stats['total_withdrawals'])}")
        print(f" Cumulative Transfers      : {format_currency(stats['total_transfers'])}")
        print_separator(60)
        pause_for_user()

    def show_transaction_report(self):
        """Displays breakdown of transaction counts and recent operations."""
        stats = self.report_generator.get_dashboard_statistics()
        recent_txns = self.transaction_service.get_all_transactions()

        print_header("TRANSACTION AUDIT REPORT", width=60)
        print(f" Total Transactions Recorded : {stats['total_transactions']}")
        print_separator(60)

        headers = ["TXN ID", "Account #", "Type", "Amount", "Date"]
        rows = [
            [
                t["transaction_id"],
                t["account_number"],
                t["transaction_type"],
                format_currency(Decimal(str(t["amount"]))),
                format_date_pretty(t["transaction_date"])
            ]
            for t in recent_txns[:20]  # Show 20 most recent
        ]
        print_table(headers, rows)
        pause_for_user()

    def export_csv_reports(self):
        """Exports customers, accounts, and transactions to standard CSV files."""
        print_header("EXPORT REPORTS TO CSV", width=60)
        print("Generating CSV files in workspace directory...\n")

        try:
            cust_path = self.report_generator.export_customers_csv("customers_report.csv")
            print_success(f"Customers Report exported: {cust_path}")

            acc_path = self.report_generator.export_accounts_csv("accounts_report.csv")
            print_success(f"Accounts Report exported: {acc_path}")

            txn_path = self.report_generator.export_transactions_csv("transactions_report.csv")
            print_success(f"Transactions Report exported: {txn_path}")

            print_info("\nAll 3 CSV reports successfully generated using Python standard library csv module.")
        except Exception as ex:
            print_error(f"CSV Export failed: {ex}")

        pause_for_user()
