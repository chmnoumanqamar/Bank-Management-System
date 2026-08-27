"""
Main Application CLI Menu.
Provides the primary authentication dispatcher, registration portal, and top-level execution loop.
"""

import sys
from database import DatabaseManager
from services.auth_service import AuthService
from services.customer_service import CustomerService
from services.account_service import AccountService
from services.transaction_service import TransactionService
from reports.report_generator import ReportGenerator
from cli.admin_menu import AdminMenu
from cli.customer_menu import CustomerMenu
from utils.security import get_hidden_input
from utils.validators import (
    validate_full_name,
    validate_cnic,
    validate_phone,
    validate_email,
    validate_address,
    validate_date_of_birth,
    validate_username,
    validate_password
)
from utils.helpers import (
    print_header,
    print_sub_header,
    print_separator,
    print_double_separator,
    print_success,
    print_error,
    print_warning,
    print_info,
    prompt_confirmation,
    pause_for_user
)
from config import APP_NAME, APP_VERSION

class MainMenu:
    """Entry menu controller for the Bank Management System CLI."""

    def __init__(self, db: DatabaseManager):
        self.db = db
        self.auth_service = AuthService(db)
        self.customer_service = CustomerService(db)
        self.account_service = AccountService(db)
        self.transaction_service = TransactionService(db)
        self.report_generator = ReportGenerator(db)

        self.admin_menu = AdminMenu(
            self.auth_service,
            self.customer_service,
            self.account_service,
            self.transaction_service,
            self.report_generator
        )

        self.customer_menu = CustomerMenu(
            self.auth_service,
            self.customer_service,
            self.account_service,
            self.transaction_service
        )

    def run(self):
        """Runs the main application loop, catching KeyboardInterrupt safely."""
        try:
            while True:
                print_double_separator(50)
                print(f"{APP_NAME}".center(50))
                print(f"Version {APP_VERSION}".center(50))
                print_double_separator(50)
                print("\n 1. Admin Login")
                print(" 2. Customer Login")
                print(" 3. Customer Registration")
                print(" 4. Exit")
                print_separator(50)

                choice = input("Enter your choice (1-4): ").strip()

                if choice == "1":
                    self.handle_admin_login()
                elif choice == "2":
                    self.handle_customer_login()
                elif choice == "3":
                    self.handle_customer_registration()
                elif choice == "4":
                    self.handle_exit()
                    break
                else:
                    print_error("Invalid selection. Please choose an option between 1 and 4.")
                    pause_for_user()

        except KeyboardInterrupt:
            print("\n\nApplication closed safely.\nGoodbye!\n")
            sys.exit(0)

    def handle_admin_login(self):
        """Admin authentication prompt."""
        print_header("ADMINISTRATOR LOGIN", width=50)
        username = input("Username: ").strip()
        if not username:
            print_error("Username cannot be empty.")
            pause_for_user()
            return

        password = get_hidden_input("Password: ")
        if not password:
            print_error("Password cannot be empty.")
            pause_for_user()
            return

        success, msg, _ = self.auth_service.login_admin(username, password)
        if success:
            print_success("Welcome, Administrator!")
            self.admin_menu.display()
        else:
            print_error(msg)
            pause_for_user()

    def handle_customer_login(self):
        """Customer authentication prompt."""
        print_header("CUSTOMER LOGIN", width=50)
        username = input("Username: ").strip()
        if not username:
            print_error("Username cannot be empty.")
            pause_for_user()
            return

        password = get_hidden_input("Password: ")
        if not password:
            print_error("Password cannot be empty.")
            pause_for_user()
            return

        success, msg, _ = self.auth_service.login_customer(username, password)
        if success:
            print_success("Login successful!")
            self.customer_menu.display()
        else:
            print_error(msg)
            pause_for_user()

    def handle_customer_registration(self):
        """Customer self-registration portal."""
        print_header("CUSTOMER REGISTRATION", width=60)
        print("Please provide the required information below.\n")

        # 1. Full Name
        while True:
            name_input = input("Full Name: ").strip()
            valid, res = validate_full_name(name_input)
            if valid:
                full_name = res
                break
            print_error(res)

        # 2. CNIC
        while True:
            cnic_input = input("CNIC / National ID (e.g. 42101-1234567-1): ").strip()
            valid, res = validate_cnic(cnic_input)
            if valid:
                cnic = res
                break
            print_error(res)

        # 3. Phone
        while True:
            phone_input = input("Phone Number (e.g. 03001234567): ").strip()
            valid, res = validate_phone(phone_input)
            if valid:
                phone = res
                break
            print_error(res)

        # 4. Email
        while True:
            email_input = input("Email Address: ").strip()
            valid, res = validate_email(email_input)
            if valid:
                email = res
                break
            print_error(res)

        # 5. Address
        while True:
            addr_input = input("Residential Address: ").strip()
            valid, res = validate_address(addr_input)
            if valid:
                address = res
                break
            print_error(res)

        # 6. Date of Birth
        while True:
            dob_input = input("Date of Birth (YYYY-MM-DD): ").strip()
            valid, res = validate_date_of_birth(dob_input)
            if valid:
                dob = res
                break
            print_error(res)

        # 7. Username
        while True:
            user_input = input("Desired Username: ").strip()
            valid, res = validate_username(user_input)
            if valid:
                username = res
                break
            print_error(res)

        # 8. Password
        while True:
            pwd = get_hidden_input("Password: ")
            valid, msg = validate_password(pwd)
            if not valid:
                print_error(msg)
                continue
            confirm = get_hidden_input("Confirm Password: ")
            if pwd != confirm:
                print_error("Passwords do not match. Please try again.")
                continue
            break

        print_sub_header("Review Registration Details", width=60)
        print(f" Full Name   : {full_name}")
        print(f" CNIC        : {cnic}")
        print(f" Phone       : {phone}")
        print(f" Email       : {email}")
        print(f" Address     : {address}")
        print(f" DOB         : {dob}")
        print(f" Username    : {username}")
        print_separator(60)

        if not prompt_confirmation("Submit customer registration? (Y/N): "):
            print_warning("Registration cancelled.")
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
            password=pwd
        )

        if success:
            print_success(f"{msg}\nYour Customer ID is #{new_id}. You can now log in using option 2.")
        else:
            print_error(msg)

        pause_for_user()

    def handle_exit(self):
        """Displays exit message and terminates cleanly."""
        print_separator(50)
        print("\nThank you for using Bank Management System.")
        print("\nGoodbye!\n")
        print_separator(50)
