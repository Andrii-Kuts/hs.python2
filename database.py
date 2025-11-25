from sqlalchemy import DateTime, ForeignKey, select, delete
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine, AsyncSession
from typing import Optional, List
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker, selectinload
from datetime import datetime
import os
from classes import *
from logger import logger

class Base(DeclarativeBase):
    pass

class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(primary_key=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"))
    group: Mapped["Group"] = relationship(back_populates="events")
    username: Mapped[str]
    time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True)
    )
    delta: Mapped[int]
    wait_minutes: Mapped[Optional[int]]
    new_length: Mapped[Optional[int]]

class Group(Base):
    __tablename__ = "groups"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    events: Mapped[List["Event"]] = relationship(back_populates="group")

class Database:
    _instance: Database = None

    @classmethod
    async def get_instance(cls) -> Database:
        if cls._instance is None:
            cls._instance = Database()
            await cls._instance._initialize()
        return cls._instance

    def __init__(self):
        self.engine = create_async_engine(os.getenv("DB_URL"))
        self.AsyncSessionLocal: sessionmaker[AsyncSession] = sessionmaker(self.engine, class_=AsyncSession, expire_on_commit=False)
        
    async def _initialize(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def import_dataset(self, group_id: int, dataset: Dataset):
        logger.info(f"[Database] Starting to load dataset into a database")
        try:
            async with self.AsyncSessionLocal() as session:
                async with session.begin():
                    group = await session.get(Group, group_id)
                    if group is None:
                        group = Group(id=group_id)
                        session.add(group)
                    await session.execute(delete(Event).where(Event.group_id == group.id))
                    events = [Event(
                        group=group,
                        username=delta.user,
                        time=delta.timestamp,
                        delta=delta.delta,
                        wait_minutes=delta.wait_minutes,
                        new_length=delta.new_length,
                    ) for delta in dataset.deltas]
                    session.add_all(events)
                    await session.commit()
                    logger.info(f"[Database] Successfuly loaded dataset into a database!")
                    return True
        except Exception as e:
            logger.error("[Database] Error while importing dataset", exc_info=True)
            return False
        
    async def read_dataset(self, group_id: int) -> Dataset:
        logger.info(f"[Database] Starting to read dataset from a database")
        try:
            async with self.AsyncSessionLocal() as session:
                async with session.begin():
                    result = await session.execute(
                        select(Group)
                        .options(selectinload(Group.events))
                        .where(Group.id == group_id)
                    )
                    group = result.scalar_one_or_none()
                    if group is None:
                        return None
                    deltas = [DeltaInstance(
                        event.username,
                        event.time,
                        event.delta,
                        event.wait_minutes,
                        event.delta == 0,
                        event.new_length,
                    ) for event in group.events]
                    dataset = Dataset(deltas)
                    return dataset
        except Exception as e:
            logger.error("[Database] Error while reading dataset", exc_info=True)
            return None

