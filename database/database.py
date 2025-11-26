from sqlalchemy import DateTime, ForeignKey, select, delete
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine, AsyncSession
from typing import Optional, List
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker, selectinload
from datetime import datetime
import os
from classes import *
from logger import logger
from analytics import Analytics
import database.tables as table

class Database:
    _instance: Database = None

    @classmethod
    async def get_instance(cls) -> Database:
        if cls._instance is None:
            cls._instance = Database()
            await cls._instance._initialize()
        return cls._instance

    def __init__(self):
        db_endpoint = os.getenv("DATABASE_ENDPOINT")
        db_user = os.getenv("DATABASE_USER")
        db_password = os.getenv("DATABASE_PASSWORD")
        db_name = os.getenv("DATABASE_NAME")
        db_url = f"postgresql+asyncpg://{db_user}:{db_password}@{db_endpoint}/{db_name}"
        self.engine = create_async_engine(db_url)
        self.AsyncSessionLocal: sessionmaker[AsyncSession] = sessionmaker(self.engine, class_=AsyncSession, expire_on_commit=False)
        
    async def _initialize(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(table.Base.metadata.create_all)

    async def import_dataset(self, group_id: int, dataset: Dataset):
        logger.info(f"[Database] Starting to load dataset into a database")
        try:
            async with self.AsyncSessionLocal() as session:
                async with session.begin():
                    group = await session.get(table.Group, group_id)
                    if group is None:
                        group = table.Group(id=group_id)
                        session.add(group)
                    await session.execute(delete(table.Event).where(table.Event.group_id == group.id))
                    events = [table.Event(
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
                        select(table.Group)
                        .options(selectinload(table.Group.events))
                        .where(table.Group.id == group_id)
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
        except Exception:
            logger.error("[Database] Error while reading dataset", exc_info=True)
            return None
        
    async def write_analytics(self, group_id: int, analytics: Analytics):
        logger.info(f"[Database] Starting to write analytics into a database")
        try:
            async with self.AsyncSessionLocal() as session:
                async with session.begin():
                    group = await session.get(table.Group, group_id)
                    if group is None:
                        return
                    await session.execute(delete(table.Analytics).where(table.Analytics.group_id == group.id))
                    users = [table.AnalyticsUser(username=user) for user in analytics.users]
                    user_length_history: list[table.UserLengthHistory] = []
                    for user,user_length_histories in analytics.user_length_histories.items():
                        user_length_history.extend([table.UserLengthHistory(
                            username=user,
                            time=user_length_history[0],
                            length=user_length_history[1],
                        ) for user_length_history in user_length_histories])
                    user_delta_history: list[table.UserDeltaHistory] = []
                    for user,user_deltas in analytics.user_deltas.items():
                        user_delta_history.extend([table.UserDeltaHistory(
                            username=user,
                            delta=user_delta[1],
                            time=user_delta[0],
                        ) for user_delta in user_deltas])
                    best_player_history = [table.BestPlayerHistory(
                        username=best_player[0],
                        start_time=best_player[1],
                        end_time=best_player[2],
                    ) for best_player in analytics.best_players_history]
                    user_streaks: list[table.UserStreak] = []
                    for user,streaks in analytics.streaks.items():
                        user_streaks.extend([table.UserStreak(
                            username=user,
                            start_time=streak[0],
                            end_time=streak[1],
                            days_count=streak[2],
                        ) for streak in streaks])
                    analytics_db = table.Analytics(
                        group_id=group_id,
                        users=users,
                        user_length_history=user_length_history,
                        user_delta_history=user_delta_history,
                        best_player_history=best_player_history,
                        user_streaks=user_streaks,
                    )
                    session.add(analytics_db)
                    await session.commit()
                    logger.info(f"[Database] Successfuly written analytics into a database!")
                    return True
        except Exception:
            logger.error("[Database] Error while writing analytics", exc_info=True)
            return False

    async def read_analytics(self, group_id: int) -> Analytics:
        logger.info(f"[Database] Starting to read analytics from a database")
        try:
            async with self.AsyncSessionLocal() as session:
                async with session.begin():
                    result = await session.execute(
                        select(table.Group)
                        .options(
                            selectinload(table.Group.analytics).selectinload(table.Analytics.users),
                            selectinload(table.Group.analytics).selectinload(table.Analytics.user_length_history),
                            selectinload(table.Group.analytics).selectinload(table.Analytics.user_delta_history),
                            selectinload(table.Group.analytics).selectinload(table.Analytics.best_player_history),
                            selectinload(table.Group.analytics).selectinload(table.Analytics.user_streaks),
                        )
                        .where(table.Group.id == group_id)
                    )
                    group = result.scalar_one_or_none()
                    if group is None:
                        return None
                    
                    users = list(map(lambda user: user.username, group.analytics.users))
                    user_length_histories: dict[str,list[tuple[datetime, int]]] = {}
                    for user_length in group.analytics.user_length_history:
                        user = user_length.username
                        if user not in user_length_histories:
                            user_length_histories[user] = []
                        user_length_histories[user].append((user_length.time, user_length.length))
                    user_deltas: dict[str, list[tuple[datetime, int]]] = {}
                    for user_delta in group.analytics.user_delta_history:
                        user = user_delta.username
                        if user not in user_deltas:
                            user_deltas[user] = []
                        user_deltas[user].append((user_delta.time, user_delta.delta))
                    best_players_history = [(best_player.username, best_player.start_time, best_player.end_time)
                        for best_player in group.analytics.best_player_history]
                    streaks: dict[str, list[tuple[datetime, datetime, int]]] = {}
                    for streak in group.analytics.user_streaks:
                        user = streak.username
                        if user not in streaks:
                            streaks[user] = []
                        streaks[user].append((streak.start_time, streak.end_time, streak.days_count))

                    analytics = Analytics(users, user_length_histories, user_deltas, best_players_history, streaks)
                    return analytics
        except Exception as e:
            logger.error("[Database] Error while reading analytics", exc_info=True)
            return None

