from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, Table, Column
from datetime import datetime
from datetime import timezone

from flask import url_for

from bucketbudget import db, Base

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


budget_user = Table(
    "budget_user",
    Base.metadata,
    Column("budget_id", ForeignKey("budget.id"), primary_key=True),
    Column("user_id", ForeignKey("user.id"), primary_key=True)
)

class Budget(db.Model):
    __tablename__ = "budget"
    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    created: Mapped[datetime] = mapped_column(default=now_utc)
    title: Mapped[str]
    invite_code: Mapped[str]
    frequency: Mapped[Frequency]

    owner: Mapped["User"] = relationship(back_populates="owned_budgets")
    users: Mapped[list["User"]] = relationship(secondary=budget_user, back_populates="budgets")

    income_items: Mapped[list["IncomeItem"]] = relationship(
        "IncomeItem",
        backref="budget",
        cascade="all, delete"
    )
    expense_items: Mapped[list["ExpenseItem"]] = relationship(
        "ExpenseItem",
        backref="budget",
        cascade="all, delete"
    )
    buckets: Mapped[list["Bucket"]] = relationship(
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