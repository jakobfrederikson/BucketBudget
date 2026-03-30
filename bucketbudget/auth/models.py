from __future__ import annotations

import datetime

from typing import TYPE_CHECKING

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey
from werkzeug.security import check_password_hash
from werkzeug.security import generate_password_hash

from bucketbudget import db

from flask_security.models import fsqla_v3 as fsqla
fsqla.FsModels.set_db_info(db)

if TYPE_CHECKING:
    from ..budget.models import Budget


class Role(db.Model, fsqla.FsRoleMixin):
    __tablename__ = "role"


class User(db.Model, fsqla.FsUserMixin):
    __tablename__ = "user"
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(unique=True)
    confirmed_at: Mapped[datetime.datetime]
    owned_budgets: Mapped[list["Budget"]] = relationship(back_populates="owner")
    budgets: Mapped[list["Budget"]] = relationship(secondary="budget_user", back_populates="users")