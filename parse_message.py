from datetime import datetime
from classes import DeltaInstance
import re

class ParseMessageResult:
    def __init__(self, username: str = None, user_handle: str = None, delta: int = None, new_length: int = None, wait_minutes: int = None):
        self.username = username
        self.user_handle = user_handle
        self.delta = delta
        self.new_length = new_length
        self.wait_minutes = wait_minutes

def __parse_username(message: str) -> tuple[bool,str]: 
    search = re.search("^@(.+?),", message)
    if search:
        return (False, search.group(1))
    search = re.search("^(.+?),", message)
    if search:
        return (True, search.group(1))
    return None

def __parse_delta(message: str) -> tuple[int, bool, int]:
    length_change = None
    grow = re.search(r'виріс на (\d+)', message)
    shrink = re.search(r'скоротився на (\d+)', message)
    reset = re.search(r'в тебе немає песюна', message)
    new_length_search = re.search(r'Тепер його довжина: (\d+)', message)
    new_length = int(new_length_search.group(1)) if new_length_search else None
    length_change = (int(grow.group(1)), False) if grow else ((-int(shrink.group(1)), False) if shrink else ((0, True) if reset else None))
    return None if length_change is None else length_change + (new_length,)

def __parse_wait_minutes(message: str) -> int:
    wait_search = re.search(r'Продовжуй грати через (\d+) год., (\d+) хв.', message)
    hour = wait_search.group(1)
    minute = wait_search.group(2)
    return int(hour) * 60 + int(minute)

def parse_message(message: str) -> ParseMessageResult:
    username_result = __parse_username(message)
    if username_result is None:
        return None
    delta_result = __parse_delta(message)
    if delta_result is None:
        return None
    wait_minutes_result = __parse_wait_minutes(message)
    username = None
    user_handle = None
    if username_result[0]:
        username = username_result[1]
    else:
        user_handle = username_result[1]
    delta = delta_result[0] if not delta_result[1] else 0
    new_length = delta_result[2] if not delta_result[1] else 0
    return ParseMessageResult(
        username=username,
        user_handle=user_handle,
        delta=delta,
        new_length=new_length,
        wait_minutes=wait_minutes_result
    )
