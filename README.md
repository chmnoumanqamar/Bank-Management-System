# Bank Management System — CLI Based (Python & SQLite3)

A professional, secure, menu-driven **Bank Management System** developed in Python 3 using SQLite3 and Object-Oriented Architecture. Designed for academic and semester project excellence, adhering to rigorous financial security and software engineering standards.

---

## 📌 Project Overview

The **Bank Management System** is a standalone, terminal-based banking solution that enables bank administrators and customers to perform essential and advanced financial operations safely. The application features double-entry bookkeeping principles, atomic transaction management with rollback guarantees, PBKDF2 password hashing, and exact `Decimal` precision arithmetic.

---

## 🌟 Key Features

### 👨‍💼 Administrator Portal
- **Real-Time Dynamic Dashboard**: Live counts of total customers, total accounts, active/frozen/closed status breakdowns, total bank vault balance, cumulative deposits, and cumulative withdrawals.
- **Customer Lifecycle Management**:
  - Register new customers with Pakistani format validations (CNIC, mobile number, email, date of birth).
  - Search customers across ID, Name, CNIC, Phone, or Username.
  - Update profile details (Name, Phone, Email, Address).
  - Block & Unblock customer accounts (preventing unauthorized login).
  - Delete settled customers (safeguards prevent deleting active or non-zero balance accounts).
- **Account Operations**:
  - Automatically generate unique 10-digit sequential account numbers (`1000000001`, `1000000002`, ...).
  - Create Savings and Current accounts with initial opening deposit.
  - Freeze & Unfreeze accounts (frozen accounts cannot perform transactions).
  - Close accounts (enforces zero-balance rule before closure).
  - Comprehensive account search and audit views.
- **Transaction Auditing**:
  - Inspect bank-wide transaction logs with filters by Transaction Type (Deposit, Withdrawal, Transfer) or keyword search.
- **Analytics & CSV Export**:
  - Generates formatted statistical reports for Customers, Accounts, Financials, and Transactions.
  - One-click CSV report exporter (`customers_report.csv`, `accounts_report.csv`, `transactions_report.csv`).

### 👤 Customer Portal
- **Self-Registration & Secure Login**: Full input validation, hidden password entry, and automatic profile activation.
- **Profile Management**: View personal data and update contact information (phone, email, address).
- **Account Overview & Balance Inquiry**: Inspect real-time balance formatted in PKR currency (`Rs. 50,000.00`).
- **Deposit Money**: Deposit funds into active accounts with before/after balance previews and instant receipt logs.
- **Withdraw Money**: Secure cash withdrawal with balance sufficiency verification.
- **Inter-Account Money Transfer**:
  - Transfer funds to any 10-digit bank account.
  - Double-entry atomic transaction: debits sender, credits recipient, and writes dual audit records in a single database transaction.
  - Complete rollback on transfer failure.
- **Transaction Statement**: View full account statements or filter by Deposits, Withdrawals, Transfers, or Transaction ID.
- **Password Management**: Change customer password with existing password verification and PBKDF2 re-hashing.

---

## 🔒 Security & Financial Reliability

1. **Password Hashing (PBKDF2-HMAC-SHA256)**:
   - Passwords are never stored in plain text.
   - Uses 100,000 iterations with 32-byte cryptographic random salts (`secrets.token_hex(32)`).
   - Verifies hashes in constant time using `hmac.compare_digest` to prevent timing attacks.
2. **Hidden Terminal Input**:
   - Passwords are typed invisibly using Python's `getpass` module.
3. **Parameterized SQL Queries**:
   - 100% of database queries use parameterized placeholders (`?`), completely preventing SQL injection vulnerabilities.
4. **Exact Decimal Monetary Arithmetic**:
   - All financial calculations use Python's built-in `decimal.Decimal` quantized to 2 decimal places to eliminate floating-point rounding errors.
