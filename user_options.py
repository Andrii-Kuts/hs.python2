import messenger
import os
from pathlib import Path
from logger import logger

class UserOptions:
    def __init__(self):
        self.archive_name = None

options = None

def read_options():
    global options
    options = UserOptions()
    os.makedirs("cache", exist_ok=True)
    path = Path('cache/options.txt')
    path.touch(exist_ok=True)
    logger.info(f"Reading user options from file {path.name}")
    with open(path, 'r') as file:
        dct = {}
        for line in file:
            key,value = line.strip().split("=")
            dct[key] = value
        options.archive_name = dct.get('archive_name')

def write_options():
    global options
    os.makedirs("cache", exist_ok=True)
    path = Path('cache/options.txt')
    path.touch(exist_ok=True)
    logger.info(f"Writing user options to file {path.name}")
    with open(path, 'w') as file:
        if options.archive_name:
            file.write(f"archive_name={options.archive_name}\n")

def get_archive_name() -> str:
    global options
    if options.archive_name is not None:
        return options.archive_name
    options.archive_name = messenger.request_archive_path()
    write_options()
    return options.archive_name