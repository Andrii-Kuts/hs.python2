from typing import Any, Callable, Coroutine
import requests
import telegram
from telegram import Chat, Message, Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, Application, filters, MessageHandler
import os
from classes import DeltaInstance
from parse_archive import parse_zip
from database.database import Database
import uuid
from analytics import Analytics
from plotter import PlotterPool
from asyncio import get_event_loop
from logger import logger
from parse_message import parse_message

class PesunBot:
    class RequestedUsernameInfo:
        def __init__(self, message_id: int, callback: Callable[[str], Coroutine[Any, Any, None]]):
            self.message_id = message_id
            self.callback = callback

    def __init__(self):
        self.import_users: set[tuple[int, int]] = set()
        self.requested_usernames: dict[tuple[int, str], PesunBot.RequestedUsernameInfo] = dict()
        self.usernames: dict[str, int] = {}
        self.app = ApplicationBuilder().token(os.getenv("TELEGRAM_BOT_KEY")).post_init(self.init_bot).build()

        self.app.add_handler(CommandHandler("import", self.handle_import, filters.ALL))
        self.app.add_handler(CommandHandler("analytics", self.handle_analytics, filters.ALL))
        self.app.add_handler(MessageHandler(filters.ALL, self.handle_chat_message))

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

    async def request_username(self, chat: Chat, user_handle: str, callback: Callable[[str], Coroutine[Any, Any, None]]):
        chat_id = chat.id
        key = (chat_id, user_handle)
        info = self.requested_usernames.get(key)
        if info is not None:
            previous_callback = info.callback
            async def run_callback(username: str):
                await previous_callback(username)
                await callback(username)
            info.callback = run_callback
            return
        request_message = await chat.send_message(f"@{user_handle} Please respond to this message with your pesun username!")
        info = PesunBot.RequestedUsernameInfo(request_message.id, callback)
        self.requested_usernames[key] = info

    async def handle_pesun_bot_message(self, message: Message, context: ContextTypes.DEFAULT_TYPE) -> None:
        parse_message_result = parse_message(message.text)
        if parse_message_result == None:
            return
        
        async def append_delta(username: str):
            chat_id = message.chat.id
            delta = DeltaInstance(
                username,
                message.date,
                parse_message_result.delta,
                parse_message_result.wait_minutes,
                parse_message_result.delta == 0,
                parse_message_result.new_length
            )
            result = await self.append(chat_id, delta)
            if not result:
                logger.warning("Warning! Couldn't append delta")
        
        if parse_message_result.username is not None:
            await append_delta(parse_message_result.username)
            return
        
        user_id = self.usernames.get(parse_message_result.user_handle)
        if user_id is None:
            logger.warning(f"Warning! User is unknown for handle = {parse_message_result.user_handle}")
            await self.request_username(message.chat, parse_message_result.user_handle, append_delta)
            return
        db = await Database.get_instance()
        username = await db.get_username(message.chat.id, user_id)
        if username is not None:
            await append_delta(username)
        else:
            await self.request_username(message.chat, parse_message_result.user_handle, append_delta)

    async def handle_username_provided(self, message: Message, context: ContextTypes.DEFAULT_TYPE) -> None:
        chat_id = message.chat.id
        user_handle = message.from_user.username
        key = (chat_id, user_handle)
        info = self.requested_usernames.get(key)
        reply_id = message.reply_to_message.id if message.reply_to_message else None
        if reply_id != info.message_id:
            return
        username = message.text
        db = await Database.get_instance()
        await db.set_username(chat_id, message.from_user.id, username)
        await info.callback(username)
        self.requested_usernames.pop(key)

    async def handle_response_message(self, message: Message, context: ContextTypes.DEFAULT_TYPE) -> None:
        chat_id = message.chat.id
        user_handle = message.from_user.username
        key = (chat_id, user_handle)
        if key in self.requested_usernames:
            await self.handle_username_provided(message, context)
        return

    async def handle_chat_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        self.usernames[update.effective_user.username] = update.effective_user.id
        user_id = (update.effective_user.id, update.effective_chat.id)
        if user_id in self.import_users:
            await self.handle_import_file(update, context)
            return
        reply = update.message.reply_to_message
        if not reply or reply.chat.id != update.effective_chat.id:
            return
        pesun_bot_username = "kraft28_bot"
        from_username = reply.from_user.username if reply.from_user else None
        
        if reply.from_user.id == context.bot.id:
            await self.handle_response_message(update.message, context)
            return
        if from_username == pesun_bot_username or os.getenv("ALLOW_NON_BOT_MESSAGES") == "TRUE":
            await self.handle_pesun_bot_message(reply, context)
            return

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
            return str(number) + "%  " + ("🟦" * blocks) + ("⬛️" * (cnt-blocks))
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
        response = await response.edit_text(f"⏱️  Writing into database")
        db = await Database.get_instance()
        result = await db.import_dataset(update.effective_chat.id, dataset)
        if not result:
            response = await response.edit_text("❌  Something went wrong while writing into database")
            return
        response = await response.edit_text(f"⏱️  Building analytics")
        analytics = Analytics.from_dataset(dataset)
        result = await db.write_analytics(update.effective_chat.id, analytics)
        if not result:
            response = await response.edit_text("❌  Something went wrong while building analytics")
            return
        response = await response.edit_text(f"✅  Archive has been successfuly imported!")

    async def handle_import(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        self.import_users.add((update.effective_user.id, update.effective_chat.id))
        await update.message.reply_text(f"Now send the zip archive")

    async def handle_analytics(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        response = await update.message.reply_text(f"⏱️  Creating dashboard")
        plotterData = await PlotterPool.get_instance().get_or_start_plotter(update.effective_chat.id)
        response = await response.edit_text(f"📊  Link to analytics:\n\n{os.getenv("DASH_LINK")}:{os.getenv("DASH_PORT")}{plotterData.path}")

    async def append(self, group_id: int, delta: DeltaInstance):
        db = await Database.get_instance()
        result = await db.append_delta(group_id, delta)
        if not result:
            return False
        plotter_data = PlotterPool.get_instance().get_plotter(group_id)
        if plotter_data is not None:
            path = plotter_data.path
            post_response = requests.post(f"{os.getenv("DASH_LINK")}:{os.getenv("DASH_PORT")}{path}update")
            if post_response.status_code != 200:
                return False
        return True

    async def stop_async(self):
        await PlotterPool.get_instance().stop_plotters()

    def stop(self):
        loop = get_event_loop()
        loop.run_until_complete(self.stop_async())
        loop.close()