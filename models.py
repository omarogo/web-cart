from app import db, login
from datetime import datetime, timezone, date
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from typing import Optional

import sqlalchemy as sa
import sqlalchemy.orm as so


class Users(UserMixin, db.Model):
    __tablename__ = 'users'
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    username: so.Mapped[str] = so.mapped_column(sa.String(64), index=True, unique=True, nullable=False)
    name: so.Mapped[str] = so.mapped_column(sa.String(100), index=True, nullable=False)
    email: so.Mapped[str] = so.mapped_column(sa.String(120), index=True, unique=True, nullable=False)
    password_hash: so.Mapped[Optional[str]] = so.mapped_column(sa.String(256), nullable=False)
    created_at: so.Mapped[datetime] = so.mapped_column(sa.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: so.Mapped[datetime] = so.mapped_column(sa.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relaciones ORM
    markets: so.Mapped[list['Markets']] = so.relationship(
        'Markets', back_populates='owner', cascade='all, delete-orphan'
    )
    buys: so.Mapped[list['Buys']] = so.relationship(
        'Buys', back_populates='buyer', cascade='all, delete-orphan'
    )

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def __repr__(self) -> str:
        return f"<Users id={self.id} username={self.username!r}>"


class Markets(db.Model):
    __tablename__ = 'markets'
    market_id: so.Mapped[int] = so.mapped_column(primary_key=True)
    name: so.Mapped[str] = so.mapped_column(sa.String(128), index=True, nullable=False)
    date: so.Mapped[date] = so.mapped_column(sa.Date, default=date.today, index=True)
    user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(Users.id), index=True, nullable=False)
    created_at: so.Mapped[datetime] = so.mapped_column(sa.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: so.Mapped[datetime] = so.mapped_column(sa.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relaciones ORM
    owner: so.Mapped[Users] = so.relationship(
        'Users', back_populates='markets'
    )
    items: so.Mapped[list['Buys']] = so.relationship(
        'Buys', back_populates='market', cascade='all, delete-orphan'
    )

    def __repr__(self) -> str:
        return f"<Markets market_id={self.market_id} name={self.name!r}>"


class Buys(db.Model):
    __tablename__ = 'buys'
    buy_id: so.Mapped[int] = so.mapped_column(primary_key=True)
    item_name: so.Mapped[str] = so.mapped_column(sa.String(64), index=True, nullable=False)
    qty: so.Mapped[int] = so.mapped_column(nullable=False)
    price: so.Mapped[float] = so.mapped_column(nullable=False)
    expire: so.Mapped[Optional[datetime]] = so.mapped_column(sa.DateTime(timezone=True), index=True, nullable=True)
    market_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(Markets.market_id), index=True, nullable=False)
    user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(Users.id), index=True, nullable=False)
    created_at: so.Mapped[datetime] = so.mapped_column(sa.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: so.Mapped[datetime] = so.mapped_column(sa.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relaciones ORM
    market: so.Mapped[Markets] = so.relationship(
        'Markets', back_populates='items'
    )
    buyer: so.Mapped[Users] = so.relationship(
        'Users', back_populates='buys'
    )

    def __repr__(self) -> str:
        return f"<Buys buy_id={self.buy_id} item_name={self.item_name!r} qty={self.qty}>"


# Carga de usuario para flask-login
@login.user_loader
def load_user(user_id: str) -> Optional[Users]:
    return db.session.get(Users, int(user_id))


