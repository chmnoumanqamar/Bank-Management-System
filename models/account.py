"""
Account Data Model.
Encapsulates Bank Account attributes, monetary Decimal casting, and status logic.
"""

from decimal import Decimal
from typing import Optional, Dict, Any
from config import ACCOUNT_STATUS_ACTIVE, ACCOUNT_STATUS_FROZEN, ACCOUNT_STATUS_CLOSED

class Account:
    """Represents a Customer Bank Account."""

    def __init__(
        self,
        id: Optional[int],
        account_number: str,
        customer_id: int,
        account_type: str,
        balance: Decimal,
        status: str = ACCOUNT_STATUS_ACTIVE,
        created_at: Optional[str] = None,
        closed_at: Optional[str] = None
    ):
        self.id = id
        self.account_number = str(account_number)
        self.customer_id = customer_id
        self.account_type = account_type
        self.balance = balance if isinstance(balance, Decimal) else Decimal(str(balance))
        self.status = status
        self.created_at = created_at
        self.closed_at = closed_at

    @property
    def is_active(self) -> bool:
        """Returns True if account can perform deposits, withdrawals, and transfers."""
        return self.status == ACCOUNT_STATUS_ACTIVE

    @property
    def is_frozen(self) -> bool:
        """Returns True if account is frozen."""
        return self.status == ACCOUNT_STATUS_FROZEN

    @property
    def is_closed(self) -> bool:
        """Returns True if account is permanently closed."""
        return self.status == ACCOUNT_STATUS_CLOSED

    @classmethod
    def from_row(cls, row: Any) -> "Account":
        """Constructs an Account instance from a sqlite3.Row."""
        return cls(
            id=row["id"],
            account_number=str(row["account_number"]),
            customer_id=row["customer_id"],
            account_type=row["account_type"],
            balance=Decimal(str(row["balance"])),
            status=row["status"],
            created_at=row["created_at"],
            closed_at=row["closed_at"] if "closed_at" in row.keys() else None
        )

    def to_dict(self) -> Dict[str, Any]:
        """Returns dictionary representation of Account."""
        return {
            "id": self.id,
            "account_number": self.account_number,
            "customer_id": self.customer_id,
            "account_type": self.account_type,
            "balance": str(self.balance),
            "status": self.status,
            "created_at": self.created_at,
            "closed_at": self.closed_at
        }

    def __repr__(self) -> str:
        return f"<Account num={self.account_number} type={self.account_type} bal={self.balance} status={self.status}>"
