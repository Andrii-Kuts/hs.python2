from logger import logger
from datetime import datetime, timezone, timedelta
import pytz
from classes import DeltaInstance

def normalize_date(date: datetime):
    tz = timezone(timedelta(hours=0))
    return date.astimezone(tz)
    
def is_legacy(date: datetime):
    cutoff_date = datetime(day=28, month=11, year=2022, tzinfo=timezone.utc)
    return date < cutoff_date

def get_dts(date: datetime):
    tz = pytz.timezone("Europe/Kyiv")
    date_tz = date.astimezone(tz)
    dts = int(round(date_tz.dst().total_seconds() / (60*60)))
    return dts

def same_section(date1: datetime, date2: datetime):
    if is_legacy(date1) != is_legacy(date2):
        return False
    dts1 = get_dts(date1)
    dts2 = get_dts(date2)
    return dts1 == dts2

def next_pesun_date(date: datetime):
    tz = pytz.timezone("Europe/Kyiv")
    date_tz = date.astimezone(tz)
    shift = 23 if is_legacy(date) else 2
    dts = get_dts(date_tz)
    target = (dts*2 + shift)%24
    next_date = date_tz.replace(hour=target, minute=0, second=0, microsecond=0)
    while next_date <= date_tz:
        next_date += timedelta(days=1)
    return next_date

def same_pesun_day(prev: datetime, cur: datetime) -> bool:
    nx1 = next_pesun_date(prev)
    nx2 = next_pesun_date(cur)
    return nx1 == nx2

def consecutive_pesun_days(prev: datetime, cur: datetime) -> bool:
    nx1 = next_pesun_date(next_pesun_date(prev))
    nx2 = next_pesun_date(cur)
    return nx1 == nx2

def apply_delta(length: int, delta: DeltaInstance) -> int:
    return 0 if delta.is_reset else length+delta.delta

def format_plural(val: int, name: str):
    return f"{val} {name}{"" if val == 1 else "s"}"

def format_date(date: datetime) -> str:
    return date.strftime("%d.%m.%Y")