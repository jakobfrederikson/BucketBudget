from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey
from datetime import datetime
from datetime import timezone

from flask import url_for

from flaskr import db
from flaskr.auth.models import User


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


class Budget(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    created: Mapped[datetime] = mapped_column(default=now_utc)
    title: Mapped[str]
    invite_code: Mapped[str]
    frequency: Mapped[list]

    # User object backed by owner_id
    # lazy="joined" means the user is returned with the budget in one query
    owner: Mapped[User] = relationship(lazy="joined", back_populates="budgets")

    @property
    def update_url(self) -> str:
        return url_for("budget.update", id=self.id)

    @property
    def delete_url(self) -> str:
        return url_for("budget.delete", id=self.id)