5. **Database Transaction Integrity**:
   - Uses SQLite `PRAGMA foreign_keys = ON;` and context-managed transactions.
   - If any step in a multi-step operation (like a transfer) fails, all database changes are automatically rolled back.
6. **Robust Input Validation**:
   - Pakistan CNIC validation: `XXXXX-XXXXXXX-X`
   - Mobile numbers: Pakistani standard format (`03XXXXXXXXX` or `+923XXXXXXXXX`)
   - RFC-compliant email checking
   - Age verification (minimum 18 years old)
   - Positive numeric amounts with up to 2 decimal places

---

## 🏗️ Project Architecture

```text
Bank management system/
├── config.py                 # Application configuration, constants, and paths
├── database.py               # DatabaseManager: SQLite connection pool, schema, seed data
├── main.py                   # Application entry point with CLI launcher
├── requirements.txt          # Standard library declaration
├── README.md                 # Project documentation and viva guide
├── models/
│   ├── __init__.py
│   ├── customer.py           # Customer entity model
│   ├── account.py            # Account entity model
│   └── transaction.py        # Transaction entity model
├── services/
│   ├── __init__.py
│   ├── auth_service.py       # Admin & Customer login, session state
│   ├── customer_service.py   # Customer CRUD, search, blocking, updates
│   ├── account_service.py    # Account generation, freeze, unfreeze, close
│   └── transaction_service.py# Deposits, withdrawals, atomic transfers
├── reports/
│   ├── __init__.py
│   └── report_generator.py   # Statistical dashboards and CSV export
├── cli/
│   ├── __init__.py
│   ├── main_menu.py          # Entry CLI dispatcher and registration
│   ├── admin_menu.py         # Administrator workflow menus
│   └── customer_menu.py      # Customer dashboard and financial menus
├── utils/
│   ├── __init__.py
│   ├── security.py           # PBKDF2 hashing and hidden input
│   ├── validators.py         # Regex and business validators
│   ├── helpers.py            # CLI ASCII tables, banners, formatters
│   └── logger.py             # Event audit logger (bank_management.log)
└── tests/
    ├── __init__.py
    └── test_banking_system.py# Comprehensive automated test suite
```

---

## 🗄️ Database Schema (`bank_management.db`)

### 1. `admins`
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Unique Admin ID |
| `username` | TEXT | UNIQUE, NOT NULL | Admin login username |
| `password_hash` | TEXT | NOT NULL | PBKDF2-HMAC-SHA256 hex string |
| `salt` | TEXT | NOT NULL | 32-byte hex salt |
| `full_name` | TEXT | NOT NULL | Administrator's name |
| `email` | TEXT | NOT NULL | Contact email |
| `created_at` | TEXT | NOT NULL | Timestamp |

### 2. `customers`
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Unique Customer ID |
| `full_name` | TEXT | NOT NULL | Customer full name |
| `cnic` | TEXT | UNIQUE, NOT NULL | Format: `XXXXX-XXXXXXX-X` |
| `phone` | TEXT | NOT NULL | Mobile number |
| `email` | TEXT | UNIQUE, NOT NULL | Email address |
| `address` | TEXT | NOT NULL | Residential address |
| `date_of_birth` | TEXT | NOT NULL | `YYYY-MM-DD` |
| `username` | TEXT | UNIQUE, NOT NULL | Login username |
| `password_hash` | TEXT | NOT NULL | PBKDF2 hash |
| `salt` | TEXT | NOT NULL | Unique salt |
| `status` | TEXT | NOT NULL DEFAULT 'Active' | `Active` or `Blocked` |
| `created_at` | TEXT | NOT NULL | Timestamp |

### 3. `accounts`
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Internal Account ID |
| `account_number` | TEXT | UNIQUE, NOT NULL | 10-digit number (`1000000001`) |
| `customer_id` | INTEGER | REFERENCES customers(id) | Foreign key to customer |
| `account_type` | TEXT | NOT NULL | `Savings` or `Current` |
| `balance` | TEXT | NOT NULL | Exact string representation of Decimal |
| `status` | TEXT | NOT NULL DEFAULT 'Active' | `Active`, `Frozen`, or `Closed` |
| `created_at` | TEXT | NOT NULL | Creation timestamp |
| `closed_at` | TEXT | NULL | Closure timestamp |

### 4. `transactions`
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Internal Log ID |
| `transaction_id` | TEXT | UNIQUE, NOT NULL | Format: `TXNYYYYMMDDXXXX` |
| `account_id` | INTEGER | REFERENCES accounts(id) | Foreign key to account |
| `transaction_type`| TEXT | NOT NULL | `Deposit`, `Withdrawal`, `Transfer`, `Transfer Received` |
| `amount` | TEXT | NOT NULL | Exact Decimal string |
| `balance_before` | TEXT | NOT NULL | Balance prior to transaction |
| `balance_after` | TEXT | NOT NULL | Balance post transaction |
| `description` | TEXT | NULL | Note or remarks |
| `related_account`| TEXT | NULL | Counterparty account for transfers |
| `transaction_date`| TEXT | NOT NULL | Timestamp |
| `status` | TEXT | NOT NULL DEFAULT 'Completed'| Transaction status |

---

## 🚀 Getting Started

### Prerequisites
- Python 3.8 or higher installed on your system.
- Zero external package installation required (100% Python standard library).

### Running the Application

1. Open your terminal / command prompt and navigate to the project directory:
   ```bash
   cd "Bank management system"
   ```

2. Run the application:
   ```bash
   python main.py
   ```

---

## 🔑 Demo Credentials (For Testing & Evaluation)

When the program runs for the first time, demo accounts are automatically seeded into the database:

### 1. Administrator Account
- **Username**: `admin`
- **Password**: `admin123`

### 2. Demo Customer 1
- **Username**: `m_ali`
- **Password**: `customer123`
- **Account Number**: `1000000001` (Savings, Initial Balance: `Rs. 50,000.00`)

### 3. Demo Customer 2
- **Username**: `f_zahra`
- **Password**: `customer123`
- **Account Number**: `1000000002` (Current, Initial Balance: `Rs. 75,000.00`)

---

## 🧪 Running Automated Tests

A complete unit and integration test suite is included to verify all 58 banking rules, security hashing, input validation, double-entry transfers, and atomic rollbacks.

To run the tests:
```bash
python -m unittest discover -s tests -p "test_*.py"
```

---

## 🎓 Academic / Viva Presentation Guide

When presenting this project for an academic defense, semester viva, or code walkthrough:

1. **Why SQLite over text/JSON files?**
   - SQLite provides ACID (Atomicity, Consistency, Isolation, Durability) guarantees, relational integrity via foreign keys, and SQL indexing for fast query performance.
2. **Why Python's `Decimal` instead of `float`?**
   - Floating-point representations (IEEE 754) suffer from binary representation errors (e.g. `0.1 + 0.2 = 0.30000000000000004`), which can cause financial discrepancies. `Decimal` guarantees exact base-10 arithmetic.
3. **How does Transfer Atomicity work?**
   - Transfers are executed inside a single `with db.transaction():` block. If debiting the sender succeeds but crediting the receiver fails (e.g., receiver account is frozen), the context manager triggers a `ROLLBACK`, ensuring money is never lost or partially deducted.
4. **How are passwords protected?**
   - Using PBKDF2-HMAC-SHA256 with individual cryptographic salts and 100,000 hashing rounds. Raw passwords are never stored or printed in logs.

---

## 🔮 Future Enhancements
- Two-Factor Authentication (2FA) via TOTP / SMS OTP.
- Graphical Desktop GUI (PyQt / CustomTkinter) or Modern Web Portal (FastAPI / React).
- Automated scheduled interest calculation for Savings accounts.
- ATM card PIN generation and virtual card management.
- Multi-currency support and real-time forex exchange rates.
