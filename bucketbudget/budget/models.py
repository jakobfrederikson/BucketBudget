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
    FourWeekly = 'Four-Weekly'
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
    owner: Mapped[User] = relationship(
        lazy="joined", back_populates="budgets")

    income_items = relationship(
        "IncomeItem",
        back_populates="budget",
        cascade="all, delete",
        passive_deletes=True
    )
    expense_items = relationship(
        "ExpenseItem",
        back_populates="budget",
        cascade="all, delete",
        passive_deletes=True
    )
    buckets = relationship(
        "Bucket",
        back_populates="budget",
        cascade="all, delete",
        passive_deletes=True
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

    budget: Mapped["Budget"] = relationship(back_populates="income_items")


class ExpenseItem(db.Model):
    __tablename__ = "expense_item"
    id: Mapped[int] = mapped_column(primary_key=True)
    budget_id: Mapped[int] = mapped_column(ForeignKey("budget.id", ondelete="CASCADE"))
    title: Mapped[str]
    amount: Mapped[decimal.Decimal]
    frequency: Mapped[Frequency]
    expense_bucket: Mapped[bool]

    budget: Mapped["Budget"] = relationship(back_populates="expense_items")


class Bucket(db.Model):
    __tablename__ = "bucket"
    id: Mapped[int] = mapped_column(primary_key=True)
    budget_id: Mapped[int] = mapped_column(ForeignKey("budget.id", ondelete="CASCADE"))
    title: Mapped[str]
    percent: Mapped[decimal.Decimal]

    budget: Mapped["Budget"] = relationship(back_populates="buckets")