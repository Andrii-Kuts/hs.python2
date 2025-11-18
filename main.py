import messenger
from logger import logger
from parse_archive import parse_archive
from analytics import build_analytics

# EXPERIMENTAL Saves parsed data into a database
def migrate_to_db():
    ...

# Generates analytics based on the data
def generate_analystics():
    ...

# Shows current users leaderboard
def leaderboard():
    ...

# Shows individual user analytics
def user_analytics(used):
    ...

# Shows timeline of best users
def timeline():
    ...

# Shows global analytics, like the total number of interactions
def global_statistics():
    ...

path = messenger.request_archive_path()
deltas = parse_archive(path)
for delta in deltas:
    if delta.user == "@golybchuk":
        logger.info(f"{delta.timestamp}: {delta.delta}")
        
analytics = build_analytics(deltas)

for user in analytics.get_users():
    length = analytics.get_user_length(user)
    print(f"User: {user}, Length: {length}")
    