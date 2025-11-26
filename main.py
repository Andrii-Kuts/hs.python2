import messenger
from logger import logger
from analytics import build_analytics
from user_options import read_options
from dataset import get_dataset
import plotter
from dotenv import load_dotenv
import database.database as database
import asyncio
from bot import PesunBot

def main():
    load_dotenv()
    messenger.notify_app_started()
    read_options()
    bot = PesunBot()
    try:
        logger.info("Starting telegram bot")
        bot.run()
    finally:
        bot.stop()
        logger.info("Telegram bot was stopped")

if __name__ == "__main__":
    main()
    