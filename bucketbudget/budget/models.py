from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, Table, Column
from datetime import datetime
from datetime import timezone

from flask import url_for

from bucketbudget import db, Base

from decimal import Decimal, ROUND_HALF_UP
import enum


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


class Frequency(enum.Enum):
    Weekly = 'Weekly'
    Fortnightly = 'Fortnightly'
    FourWeekly = 'Four-Weekly'
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
    frequency_enum: Mapped[Frequency]

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
    def view_url(self) -> str:
        return url_for("budget.read", budget_id=self.id)

    @property
    def update_url(self) -> str:
        return url_for("budget.update", budget_id=self.id)

    @property
    def delete_url(self) -> str:
        return url_for("budget.delete", budget_id=self.id)

    @property
    def frequency(self) -> str:
        return self.frequency_enum.value


class IncomeItem(db.Model):
    __tablename__ = "income_item"
    id: Mapped[int] = mapped_column(primary_key=True)
    budget_id: Mapped[int] = mapped_column(ForeignKey("budget.id", ondelete="CASCADE"))
    title: Mapped[str]
    amount_int: Mapped[int]
    frequency_enum: Mapped[Frequency]

    @property
    def amount(self) -> Decimal:
        return Decimal(self.amount_int / 100.0).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    @amount.setter
    def amount(self, value: Decimal):
        value = value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        self.amount_int = int(value * 100)

    @property
    def frequency(self) -> str:
        return self.frequency_enum.value


class ExpenseItem(db.Model):
    __tablename__ = "expense_item"
    id: Mapped[int] = mapped_column(primary_key=True)
    budget_id: Mapped[int] = mapped_column(ForeignKey("budget.id", ondelete="CASCADE"))
    title: Mapped[str]
    amount_int: Mapped[int]
    frequency_enum: Mapped[Frequency]

    @property
    def amount(self) -> Decimal:
        return Decimal(self.amount_int / 100.0).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    @amount.setter
    def amount(self, value: Decimal):
        value = value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        print("test")
        self.amount_int = int(value * 100)

    @property
    def frequency(self) -> str:
        return self.frequency_enum.value


bucket_expense_items = Table(
    "bucket_expense_items",
    Base.metadata,
    Column("bucket_id", ForeignKey("bucket.id", ondelete="CASCADE"), primary_key=True),
    Column("expense_item_id", ForeignKey("expense_item.id", ondelete="CASCADE"), primary_key=True)
)

class Bucket(db.Model):
    __tablename__ = "bucket"
    id: Mapped[int] = mapped_column(primary_key=True)
    budget_id: Mapped[int] = mapped_column(ForeignKey("budget.id", ondelete="CASCADE"))
    title: Mapped[str]
    is_expense_bucket: Mapped[bool]
    percent_int: Mapped[int | None]

    expense_items: Mapped[list["ExpenseItem"]] = relationship(
        secondary=bucket_expense_items,
        backref="buckets"
    )
    
    @property
    def expense_items_sum(self) -> Decimal:
        if self.is_expense_bucket:
            # return sum of all expense items linked to this bucket
            return sum((item.amount for item in self.expense_items), Decimal("0.01"))
        else:
            # not an expense item bucket so return 0
            return 0

    @property
    def percent(self) -> Decimal:
        if self.is_expense_bucket:
            return 0
        return Decimal(self.percent_int / 100.0)

    @percent.setter
    def percent(self, value: Decimal):
        if not self.is_expense_bucket:
            value = value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            self.percent_int = int(value * 100)