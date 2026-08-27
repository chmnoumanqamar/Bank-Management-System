"""
Customer CLI Menu.
Implements the customer portal: Profile, Accounts, Balance Inquiries,
Deposits, Withdrawals, Transfers, Transaction History, and Password updates.
"""

from decimal import Decimal
from typing import List, Optional

from services.auth_service import AuthService
from services.customer_service import CustomerService
from services.account_service import AccountService
from services.transaction_service import TransactionService
from models.customer import Customer
from models.account import Account
from utils.security import get_hidden_input
from utils.validators import (
    validate_phone,
    validate_email,
    validate_address,
    validate_amount,
    validate_account_number,
    validate_password
)
from utils.helpers import (
    print_header,
    print_sub_header,
    print_separator,
    print_double_separator,
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
    TRANSACTION_TYPE_DEPOSIT,
    TRANSACTION_TYPE_WITHDRAWAL,
    TRANSACTION_TYPE_TRANSFER,
    TRANSACTION_TYPE_TRANSFER_RECEIVED,
    ACCOUNT_STATUS_ACTIVE,
    MIN_TRANSACTION_AMOUNT
)

class CustomerMenu:
    """Handles Customer operations, accounts, and financial transactions."""

    def __init__(
        self,
        auth_service: AuthService,
        customer_service: CustomerService,
        account_service: AccountService,
        transaction_service: TransactionService
    ):
        self.auth_service = auth_service
        self.customer_service = customer_service
        self.account_service = account_service
        self.transaction_service = transaction_service

    def display(self):
        """Customer dashboard main loop."""
        while self.auth_service.is_authenticated and self.auth_service.current_role == "CUSTOMER":
            customer: Customer = self.auth_service.current_user
            # Refresh customer details from database in case updated
            refreshed = self.customer_service.get_customer_by_id(customer.id)
            if refreshed:
                customer = refreshed
                self.auth_service.current_user = refreshed

            print_header("CUSTOMER DASHBOARD", width=60)
            print(f" Welcome, {customer.full_name}\n")
            print(" 1. My Profile")
            print(" 2. My Accounts")
            print(" 3. Check Balance")
            print(" 4. Deposit Money")
            print(" 5. Withdraw Money")
            print(" 6. Transfer Money")
            print(" 7. Transaction History")
            print(" 8. Change Password")
            print(" 9. Logout")
            print_separator(60)

            choice = input("Enter your choice (1-9): ").strip()

            if choice == "1":
                self.view_profile(customer)
            elif choice == "2":
                self.view_accounts(customer)
            elif choice == "3":
                self.check_balance(customer)
            elif choice == "4":
                self.deposit_money(customer)
            elif choice == "5":
                self.withdraw_money(customer)
            elif choice == "6":
                self.transfer_money(customer)
            elif choice == "7":
                self.transaction_history(customer)
            elif choice == "8":
                self.change_password(customer)
            elif choice == "9":
                self.auth_service.logout()
                print_success("You have been successfully logged out.")
                pause_for_user()
                break
            else:
                print_error("Invalid option. Please choose a number between 1 and 9.")
                pause_for_user()

    def view_profile(self, customer: Customer):
        """Displays customer profile and allows modifying contact details."""
        print_header("MY PROFILE", width=60)
        print(f" Customer ID    : {customer.id}")
        print(f" Full Name      : {customer.full_name}")
        print(f" CNIC           : {customer.cnic}")
        print(f" Phone Number   : {customer.phone}")
        print(f" Email Address  : {customer.email}")
        print(f" Address        : {customer.address}")
        print(f" Date of Birth  : {customer.date_of_birth}")
        print(f" Username       : {customer.username}")
        print(f" Account Status : {customer.status}")
        print(f" Member Since   : {format_date_pretty(customer.created_at)}")
        print_separator(60)

        print("Options: 1. Update Contact Details | 2. Back")
        p_choice = input("Enter choice (1 or 2): ").strip()

        if p_choice == "1":
            print_sub_header("Update Contact Information", width=60)
            print("Leave blank to keep existing value.\n")

            new_phone_input = input(f"New Phone [{customer.phone}]: ").strip()
            new_phone = None
            if new_phone_input:
                valid, res = validate_phone(new_phone_input)
                if not valid:
                    print_error(res)
                    pause_for_user()
                    return
                new_phone = res

            new_email_input = input(f"New Email [{customer.email}]: ").strip()
            new_email = None
            if new_email_input:
                valid, res = validate_email(new_email_input)
                if not valid:
                    print_error(res)
                    pause_for_user()
                    return
                new_email = res

            new_addr_input = input(f"New Address [{customer.address}]: ").strip()
            new_addr = None
            if new_addr_input:
                valid, res = validate_address(new_addr_input)
                if not valid:
                    print_error(res)
                    pause_for_user()
                    return
                new_addr = res

            if not any([new_phone, new_email, new_addr]):
                print_info("No changes were made.")
                pause_for_user()
                return

            if prompt_confirmation("Confirm update of your contact details? (Y/N): "):
                success, msg = self.customer_service.update_customer_profile(
                    customer_id=customer.id,
                    phone=new_phone,
                    email=new_email,
                    address=new_addr
                )
                if success:
                    print_success(msg)
                else:
                    print_error(msg)
            else:
                print_info("Update cancelled.")
        pause_for_user()

    def view_accounts(self, customer: Customer):
        """Displays all bank accounts owned by the customer."""
        print_header("MY BANK ACCOUNTS", width=60)
        accounts = self.account_service.get_accounts_by_customer_id(customer.id)

        if not accounts:
            print_warning("You do not have any registered bank accounts.")
            pause_for_user()
            return

        headers = ["Account Number", "Type", "Status", "Balance", "Opening Date"]
        rows = [
            [
                a.account_number,
                a.account_type,
                a.status,
                format_currency(a.balance),
                format_date_pretty(a.created_at)
            ]
            for a in accounts
        ]
        print_table(headers, rows)
        pause_for_user()

    def _select_customer_account(
        self,
        customer: Customer,
        active_only: bool = True
    ) -> Optional[Account]:
        """Helper to let a customer pick one of their accounts from a menu."""
        accounts = self.account_service.get_accounts_by_customer_id(customer.id)

        if active_only:
            accounts = [a for a in accounts if a.is_active]

        if not accounts:
            if active_only:
                print_error("You do not have any Active accounts available for this operation.")
            else:
                print_error("No accounts found.")
            return None

        if len(accounts) == 1:
            return accounts[0]

        print("\nSelect Account:")
        for idx, acc in enumerate(accounts, start=1):
            print(f" {idx}. Account: {acc.account_number} ({acc.account_type}) | Balance: {format_currency(acc.balance)} | Status: {acc.status}")

        while True:
            choice = input(f"Enter account choice (1-{len(accounts)}): ").strip()
            if choice.isdigit() and 1 <= int(choice) <= len(accounts):
                return accounts[int(choice) - 1]
            print_error(f"Please enter a number between 1 and {len(accounts)}.")

    def check_balance(self, customer: Customer):
        """Performs a balance inquiry on a customer account."""
        print_header("BALANCE INQUIRY", width=60)
        account = self._select_customer_account(customer, active_only=False)
        if not account:
            pause_for_user()
            return

        # Fetch fresh account balance
        fresh_acc = self.account_service.get_account_by_number(account.account_number)
        if not fresh_acc:
            print_error("Unable to retrieve account details.")
            pause_for_user()
            return

        print_header("ACCOUNT DETAILS", width=50)
        print(f" Account Number : {fresh_acc.account_number}")
        print(f" Account Type   : {fresh_acc.account_type}")
        print(f" Status         : {fresh_acc.status}")
        print(f" Current Balance: {format_currency(fresh_acc.balance)}")
        print(f" Created On     : {format_date_pretty(fresh_acc.created_at)}")
        print_separator(50)
        pause_for_user()

    def deposit_money(self, customer: Customer):
        """Handles deposit into a customer's active account."""
        print_header("DEPOSIT MONEY", width=60)
        account = self._select_customer_account(customer, active_only=True)
        if not account:
            pause_for_user()
            return

        # Fetch latest balance
        fresh_acc = self.account_service.get_account_by_number(account.account_number)
        if not fresh_acc or not fresh_acc.is_active:
            print_error(f"Account {account.account_number} is not active for deposits.")
            pause_for_user()
            return

        while True:
            amt_str = input(f"Enter deposit amount (Min {format_currency(MIN_TRANSACTION_AMOUNT)}): ").strip()
            valid, amount, msg = validate_amount(amt_str, min_val=MIN_TRANSACTION_AMOUNT)
            if valid:
                break
            print_error(msg)

        current_balance = fresh_acc.balance
        new_balance = current_balance + amount

        print_sub_header("Deposit Confirmation", width=50)
        print(f" Account Number : {fresh_acc.account_number}")
        print(f" Current Balance: {format_currency(current_balance)}")
        print(f" Deposit Amount : {format_currency(amount)}")
        print(f" New Balance    : {format_currency(new_balance)}")
        print_separator(50)

        if not prompt_confirmation("\nConfirm deposit? (Y/N): "):
            print_warning("Deposit transaction cancelled.")
            pause_for_user()
            return

        success, msg, txn_data = self.transaction_service.deposit(
            account_number=fresh_acc.account_number,
            amount=amount,
            description="Self Cash Deposit"
        )

        if success and txn_data:
            print_success("Deposit successful.")
            print(f"\n Transaction ID: {txn_data['transaction_id']}")
            print(f" Amount        : {format_currency(txn_data['amount'])}")
            print(f" New Balance   : {format_currency(txn_data['balance_after'])}")
        else:
            print_error(msg)

        pause_for_user()

    def withdraw_money(self, customer: Customer):
        """Handles withdrawal from a customer's active account."""
        print_header("WITHDRAW MONEY", width=60)
        account = self._select_customer_account(customer, active_only=True)
        if not account:
            pause_for_user()
            return

        fresh_acc = self.account_service.get_account_by_number(account.account_number)
        if not fresh_acc or not fresh_acc.is_active:
            print_error(f"Account {account.account_number} is not active for withdrawals.")
            pause_for_user()
            return

        while True:
            amt_str = input(f"Enter withdrawal amount (Min {format_currency(MIN_TRANSACTION_AMOUNT)}): ").strip()
            valid, amount, msg = validate_amount(amt_str, min_val=MIN_TRANSACTION_AMOUNT)
            if valid:
                break
            print_error(msg)

        current_balance = fresh_acc.balance

        if current_balance < amount:
            print_error(
                f"Transaction failed.\n\n"
                f"Insufficient balance.\n"
                f"Current Balance: {format_currency(current_balance)}\n"
                f"Requested Amount: {format_currency(amount)}"
            )
            pause_for_user()
            return

        remaining_balance = current_balance - amount

        print_sub_header("Withdrawal Confirmation", width=50)
        print(f" Account Number    : {fresh_acc.account_number}")
        print(f" Current Balance   : {format_currency(current_balance)}")
        print(f" Withdrawal Amount : {format_currency(amount)}")
        print(f" Remaining Balance : {format_currency(remaining_balance)}")
        print_separator(50)

        if not prompt_confirmation("\nConfirm withdrawal? (Y/N): "):
            print_warning("Withdrawal transaction cancelled.")
            pause_for_user()
            return

        success, msg, txn_data = self.transaction_service.withdraw(
            account_number=fresh_acc.account_number,
            amount=amount,
            description="Self Cash Withdrawal"
        )

        if success and txn_data:
            print_success("Withdrawal successful.")
            print(f"\n Transaction ID    : {txn_data['transaction_id']}")
            print(f" Amount           : {format_currency(txn_data['amount'])}")
            print(f" Remaining Balance: {format_currency(txn_data['balance_after'])}")
        else:
            print_error(msg)

        pause_for_user()

    def transfer_money(self, customer: Customer):
        """Handles inter-account transfers with atomic rollback guarantees."""
        print_header("TRANSFER MONEY", width=60)
        src_account = self._select_customer_account(customer, active_only=True)
        if not src_account:
            pause_for_user()
            return

        fresh_src = self.account_service.get_account_by_number(src_account.account_number)
        if not fresh_src or not fresh_src.is_active:
            print_error(f"Source account {src_account.account_number} is not active for transfers.")
            pause_for_user()
            return

        # 1. Destination Account Number
        while True:
            dst_acc_input = input("Enter Destination 10-Digit Account Number: ").strip()
            valid, res = validate_account_number(dst_acc_input)
            if not valid:
                print_error(res)
                continue
            if res == fresh_src.account_number:
                print_error("Source and destination accounts cannot be identical.")
                continue
            dst_acc = self.account_service.get_account_by_number(res)
            if not dst_acc:
                print_error(f"Destination account '{res}' does not exist.")
                continue
            if not dst_acc.is_active:
                print_error(f"Destination account '{res}' is currently {dst_acc.status} and cannot receive transfers.")
                continue
            destination_account = dst_acc
            break

        # 2. Transfer Amount
        while True:
            amt_str = input(f"Enter transfer amount (Min {format_currency(MIN_TRANSACTION_AMOUNT)}): ").strip()
            valid, amount, msg = validate_amount(amt_str, min_val=MIN_TRANSACTION_AMOUNT)
            if valid:
                break
            print_error(msg)

        if fresh_src.balance < amount:
            print_error(
                f"Transfer failed.\n\n"
                f"Insufficient balance in source account.\n"
                f"Available Balance: {format_currency(fresh_src.balance)}\n"
                f"Transfer Amount  : {format_currency(amount)}"
            )
            pause_for_user()
            return

        description = input("Enter transfer note/description (optional): ").strip()

        print_sub_header("TRANSFER CONFIRMATION", width=50)
        print(f" From Account : {fresh_src.account_number}")
        print(f" To Account   : {destination_account.account_number}")
        print(f" Amount       : {format_currency(amount)}")
        if description:
            print(f" Note         : {description}")
        print_separator(50)

        if not prompt_confirmation("\nConfirm transfer? (Y/N): "):
            print_warning("Transfer cancelled.")
            pause_for_user()
            return

        success, msg, txn_data = self.transaction_service.transfer(
            source_account_number=fresh_src.account_number,
            destination_account_number=destination_account.account_number,
            amount=amount,
            description=description or "Inter-account Transfer"
        )

        if success and txn_data:
            print_success("Transfer completed successfully.")
            print(f"\n Transaction ID     : {txn_data['sender_txn_id']}")
            print(f" Transferred Amount : {format_currency(txn_data['amount'])}")
            print(f" Remaining Balance  : {format_currency(txn_data['new_source_balance'])}")
        else:
            print_error(msg)

        pause_for_user()

    def transaction_history(self, customer: Customer):
        """Displays filtered transaction statement for customer accounts."""
        print_header("TRANSACTION HISTORY", width=60)
        account = self._select_customer_account(customer, active_only=False)
        if not account:
            pause_for_user()
            return

        print_sub_header(f"Filter Options for Account #{account.account_number}", width=60)
        print(" 1. View All Transactions")
        print(" 2. Deposits Only")
        print(" 3. Withdrawals Only")
        print(" 4. Transfers Only")
        print(" 5. Search by Transaction ID")
        print(" 6. Back")

        choice = input("\nEnter choice (1-6): ").strip()
        txn_type = None
        search_txn_id = None

        if choice == "1":
            pass
        elif choice == "2":
            txn_type = TRANSACTION_TYPE_DEPOSIT
        elif choice == "3":
            txn_type = TRANSACTION_TYPE_WITHDRAWAL
        elif choice == "4":
            # Show both outgoing and incoming transfers
            txn_type = None  # Will filter in memory or fetch both
        elif choice == "5":
            search_txn_id = input("Enter Transaction ID keyword: ").strip()
        elif choice == "6":
            return
        else:
            print_error("Invalid option.")
            pause_for_user()
            return

        transactions = self.transaction_service.get_transactions_for_account(
            account_id=account.id,
            txn_type=txn_type,
            search_txn_id=search_txn_id
        )

        if choice == "4":
            transactions = [
                t for t in transactions
                if t.transaction_type in [TRANSACTION_TYPE_TRANSFER, TRANSACTION_TYPE_TRANSFER_RECEIVED]
            ]

        print_header(f"STATEMENT FOR ACCOUNT {account.account_number}", width=70)
        headers = ["Transaction ID", "Type", "Amount", "Balance", "Related Acc", "Date & Time"]
        rows = [
            [
                t.transaction_id,
                t.transaction_type,
                format_currency(t.amount),
                format_currency(t.balance_after),
                t.related_account or "-",
                format_date_pretty(t.transaction_date)
            ]
            for t in transactions
        ]

        print_table(headers, rows)
        pause_for_user()

    def change_password(self, customer: Customer):
        """Allows customer to change their login password."""
        print_header("CHANGE PASSWORD", width=60)

        current_pwd = get_hidden_input("Enter Current Password: ")
        if not current_pwd:
            print_error("Current password cannot be empty.")
            pause_for_user()
            return

        while True:
            new_pwd = get_hidden_input("Enter New Password: ")
            valid, msg = validate_password(new_pwd)
            if not valid:
                print_error(msg)
                continue
            confirm_pwd = get_hidden_input("Confirm New Password: ")
            if new_pwd != confirm_pwd:
                print_error("Passwords do not match. Please try again.")
                continue
            break

        if not prompt_confirmation("\nConfirm password update? (Y/N): "):
            print_warning("Password update cancelled.")
            pause_for_user()
            return

        success, msg = self.auth_service.change_customer_password(
            customer_id=customer.id,
            current_password=current_pwd,
            new_password=new_pwd
        )

        if success:
            print_success(msg)
        else:
            print_error(msg)

        pause_for_user()
