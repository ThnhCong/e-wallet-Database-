from dataclasses import dataclass
from typing import Any


@dataclass
class AppState:
    user: dict[str, Any] | None = None

    @property
    def user_id(self):
        return self.user.get("user_id") if self.user else None

    @property
    def is_admin(self):
        return bool(self.user and self.user.get("user_role", "").lower() == "admin")

    def clear(self):
        self.user = None
