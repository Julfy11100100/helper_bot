from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class User:
    id: int
    username: Optional[str]
    first_name: str
    added_date: datetime
    is_active: bool = True

@dataclass
class Message:
    id: int
    text: str
    created_date: datetime
    is_active: bool = True