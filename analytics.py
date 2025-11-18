from classes import DeltaInstance
from logger import logger

class Analytics:
    def __init__(self, deltas: list[DeltaInstance]):
        logger.info(f"Starting building analytics from {len(deltas)} deltas")
        self.users = set()
        self.user_lengths = {}
        for delta in deltas:
            self.users.add(delta.user)
            cur_length = self.user_lengths.get(delta.user, 0)
            self.user_lengths[delta.user] = cur_length + delta.delta
        logger.info(f"Found a total of {len(self.users)} users")

    def get_users(self) -> set[str]:
        return self.users

    def get_user_length(self, user: str) -> int:
        return self.user_lengths.get(user, 0)
    
def build_analytics(deltas: list[DeltaInstance]) -> Analytics:
    return Analytics(deltas)
