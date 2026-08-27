"""
CLI Formatting and Helper Functions.
Provides terminal headers, table layout renderers, currency formatters, and confirmation prompts.
"""

import os
from decimal import Decimal, InvalidOperation
from datetime import datetime
from typing import List, Any, Union
from config import CURRENCY_SYMBOL

def format_currency(amount: Union[Decimal, float, str, int]) -> str:
    """Formats a numeric amount into standard currency string: Rs. 12,500.00"""
    if amount is None:
        return f"{CURRENCY_SYMBOL} 0.00"
    try:
        if isinstance(amount, (str, float, int)):
            dec_amount = Decimal(str(amount))
        else:
            dec_amount = amount
        formatted = f"{dec_amount:,.2f}"
        return f"{CURRENCY_SYMBOL} {formatted}"
    except (InvalidOperation, ValueError, TypeError):
        return f"{CURRENCY_SYMBOL} 0.00"

def format_date_pretty(date_str: str) -> str:
    """
    Formats ISO or standard database date strings to reader-friendly format.
    E.g. '2026-08-27 10:15:00' -> '27-Aug-2026 10:15'
    """
    if not date_str:
        return "N/A"
    try:
        # Check if includes time
        if " " in date_str:
            dt = datetime.strptime(date_str.split(".")[0], "%Y-%m-%d %H:%M:%S")
            return dt.strftime("%d-%b-%Y %I:%M %p")
        else:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            return dt.strftime("%d-%b-%Y")
    except Exception:
        return date_str

def print_header(title: str, width: int = 60):
    """Prints a styled primary section header."""
    print()
    print("=" * width)
    print(f"{title.center(width)}")
    print("=" * width)
    print()

def print_sub_header(title: str, width: int = 60):
    """Prints a styled secondary sub-header."""
    print()
    print("-" * width)
    print(f" {title}")
    print("-" * width)

def print_separator(width: int = 60):
    """Prints a single line separator."""
    print("-" * width)

def print_double_separator(width: int = 60):
    """Prints a double line separator."""
    print("=" * width)

def print_success(message: str):
    """Prints a success message."""
    print(f"\n[+] SUCCESS: {message}")

def print_error(message: str):
    """Prints an error message."""
    print(f"\n[!] ERROR: {message}")

def print_warning(message: str):
    """Prints a warning message."""
    print(f"\n[*] WARNING: {message}")

def print_info(message: str):
    """Prints an informational message."""
    print(f"\n[i] INFO: {message}")

def prompt_confirmation(prompt_text: str = "Confirm this action? (Y/N): ") -> bool:
    """
    Repeatedly prompts user for a Yes/No confirmation until 'y' or 'n' is given.
    Returns True for Yes, False for No.
    """
    while True:
        try:
            choice = input(prompt_text).strip().lower()
            if choice in ["y", "yes"]:
                return True
            elif choice in ["n", "no"]:
                return False
            else:
                print("Invalid input. Please enter 'Y' for Yes or 'N' for No.")
        except EOFError:
            return False

def pause_for_user(prompt_text: str = "\nPress Enter to continue..."):
    """Pauses CLI execution until user presses Enter."""
    try:
        input(prompt_text)
    except (EOFError, KeyboardInterrupt):
        pass

def print_table(headers: List[str], rows: List[List[Any]], col_widths: List[int] = None):
    """
    Renders a formatted ASCII table in the CLI terminal.
    Calculates dynamic column widths if not provided.
    """
    if not headers:
        return
        
    str_rows = [[str(cell) if cell is not None else "N/A" for cell in row] for row in rows]
    
    # Calculate widths
    if not col_widths:
        col_widths = [len(h) for h in headers]
        for row in str_rows:
            for idx, cell in enumerate(row):
                if idx < len(col_widths):
                    col_widths[idx] = max(col_widths[idx], len(cell))
        # Add padding
        col_widths = [w + 2 for w in col_widths]
        
    total_width = sum(col_widths) + len(col_widths) + 1
    
    # Header row
    header_line = "|" + "|".join(f" {headers[i].ljust(col_widths[i] - 1)}" for i in range(len(headers))) + "|"
    sep_line = "+" + "+".join("-" * col_widths[i] for i in range(len(headers))) + "+"
    
    print(sep_line)
    print(header_line)
    print(sep_line)
    
    if not str_rows:
        empty_msg = "No records found."
        print(f"| {empty_msg.center(total_width - 4)} |")
        print(sep_line)
        return
        
    for row in str_rows:
        row_str = "|"
        for idx in range(len(headers)):
            cell_val = row[idx] if idx < len(row) else ""
            row_str += f" {cell_val.ljust(col_widths[idx] - 1)}|"
        print(row_str)
        
    print(sep_line)
