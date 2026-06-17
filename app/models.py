from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Float
)

from sqlalchemy.sql import func

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    username = Column(
        String,
        unique=True,
        nullable=False
    )

    email = Column(
        String,
        unique=True,
        nullable=True
    )

    phone = Column(
        String,
        unique=True,
        nullable=True
    )

    password_hash = Column(
        String,
        nullable=False
    )

    balance = Column(
        Integer,
        default=100000
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    role = Column(
    String,
    default="PLAYER"
    )


class GameRound(Base):
    __tablename__ = "game_rounds"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    period = Column(
        String,
        unique=True,
        nullable=False
    )

    result = Column(
        String,
        nullable=False
    )

    game_mode = Column(
    String,
    default="BET_COUNT"
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )


class Bet(Base):
    __tablename__ = "bets"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    user_id = Column(
        Integer,
        nullable=False
    )

    period = Column(
        String,
        nullable=False
    )

    color = Column(
        String,
        nullable=False
    )

    amount = Column(
        Float,
        nullable=False
    )

    status = Column(
        String,
        default="PENDING"
    )

    payout = Column(
        Float,
        default=0
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )


class SystemConfig(Base):
    __tablename__ = "system_config"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    game_mode = Column(
        String,
        default="BET_COUNT"
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )