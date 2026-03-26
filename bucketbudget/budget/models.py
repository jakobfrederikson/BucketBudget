from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey
from datetime import datetime
from datetime import timezone

from flask import url_for

from bucketbudget import db
from bucketbudget.auth.models import User

import decimal
import enum


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


class Frequency(enum.Enum):
    Weekly = 'Weekly'
    Fortnightly = 'Fortnightly'
    FourWeekly = 'FourWeekly'
    Monthly = 'Monthly'
    Yearly = 'Yearly'


class Budget(db.Model):
    __tablename__ = "budget"
    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    created: Mapped[datetime] = mapped_column(default=now_utc)
    title: Mapped[str]
    invite_code: Mapped[str]
    frequency: Mapped[Frequency]

    # User object backed by owner_id
    # lazy="joined" means the user is returned with the budget in one query
    owner: Mapped[User] = relationship(back_populates="budgets")

    income_items = relationship(
        "IncomeItem",
        backref="budget",
        cascade="all, delete"
    )
    expense_items = relationship(
        "ExpenseItem",
        backref="budget",
        cascade="all, delete"
    )
    buckets = relationship(
        "Bucket",
        backref="budget",
        cascade="all, delete"
    )

    @property
    def update_url(self) -> str:
        return url_for("budget.update", id=self.id)

    @property
    def delete_url(self) -> str:
        return url_for("budget.delete", id=self.id)


class IncomeItem(db.Model):
    __tablename__ = "income_item"
    id: Mapped[int] = mapped_column(primary_key=True)
    budget_id: Mapped[int] = mapped_column(ForeignKey("budget.id", ondelete="CASCADE"))
    title: Mapped[str]
    amount: Mapped[decimal.Decimal]
    frequency: Mapped[Frequency]


class ExpenseItem(db.Model):
    __tablename__ = "expense_item"
    id: Mapped[int] = mapped_column(primary_key=True)
    budget_id: Mapped[int] = mapped_column(ForeignKey("budget.id", ondelete="CASCADE"))
    title: Mapped[str]
    amount: Mapped[decimal.Decimal]
    frequency: Mapped[Frequency]
    expense_bucket: Mapped[bool]


class Bucket(db.Model):
    __tablename__ = "bucket"
    id: Mapped[int] = mapped_column(primary_key=True)
    budget_id: Mapped[int] = mapped_column(ForeignKey("budget.id", ondelete="CASCADE"))
    title: Mapped[str]
    percent: Mapped[decimal.Decimal]