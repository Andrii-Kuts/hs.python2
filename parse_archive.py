from logger import logger
from classes import DeltaInstance
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
    if not file_path.is_file():
        logger.error("Nicknames file is not a file")
    logger.info(f"Parsing nicknames file {file_path.name}")
    try:
        with open(file_path, 'r') as file:
            content = file.read()
            lines = content.splitlines()
            result = {}
            for line in lines:
                handle, user = line.split()
                result[handle] = user
            return result

    except Exception as e:
        logger.error(f"Exception while parsing nicknames file {file_path.name}", exc_info=True)
        return []
    
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

def __parse_length_change(message: str) -> int:
    length_change = None
    grow = re.search(r'виріс на (\d+)', message)
    shrink = re.search(r'скоротився на (\d+)', message)
    length_change = int(grow.group(1)) if grow else (-int(shrink.group(1)) if shrink else None)
    return length_change

def __parse_message_meta(message: str) -> MessageMeta:
    id = __parse_message_id(message)
    if id is None:
        return None
    from_user = __parse_from_user(message)
    return MessageMeta(from_user, id)

def __parse_user(message: str, usernames: dict[str, str]) -> str:
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
    # No handle, user name might be provided directly
    else:
        name_match = re.search(r'<div class="text">\s*([^<>,]+),\s*твій песюн', message)
        user = name_match.group(1).strip() if name_match else None
    return user

def __parse_message(message: str, messages_meta: dict[str, MessageMeta], usernames: dict[str, str]) -> DeltaInstance:
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
    user = __parse_user(message, usernames)
    if user is None:
        return None
    return DeltaInstance(user, timestamp, length_change)

def __parse_html(file_path: Path, usernames: dict[str, str]) -> list[DeltaInstance]:
    logger.info(f"Parsing file {file_path.name}")
    try:
        with open(file_path, 'r') as file:
            content = file.read()
            soup = BeautifulSoup(content, "html.parser")
            regular_blocks = list(map(lambda block : block.prettify(), soup.find_all("div", class_="message default clearfix")))
            joined_blocks = list(map(lambda block : block.prettify(), soup.find_all("div", class_="message default clearfix joined")))
            blocks = regular_blocks + joined_blocks
            messages_meta_list = list(map(__parse_message_meta, blocks))
            messages_meta = {meta.id: meta for meta in messages_meta_list}
            parsed_messages = list(map(lambda body_block : __parse_message(body_block, messages_meta, usernames), blocks))
            result = list(filter(lambda delta : delta is not None, parsed_messages))
            logger.info(f"Successfully parsed {len(result)} blocks")
            return result

    except Exception as e:
        logger.error(f"Exception while parsing file {file_path.name}", exc_info=True)
        return []

def parse_archive(path) -> list[DeltaInstance]:
    file = Path(path)

    if not file.exists():
        logger.error("File doesn't exist")
    if not file.is_dir():
        logger.error("File is not a folder")

    logger.info("Reading archive contents")
    usernames = __parse_usernames(file)
    message_files = list(file.glob("messages*.html"))

    logger.info(f"Found {len(message_files)} files")
    result = []
    for html_file in message_files:
        result.extend(__parse_html(html_file, usernames))
    return result
