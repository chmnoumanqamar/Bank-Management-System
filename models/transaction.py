"""
Transaction Data Model.
Encapsulates financial transaction logs and metadata.
"""

from decimal import Decimal
from typing import Optional, Dict, Any
from config import TRANSACTION_STATUS_COMPLETED

class Transaction:
    """Represents a financial transaction log."""

    def __init__(
        self,
        id: Optional[int],
        transaction_id: str,
        account_id: int,
        transaction_type: str,
        amount: Decimal,
        balance_before: Decimal,
        balance_after: Decimal,
        description: Optional[str] = None,
        related_account: Optional[str] = None,
        transaction_date: Optional[str] = None,
        status: str = TRANSACTION_STATUS_COMPLETED
    ):
        self.id = id
        self.transaction_id = transaction_id
        self.account_id = account_id
        self.transaction_type = transaction_type
        self.amount = amount if isinstance(amount, Decimal) else Decimal(str(amount))
        self.balance_before = balance_before if isinstance(balance_before, Decimal) else Decimal(str(balance_before))
        self.balance_after = balance_after if isinstance(balance_after, Decimal) else Decimal(str(balance_after))
        self.description = description
        self.related_account = related_account
        self.transaction_date = transaction_date
        self.status = status

    @classmethod
    def from_row(cls, row: Any) -> "Transaction":
        """Constructs a Transaction instance from a sqlite3.Row."""
        return cls(
            id=row["id"],
            transaction_id=row["transaction_id"],
            account_id=row["account_id"],
            transaction_type=row["transaction_type"],
            amount=Decimal(str(row["amount"])),
            balance_before=Decimal(str(row["balance_before"])),
            balance_after=Decimal(str(row["balance_after"])),
            description=row["description"],
            related_account=row["related_account"],
            transaction_date=row["transaction_date"],
            status=row["status"]
        )

    def to_dict(self) -> Dict[str, Any]:
        """Returns dictionary representation of Transaction."""
        return {
            "id": self.id,
            "transaction_id": self.transaction_id,
            "account_id": self.account_id,
            "transaction_type": self.transaction_type,
            "amount": str(self.amount),
            "balance_before": str(self.balance_before),
            "balance_after": str(self.balance_after),
            "description": self.description,
            "related_account": self.related_account,
            "transaction_date": self.transaction_date,
            "status": self.status
        }

    def __repr__(self) -> str:
        return f"<Transaction id={self.transaction_id} type={self.transaction_type} amt={self.amount}>"
