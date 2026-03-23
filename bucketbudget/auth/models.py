from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy.orm import Mapped, mapped_column, relationship
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
    budgets: Mapped[list[Budget]] = relationship(
        "Budget", back_populates="owner")