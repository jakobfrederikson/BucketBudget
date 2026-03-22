from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey
from datetime import datetime
from datetime import timezone

from flask import url_for

from bucketbudget import db
from bucketbudget.auth.models import User

from flask_security.models import fsqla_v3 as fsqla
fsqla.FsModels.set_db_info(db)

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    LargeBinary,
    String,
)

class User(db.Model, fsqla.FsUserMixin):
    __tablename__ = "user"
    email = Column("email")


class Budget(db.Model):
    __tablename__ = "Budget"
    id = Column(Integer, primary_key=True)
    owner_id: Mapped[int] = map

