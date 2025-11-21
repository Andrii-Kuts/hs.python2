from logger import logger
from classes import DeltaInstance, Dataset
from pathlib import Path
from bs4 import BeautifulSoup
from datetime import datetime
import re

class MessageMeta:
    def __init__(self, from_user: str, id: int):
        self.from_user = from_user
        self.id = id

def __parse_usernames(archive_path: Path) -> dict[str, str]:
    file_path = archive_path / "nicknames.txt"
    if not file_path.exists():
        logger.error("Nicknames file doesn't exist")
        return {}
    if not file_path.is_file():
        logger.error("Nicknames file is not a file")
        return {}
    logger.info(f"Parsing nicknames file {file_path.name}")
    with open(file_path, 'r') as file:
        content = file.read()
        lines = content.splitlines()
        result = {}
        for line in lines:
            handle, user = line.split()
            result[handle] = user
        return result
    
def __parse_message_id(message: str) -> int:
    id_search = re.search(r'id="message(.*?)"', message, flags=re.DOTALL)
    id = int(id_search.group(1).strip()) if id_search else None
    return id

def __parse_from_user(message: str) -> str:
    from_user_search = re.search(r'<div class="from_name">\s*(.*?)\s*<\/div>', message, flags=re.DOTALL)
    from_user = from_user_search.group(1).strip() if from_user_search else None
    return from_user
    
def __parse_timestamp(message: str) -> datetime:
    timestamp_search = re.search(r'title="([^"]+)"', message)
    if not timestamp_search:
        return None
    timestamp_str = timestamp_search.group(1)
    if not timestamp_str:
        return None
    timestamp_str = timestamp_str.replace("UTC", "")
    timestamp = datetime.strptime(timestamp_str, "%d.%m.%Y %H:%M:%S %z")
    return timestamp

def __parse_length_change(message: str) -> tuple[int, bool, int]:
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

def __parse_message_meta(message: str) -> MessageMeta:
    id = __parse_message_id(message)
    if id is None:
        return None
    from_user = __parse_from_user(message)
    return MessageMeta(from_user, id)

def __parse_user(message: str, usernames: dict[str, str], unknown_users: set[str]) -> str:
    user = None
    text_match = re.search(r'<div class="text">([.\s\S]*?)<\/div>', message, flags=re.DOTALL)
    if not text_match:
        return None
    text_content = text_match.group(1)
    user_search = re.search(r'<a[^>]*>\s*@([^<\n]+)\s*<\/a>', text_content, flags=re.DOTALL)
    # User handle provided, parsing and checking usernames map
    if user_search:
        nickname = '@' + user_search.group(1)
        user = usernames.get(nickname)
        if user is None:
            logger.warning(f"Unknown user: {nickname}")
            unknown_users.add(nickname)
    # No handle, user name might be provided directly
    else:
        name_match = re.search(r'<div class="text">\s*([^<>,]+),\s*твій песюн', message)
        user = name_match.group(1).strip() if name_match else None
    return user

def __parse_message(message: str, messages_meta: dict[str, MessageMeta], usernames: dict[str, str], unknown_users: set[str]) -> DeltaInstance:
    id = __parse_message_id(message)
    joined = re.search(r'message default clearfix joined', message)
    from_user = None
    if not joined:
        from_user = __parse_from_user(message)
    else:
        parent_id = id-1
        while True:
            parent = messages_meta.get(parent_id)
            if not parent:
                break
            from_user = parent.from_user
            if from_user:
                break
            parent_id -= 1
    if from_user != 'Ebobot':
        return None
    timestamp = __parse_timestamp(message)
    if timestamp is None:
        return None
    length_change = __parse_length_change(message)
    if length_change is None:
        return None
    delta,is_reset,new_length = length_change

    user = __parse_user(message, usernames, unknown_users)
    if user is None:
        return None
    wait_minutes = __parse_wait_minutes(message)
    return DeltaInstance(user, timestamp, delta, wait_minutes, is_reset, new_length)

def __parse_html(file_path: Path, usernames: dict[str, str], unknown_users: set[str]) -> list[DeltaInstance]:
    logger.info(f"Parsing file {file_path.name}")
    with open(file_path, 'r') as file:
        content = file.read()
        soup = BeautifulSoup(content, "html.parser")
        regular_blocks = list(map(lambda block : block.prettify(), soup.find_all("div", class_="message default clearfix")))
        joined_blocks = list(map(lambda block : block.prettify(), soup.find_all("div", class_="message default clearfix joined")))
        blocks = regular_blocks + joined_blocks
        messages_meta_list = list(map(__parse_message_meta, blocks))
        messages_meta = {meta.id: meta for meta in messages_meta_list}
        parsed_messages = list(map(lambda body_block : __parse_message(body_block, messages_meta, usernames, unknown_users), blocks))
        result = list(filter(lambda delta : delta is not None, parsed_messages))
        logger.info(f"Successfully parsed {len(result)} blocks")
        return result

def parse_archive(path) -> Dataset:
    file = Path(path)

    if not file.exists():
        logger.error("File doesn't exist")
    if not file.is_dir():
        logger.error("File is not a folder")

    logger.info("Reading archive contents")
    usernames = __parse_usernames(file)
    message_files = list(file.glob("messages*.html"))

    logger.info(f"Found {len(message_files)} files")
    deltas: list[DeltaInstance] = []
    unknown_users = set()
    for html_file in message_files:
        deltas.extend(__parse_html(html_file, usernames, unknown_users))
    deltas.sort(key=lambda delta: delta.timestamp)
    return Dataset(deltas, unknown_users)
