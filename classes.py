from datetime import datetime

class DeltaInstance:
    def __init__(self, user: str, timestamp: datetime, delta: int, wait_minutes: int = None, is_reset: bool = False, new_length: int = None):
        self.user = user
        self.timestamp = timestamp
        self.delta = delta
        self.wait_minutes = wait_minutes
        self.is_reset = is_reset
        self.new_length = new_length

class Dataset:
    def __init__(self, deltas: list[DeltaInstance], unknown_users: list[str]):
        self.deltas = deltas
        self.unknown_users = unknown_users