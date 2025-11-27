from sqlalchemy import BigInteger, DateTime, ForeignKey
from typing import Optional, List
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from datetime import datetime

class Base(DeclarativeBase):
    pass

class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    group_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("groups.id", ondelete="CASCADE"))
    group: Mapped["Group"] = relationship(back_populates="events")
    username: Mapped[str]
    time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True)
    )
    delta: Mapped[int]
    wait_minutes: Mapped[Optional[int]]
    new_length: Mapped[Optional[int]]

class GroupUser(Base):
    __tablename__ = "group_user"

    group_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("groups.id", ondelete="CASCADE"), primary_key=True)
    group: Mapped["Group"] = relationship(back_populates="users")

    username: Mapped[str]
    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

class Group(Base):
    __tablename__ = "groups"
    
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    events: Mapped[List["Event"]] = relationship(back_populates="group", order_by=Event.time)
    users: Mapped[List["GroupUser"]] = relationship(back_populates="group")
    analytics: Mapped["Analytics"] = relationship(back_populates="group")

class AnalyticsUser(Base):
    __tablename__ = "analytics_user"

    analytics_id: Mapped[int] = mapped_column(ForeignKey("analytics.id", ondelete="CASCADE"), primary_key=True)
    analytics: Mapped["Analytics"] = relationship(back_populates="users")

    username: Mapped[str] = mapped_column(primary_key=True)

class UserLengthHistory(Base):
    __tablename__ = "user_length_history"

    analytics_id: Mapped[int] = mapped_column(ForeignKey("analytics.id", ondelete="CASCADE"))
    analytics: Mapped["Analytics"] = relationship(back_populates="user_length_history")
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str]
    length: Mapped[int]
    time: Mapped[datetime] = mapped_column(DateTime(timezone=True))

class UserDeltaHistory(Base):
    __tablename__ = "user_delta_history"

    analytics_id: Mapped[int] = mapped_column(ForeignKey("analytics.id", ondelete="CASCADE"))
    analytics: Mapped["Analytics"] = relationship(back_populates="user_delta_history")

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str]
    delta: Mapped[int]
    time: Mapped[datetime] = mapped_column(DateTime(timezone=True))

class BestPlayerHistory(Base):
    __tablename__ = "best_player_history"

    analytics_id: Mapped[int] = mapped_column(ForeignKey("analytics.id", ondelete="CASCADE"))
    analytics: Mapped["Analytics"] = relationship(back_populates="best_player_history")

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str]
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    end_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

class UserStreak(Base):
    __tablename__ = "user_streak"

    analytics_id: Mapped[int] = mapped_column(ForeignKey("analytics.id", ondelete="CASCADE"))
    analytics: Mapped["Analytics"] = relationship(back_populates="user_streaks")
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str]
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    days_count: Mapped[int]

class UserBestRank(Base):
    __tablename__ = "user_best_rank"

    analytics_id: Mapped[int] = mapped_column(ForeignKey("analytics.id", ondelete="CASCADE"), primary_key=True)
    analytics: Mapped["Analytics"] = relationship(back_populates="user_best_ranks")

    username: Mapped[str] = mapped_column(primary_key=True)
    rank: Mapped[int]

class Analytics(Base):
    __tablename__ = "analytics"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    group_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("groups.id", ondelete="CASCADE"))
    group: Mapped["Group"] = relationship(back_populates="analytics")

    users: Mapped[List["AnalyticsUser"]] = relationship(back_populates="analytics")
    user_length_history: Mapped[List["UserLengthHistory"]] = relationship(back_populates="analytics", order_by=UserLengthHistory.time)
    user_delta_history: Mapped[List["UserDeltaHistory"]] = relationship(back_populates="analytics", order_by=UserDeltaHistory.time)
    best_player_history: Mapped[List["BestPlayerHistory"]] = relationship(back_populates="analytics", order_by=BestPlayerHistory.start_time)
    user_streaks: Mapped[List["UserStreak"]] = relationship(back_populates="analytics", order_by=UserStreak.start_time)
    user_best_ranks: Mapped[List["UserBestRank"]] = relationship(back_populates="analytics")