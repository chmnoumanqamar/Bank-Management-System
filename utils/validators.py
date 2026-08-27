"""
Validation Module for Bank Management System.
Contains strict, reusable validation functions for all customer and transaction inputs.
"""

import re
from datetime import datetime, date
from decimal import Decimal, InvalidOperation
from typing import Tuple, Optional

# Regular Expressions
CNIC_REGEX = re.compile(r"^\d{5}-\d{7}-\d{1}$")
PHONE_REGEX = re.compile(r"^(?:\+92|0092|0)?(3\d{2})[- ]?(\d{7})$")
EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
USERNAME_REGEX = re.compile(r"^[a-zA-Z0-9_]{3,20}$")
ACCOUNT_NUMBER_REGEX = re.compile(r"^\d{10}$")

def validate_full_name(name: str) -> Tuple[bool, str]:
    """Validates person's full name."""
    if not name or not name.strip():
        return False, "Full Name cannot be empty."
    cleaned = name.strip()
    if len(cleaned) < 2 or len(cleaned) > 50:
        return False, "Full Name must be between 2 and 50 characters."
    if not re.match(r"^[a-zA-Z\s.'-]+$", cleaned):
        return False, "Full Name can only contain letters, spaces, dots, hyphens, and apostrophes."
    return True, cleaned

def validate_cnic(cnic: str) -> Tuple[bool, str]:
    """
    Validates Pakistani CNIC format: XXXXX-XXXXXXX-X (13 digits with hyphens).
    Also normalizes unhyphenated 13 digits if provided.
    """
    if not cnic or not cnic.strip():
        return False, "CNIC cannot be empty."
    cleaned = cnic.strip()
    
    # If 13 pure digits are given, format them
    if re.match(r"^\d{13}$", cleaned):
        cleaned = f"{cleaned[:5]}-{cleaned[5:12]}-{cleaned[12]}"
        
    if not CNIC_REGEX.match(cleaned):
        return False, "Invalid CNIC format. Required format: XXXXX-XXXXXXX-X (e.g., 42101-1234567-1)."
    return True, cleaned

def validate_phone(phone: str) -> Tuple[bool, str]:
    """
    Validates Pakistani mobile numbers.
    Normalizes to 03XXXXXXXXX format.
    """
    if not phone or not phone.strip():
        return False, "Phone number cannot be empty."
    cleaned = phone.strip()
    match = PHONE_REGEX.match(cleaned)
    if not match:
        return False, "Invalid Pakistani phone number. Format example: 03001234567 or +923001234567."
    normalized = f"0{match.group(1)}{match.group(2)}"
    return True, normalized

def validate_email(email: str) -> Tuple[bool, str]:
    """Validates email format."""
    if not email or not email.strip():
        return False, "Email address cannot be empty."
    cleaned = email.strip().lower()
    if not EMAIL_REGEX.match(cleaned):
        return False, "Invalid email address format (e.g., user@example.com)."
    return True, cleaned

def validate_address(address: str) -> Tuple[bool, str]:
    """Validates physical residential address."""
    if not address or not address.strip():
        return False, "Address cannot be empty."
    cleaned = address.strip()
    if len(cleaned) < 5 or len(cleaned) > 150:
        return False, "Address must be between 5 and 150 characters."
    return True, cleaned

def validate_date_of_birth(dob_str: str) -> Tuple[bool, str]:
    """
    Validates Date of Birth format (YYYY-MM-DD) and checks that customer is at least 18 years old.
    """
    if not dob_str or not dob_str.strip():
        return False, "Date of birth cannot be empty."
    cleaned = dob_str.strip()
    try:
        dob = datetime.strptime(cleaned, "%Y-%m-%d").date()
    except ValueError:
        return False, "Invalid date format. Required format is YYYY-MM-DD (e.g., 1995-08-25)."
    
    today = date.today()
    if dob >= today:
        return False, "Date of birth cannot be today or in the future."
    
    # Calculate age
    age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
    if age < 18:
        return False, f"Customer must be at least 18 years old. Calculated age: {age} years."
    if age > 120:
        return False, f"Please enter a realistic date of birth (age {age} is out of valid range)."
    
    return True, cleaned

def validate_username(username: str) -> Tuple[bool, str]:
    """Validates system username."""
    if not username or not username.strip():
        return False, "Username cannot be empty."
    cleaned = username.strip().lower()
    if not USERNAME_REGEX.match(cleaned):
        return False, "Username must be 3-20 characters long and contain only letters, numbers, and underscores."
    return True, cleaned

def validate_password(password: str) -> Tuple[bool, str]:
    """Validates password strength."""
    if not password:
        return False, "Password cannot be empty."
    if len(password) < 6:
        return False, "Password must be at least 6 characters long."
    if len(password) > 50:
        return False, "Password cannot exceed 50 characters."
    return True, password

def validate_amount(amount_str: str, min_val: Decimal = Decimal("0.01")) -> Tuple[bool, Optional[Decimal], str]:
    """
    Validates monetary input and converts to Decimal.
    Ensures positive value with up to 2 decimal places.
    """
    if not amount_str or not amount_str.strip():
        return False, None, "Amount cannot be empty."
    cleaned = amount_str.strip().replace(",", "")
    
    try:
        val = Decimal(cleaned)
    except (InvalidOperation, ValueError):
        return False, None, "Invalid monetary amount. Must be a valid numeric value."
    
    if val.is_nan() or val.is_infinite():
        return False, None, "Invalid monetary amount."
        
    # Check decimal places
    parts = cleaned.split(".")
    if len(parts) > 1 and len(parts[1]) > 2:
        return False, None, "Amount cannot have more than 2 decimal places."
        
    if val < min_val:
        return False, None, f"Amount must be at least {min_val}."
        
    # Quantize to 2 decimal places
    quantized = val.quantize(Decimal("0.01"))
    return True, quantized, ""

def validate_account_number(acc_num: str) -> Tuple[bool, str]:
    """Validates 10-digit account number format."""
    if not acc_num or not acc_num.strip():
        return False, "Account number cannot be empty."
    cleaned = acc_num.strip()
    if not ACCOUNT_NUMBER_REGEX.match(cleaned):
        return False, "Account number must be exactly 10 digits."
    return True, cleaned
