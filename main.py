import messenger
from logger import logger
from analytics import build_analytics
from user_options import read_options
from dataset import get_dataset
import plotter

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

read_options()
dataset = get_dataset()
if len(dataset.unknown_users) > 0:
    messenger.notify_unknown_users(dataset.unknown_users)

analytics = build_analytics(dataset)

plotter.init(analytics)

# for user in analytics.get_users():
#     length = analytics.get_user_length(user)
#     print(f"User: {user}, Length: {length}")
    