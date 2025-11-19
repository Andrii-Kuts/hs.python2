import messenger
from logger import logger
from analytics import build_analytics
from user_options import read_options
from dataset import get_dataset
import plotter

# EXPERIMENTAL Saves parsed data into a database
def migrate_to_db():
    ...

def main():
    messenger.notify_app_started()
    read_options()
    dataset = get_dataset()
    if len(dataset.unknown_users) > 0:
        messenger.notify_unknown_users(dataset.unknown_users)

    analytics = build_analytics(dataset)
    plotter.init(analytics)

if __name__ == "__main__":
    main()
    