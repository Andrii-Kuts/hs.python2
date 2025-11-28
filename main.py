import messenger
from logger import logger
from dotenv import load_dotenv
from bot import PesunBot

def main():
    load_dotenv()
    messenger.notify_app_started()
    bot = PesunBot()
    try:
        logger.info("Starting telegram bot")
        bot.run()
    finally:
        bot.stop()
        logger.info("Telegram bot was stopped")

if __name__ == "__main__":
    main()
    