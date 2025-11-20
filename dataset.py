from classes import Dataset, DeltaInstance
from logger import logger
import os
from pathlib import Path
import datetime
from parse_archive import parse_archive
import user_options
import messenger

def __write_delta(file, delta: DeltaInstance):
    file.write(f"{delta.timestamp.isoformat()} {delta.user} {delta.delta} {delta.wait_minutes}\n")

def __read_delta(line: str) -> DeltaInstance:
    timestamp_str,user,delta_str,wait_time_str = line.split()
    timestamp = datetime.datetime.fromisoformat(timestamp_str)
    delta = int(delta_str)
    wait_time = int(wait_time_str)
    return DeltaInstance(user, timestamp, delta, wait_time)

def save_dataset(dataset: Dataset):
    os.makedirs("cache", exist_ok=True)
    path = Path('cache/dataset.txt')
    path.touch(exist_ok=True)
    logger.info(f"Saving dataset to file {path.name}")
    with open(path, 'w') as file:
        for delta in dataset.deltas:
            __write_delta(file, delta)
        logger.info(f"Successfuly written {len(dataset.deltas)} deltas to a file")

def load_dataset() -> Dataset:
    path = Path('cache/dataset.txt')
    if not path.exists() or not path.is_file():
        return None
    logger.info(f"Reading dataset from file {path.name}")
    with open(path, 'r') as file:
        deltas = []
        for line in file:
            deltas.append(__read_delta(line))
        logger.info(f"Successfuly read {len(deltas)} deltas from a file")
        return Dataset(deltas, [])
    
def exists() -> bool:
    path = Path('cache/dataset.txt')
    if not path.exists() or not path.is_file():
        return False
    return True
    
def get_dataset() -> Dataset:
    if exists():
        logger.info("Dataset file exists, getting it from there")
        return load_dataset()
    else:
        logger.info("Dataset file doesn't exist, parsing")
        archive_name = user_options.get_archive_name()
        messenger.archive_parsing()
        dataset = parse_archive(archive_name)
        save_dataset(dataset)
        messenger.archive_parsed()
        return dataset