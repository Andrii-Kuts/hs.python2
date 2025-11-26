import telegram
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, Application, filters, MessageHandler
import os
from dotenv import load_dotenv
from parse_archive import parse_zip
from database import Database
import uuid
from analytics import Analytics
from plotter import PlotterPool
from asyncio import CancelledError, get_event_loop, sleep, create_task

class PesunBot:
    def __init__(self):
        self.import_users: set[tuple[int, int]] = set()
        self.app = ApplicationBuilder().token(os.getenv("TELEGRAM_BOT_KEY")).post_init(self.init_bot).build()

        self.app.add_handler(CommandHandler("import", self.handle_import, filters.ALL))
        self.app.add_handler(CommandHandler("analytics", self.handle_analytics, filters.ALL))
        self.app.add_handler(MessageHandler(filters.ALL, self.handle_import_file))

    def run(self):
        self.app.run_polling(close_loop=False)

    async def init_bot(self, app: Application):
        await Database.get_instance()
        bot: telegram.Bot = app.bot
        commands = [
            telegram.BotCommand("/import", "Send chat history as a zip archive to import entire pesun data"),
            telegram.BotCommand("/analytics", "Builds an app with analytics and sends a link to it"),
        ]
        await bot.set_my_commands(commands)

    async def handle_import_file(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user_id = (update.effective_user.id, update.effective_chat.id)
        if user_id not in self.import_users:
            return
        self.import_users.remove(user_id)
        # Check if a document was sent
        document = update.message.document
        if not document:
            await update.message.reply_text("Please send a file after sending the /import command")
            return

        response = await update.message.reply_text(f"⏱️  Downloading...")
        file_id = document.file_id
        telegram_file = await context.bot.get_file(file_id)
        name = uuid.uuid4().hex
        file_path = f"cache/downloads/{name}"
        os.makedirs("cache/downloads", exist_ok=True)
        file = await telegram_file.download_to_drive(file_path)

        def get_progress_blocks_cnt(percent: float):
            cnt = 10
            return int(percent / cnt)
        def get_progress_text(percent: float):
            cnt = 10
            blocks = get_progress_blocks_cnt(percent)
            number = blocks * cnt
            return str(number) + "%  " + ("🟦" * blocks)
        response = await response.edit_text(f"⏱️  Parsing {get_progress_text(0)}")
        parsing_progress_cnt = get_progress_blocks_cnt(0)
        dataset = None
        async for parse_result in parse_zip(file):
            if parse_result.isDone():
                dataset = parse_result.dataset
                break
            else:
                percent = parse_result.file_number/parse_result.total_files * 100
                new_blocks_cnt = get_progress_blocks_cnt(percent)
                if parsing_progress_cnt != new_blocks_cnt:
                    response = await response.edit_text(f"⏱️  Parsing {get_progress_text(percent)}")
                    parsing_progress_cnt = new_blocks_cnt
        if dataset is None:
            response = await response.edit_text("❌  Could not parse the file. Are you sure its a correct zip archive?")
            return
        db = await Database.get_instance()
        result = await db.import_dataset(update.effective_chat.id, dataset)
        if result:
            response = await response.edit_text(f"✅  File '{document.file_name}' received and saved!")
        else:
            response = await response.edit_text("❌  Something went wrong while parsing the archive")

    async def handle_import(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        self.import_users.add((update.effective_user.id, update.effective_chat.id))
        await update.message.reply_text(f"Now send the zip archive")

    async def handle_analytics(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        response = await update.message.reply_text(f"⏱️  Reading the dataset...")
        db = await Database.get_instance()
        dataset = await db.read_dataset(update.effective_chat.id)
        if dataset is None:
            response = await response.edit_text("❌  Something went wrong while reading the dataset. Are you sure you've imported an archive?")
            return
        response = await response.edit_text(f"⏱️  Building analytics...")
        analytics = Analytics(dataset)
        response = await response.edit_text(f"⏱️  Starting dash app...")
        plotterData = await PlotterPool.get_instance().get_plotter(update.effective_chat.id, analytics)
        response = await response.edit_text(f"📊  Link to analytics:\n\n{os.getenv("DASH_LINK")}:{os.getenv("DASH_PORT")}{plotterData.path}")

    async def stop_async(self):
        await PlotterPool.get_instance().stop_plotters()

    def stop(self):
        loop = get_event_loop()
        loop.run_until_complete(self.stop_async())
        loop.close()