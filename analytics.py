from classes import DeltaInstance, Dataset
from logger import logger
from datetime import datetime

class Analytics:

    def __list_users(self, dataset: Dataset):
        logger.info(f"[Analytics] Starting to list all users")
        self.users = set()
        for delta in dataset.deltas:
            user = delta.user
            self.users.add(user)
        logger.info(f"[Analytics] Done! Found a total of {len(self.users)} users")

    def __calculate_user_length_histories(self, dataset: Dataset):
        logger.info(f"[Analytics] Starting to calculate user length histories")
        self.user_length_histories: dict[str,list[tuple[datetime, int]]] = {}
        user_lengths = {}
        for delta in dataset.deltas:
            user = delta.user
            cur_length = user_lengths.get(user, 0) + delta.delta
            user_lengths[user] = cur_length
            if user not in self.user_length_histories:
                self.user_length_histories[user] = []
            self.user_length_histories[user].append((delta.timestamp,cur_length))

        logger.info(f"[Analytics] User length histories are done!")

    def __init__(self, dataset: Dataset):
        deltas = dataset.deltas
        logger.info(f"[Analytics] Starting building analytics from {len(deltas)} deltas")
        self.__list_users(dataset)
        self.__calculate_user_length_histories(dataset)
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
    
def build_analytics(dataset: Dataset) -> Analytics:
    return Analytics(dataset)
