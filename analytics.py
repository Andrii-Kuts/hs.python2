from classes import Dataset
from logger import logger
from datetime import datetime, timezone, timedelta
from utils import *

class Analytics:

    def __list_users(self, dataset: Dataset):
        logger.info(f"[Analytics] Starting to list all users")
        self.users = set()
        for delta in dataset.deltas:
            user = delta.user
            self.users.add(user)
        logger.info(f"[Analytics] Done! Found a total of {len(self.users)} users")

    def __check_deltas(self, dataset: Dataset):
        logger.info(f"[Analytics] Starting to check deltas for inconsistencies")
        user_lengths = {}
        for delta in dataset.deltas:
            user = delta.user
            cur_length = apply_delta(user_lengths.get(user, 0), delta)
            user_lengths[user] = cur_length
            if delta.new_length is not None and cur_length != delta.new_length:
                logger.warning(f"Warning! Calculated and provided lengths don't match: user = {user} time = {delta.timestamp} expected = {cur_length} actual = {delta.new_length}")
        logger.info(f"[Analytics] Finished checkin deltas for inconsistencies")

    def __calculate_user_length_histories(self, dataset: Dataset):
        logger.info(f"[Analytics] Starting to calculate user length histories")
        self.user_length_histories: dict[str,list[tuple[datetime, int]]] = {}
        user_lengths = {}
        for delta in dataset.deltas:
            user = delta.user
            cur_length = apply_delta(user_lengths.get(user, 0), delta)
            user_lengths[user] = cur_length
            if user not in self.user_length_histories:
                self.user_length_histories[user] = []
            self.user_length_histories[user].append((delta.timestamp,cur_length))
        logger.info(f"[Analytics] User length histories are done!")

    def __calculate_user_deltas(self, dataset: Dataset):
        logger.info(f"[Analytics] Starting to calculate user deltas")
        self.user_deltas: dict[str, list[tuple[datetime, int]]] = {}
        for delta in dataset.deltas:
            user = delta.user
            if user not in self.user_deltas:
                self.user_deltas[user] = []
            self.user_deltas[user].append((delta.timestamp, delta.delta))
        logger.info(f"[Analytics] User deltas are done!")

    def __calculate_best_players_history(self, dataset: Dataset):
        logger.info(f"[Analytics] Starting to calculate best players history")
        self.best_players_history: list[tuple[str, datetime, datetime]] = []
        self.best_rank: dict[str, int] = {}
        user_lengths = {}
        cur_best: str = None
        cur_start: datetime = None
        for delta in dataset.deltas:
            user = delta.user
            cur_length = apply_delta(user_lengths.get(user, 0), delta)
            user_lengths[user] = cur_length

            # update best
            best = max(user_lengths, key=user_lengths.get)
            if best != cur_best:
                cur_time = delta.timestamp
                if cur_best is not None:
                    self.best_players_history.append((cur_best, cur_start, cur_time))
                cur_best = best
                cur_start = cur_time

            # update best ranks
            for i, (user, length) in enumerate(
                sorted(user_lengths.items(), key=lambda kv: kv[1], reverse=True)
            ):
                rank = i+1
                cur_rank = self.best_rank.get(user)
                if cur_rank is None or rank < cur_rank:
                    self.best_rank[user] = rank
                
        if cur_best is not None:
            self.best_players_history.append((cur_best, cur_start, datetime.now(timezone.utc)))
        logger.info(f"[Analytics] Best players history is done!")

    def __calculate_streaks(self, dataset: Dataset):
        logger.info(f"[Analytics] Starting to calculate streaks")
        self.streaks: dict[str, list[tuple[datetime, datetime, int]]] = {}
        current_streak: dict[str, tuple[datetime, datetime, int]] = {}
        def add_streak(user: str, streak: tuple[datetime, datetime, int]):
            if user not in self.streaks:
                self.streaks[user] = []
            self.streaks[user].append(streak)
        def close_streak(user: str):
            if user not in current_streak:
                return
            add_streak(user, current_streak.get(user))
        for delta in dataset.deltas:
            user = delta.user
            date = delta.timestamp
            cur_streak_count = 0
            if user not in current_streak:
                current_streak[user] = (date, date, 1)
                cur_streak_count = 1
            else:
                streak = current_streak.get(user)
                prev_date = streak[1]
                start_date = streak[0]
                if same_pesun_day(prev_date, date):
                    logger.warning(f"[Analytics] Warning while calculating streaks! Two events in the same day! user = {user} prev_date = {prev_date} date = {date}")
                elif consecutive_pesun_days(prev_date, delta.timestamp):
                    cur_streak_count = streak[2]+1
                else:
                    close_streak(user)
                    cur_streak_count = 1
                    start_date = date
                current_streak[user] = (start_date, date, cur_streak_count)
        for user in current_streak.keys():
            close_streak(user)
        logger.info(f"[Analytics] Streaks are done!")

    def __init__(self, dataset: Dataset):
        deltas = dataset.deltas
        logger.info(f"[Analytics] Starting building analytics from {len(deltas)} deltas")
        self.__list_users(dataset)
        self.__check_deltas(dataset)
        self.__calculate_user_length_histories(dataset)
        self.__calculate_user_deltas(dataset)
        self.__calculate_best_players_history(dataset)
        self.__calculate_streaks(dataset)
        logger.info(f"[Analytics] Done buildng all analytics")

    def get_users(self) -> set[str]:
        return self.users

    def get_user_length(self, user: str) -> int:
        history = self.user_length_histories.get(user)
        if history is None:
            return 0
        return history[-1][1] if len(history) > 0 else 0
    
    def get_user_length_history(self, user: str) -> list[tuple[datetime, int]]:
        return self.user_length_histories[user]
    
    def get_user_best_rank(self, user: str) -> int:
        return self.best_rank[user]
    
    def get_user_events_count(self, user: str) -> int:
        return len(self.user_deltas.get(user))
    
    def get_user_average_interval(self, user: str) -> timedelta:
        deltas = self.get_user_deltas(user)
        duration = deltas[-1][0] - deltas[0][0]
        count = len(deltas)-1
        if count <= 0:
            return duration
        return duration / count
        
    def get_user_best_streak(self, user: str) -> tuple[datetime, datetime, int]:
        return max(self.streaks.get(user), key=lambda streak: streak[2])

    def get_user_deltas(self, user: str) -> list[tuple[datetime, int]]:
        return self.user_deltas.get(user)
    
    def get_best_players_history(self):
        return self.best_players_history
    
    def get_user_streaks(self, user: str) -> list[tuple[datetime, datetime, int]]:
        return self.streaks.get(user)
    
    def get_user_current_streak(self, user: str) -> int:
        streak = self.streaks.get(user)[-1]
        deadline = next_pesun_date(streak[1])
        now = datetime.now(timezone.utc)
        return streak[2] if now <= deadline else 0

    
def build_analytics(dataset: Dataset) -> Analytics:
    return Analytics(dataset)
