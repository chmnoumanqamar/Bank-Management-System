"""
Customer Data Model.
Encapsulates Customer entity attributes, status queries, and row conversions.
"""

from typing import Optional, Dict, Any
from config import CUSTOMER_STATUS_ACTIVE, CUSTOMER_STATUS_BLOCKED

class Customer:
    """Represents a registered Bank Customer."""

    def __init__(
        self,
        id: Optional[int],
        full_name: str,
        cnic: str,
        phone: str,
        email: str,
        address: str,
        date_of_birth: str,
        username: str,
        password_hash: str,
        salt: str,
        status: str = CUSTOMER_STATUS_ACTIVE,
        created_at: Optional[str] = None
    ):
        self.id = id
        self.full_name = full_name
        self.cnic = cnic
        self.phone = phone
        self.email = email
        self.address = address
        self.date_of_birth = date_of_birth
        self.username = username
        self.password_hash = password_hash
        self.salt = salt
        self.status = status
        self.created_at = created_at

    @property
    def is_active(self) -> bool:
        """Returns True if the customer account is in Active state."""
        return self.status == CUSTOMER_STATUS_ACTIVE

    @property
    def is_blocked(self) -> bool:
        """Returns True if the customer account is in Blocked state."""
        return self.status == CUSTOMER_STATUS_BLOCKED

    @classmethod
    def from_row(cls, row: Any) -> "Customer":
        """Constructs a Customer instance from a sqlite3.Row or mapping."""
        return cls(
            id=row["id"],
            full_name=row["full_name"],
            cnic=row["cnic"],
            phone=row["phone"],
            email=row["email"],
            address=row["address"],
            date_of_birth=row["date_of_birth"],
            username=row["username"],
            password_hash=row["password_hash"],
            salt=row["salt"],
            status=row["status"],
            created_at=row["created_at"]
        )

    def to_dict(self) -> Dict[str, Any]:
        """Returns customer data as dictionary (omits password hash and salt for safety)."""
        return {
            "id": self.id,
            "full_name": self.full_name,
            "cnic": self.cnic,
            "phone": self.phone,
            "email": self.email,
            "address": self.address,
            "date_of_birth": self.date_of_birth,
            "username": self.username,
            "status": self.status,
            "created_at": self.created_at
        }

    def __repr__(self) -> str:
        return f"<Customer id={self.id} username='{self.username}' status='{self.status}'>"
