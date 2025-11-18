from datetime import datetime

class DeltaInstance:
    def __init__(self, user: str, timestamp: datetime, delta: int):
        self.user = user
        self.timestamp = timestamp
        self.delta = delta