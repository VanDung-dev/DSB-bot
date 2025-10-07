import asyncio
import logging
import os
import sys
from typing import List

import colorlog
import discord
from discord.ext import commands
from dotenv import load_dotenv

from cogs.assistant import Assistant
from cogs.help import Help
from cogs.image import ImageSearch
from cogs.moderation import Moderation
from cogs.music import MusicSearch
from cogs.welcome import Welcome
from cogs.speak import Speaking

from slash_setup import initialize_slash_commands


# Kiểm tra phiên bản Python tối thiểu
if sys.version_info < (3, 11):
    print("Yêu cầu Python 3.11 trở lên.")
    sys.exit(1)

# Tải biến môi trường từ file .env
load_dotenv()

# Cấu hình logging với màu sắc
LOG_FORMAT = "%(log_color)s[%(asctime)s] [%(levelname)s] %(name)s: %(message)s"
LOG_DATE = "%Y-%m-%d %H:%M:%S"
LOG_COLORS = {
    "DEBUG": "cyan",
    "INFO": "green",
    "WARNING": "yellow",
    "ERROR": "red",
    "CRITICAL": "bold_red",
}

# Thiết lập handler cho terminal
stream_handler = colorlog.StreamHandler()
stream_handler.setFormatter(
    colorlog.ColoredFormatter(LOG_FORMAT, datefmt=LOG_DATE, log_colors=LOG_COLORS)
)

# Cấu hình root logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(stream_handler)

# Thiết lập intents cho bot
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
intents.members = True

# Khởi tạo bot với intents
bot = commands.Bot(command_prefix="", intents=intents, help_command=None)


@bot.event
async def on_ready() -> None:
    """Sự kiện khi bot sẵn sàng hoạt động."""
    logger.info(f"🤖 Bot đã đăng nhập thành công: {bot.user} (ID: {bot.user.id})")
    # Khởi tạo lệnh slash
    slash_setup = await initialize_slash_commands(bot)
    logger.info("✅ Đã khởi tạo slash commands")


async def setup_cogs() -> None:
    """Đăng ký các cog cho bot."""
    cogs: List[commands.Cog] = [
        MusicSearch(bot),
        Help(bot),
        Assistant(bot),
        Welcome(bot),
        ImageSearch(bot),
        Moderation(bot),
        Speaking(bot),
    ]
    for cog in cogs:
        try:
            await bot.add_cog(cog)
            logger.info(f"✅ Đã đăng ký cog: {cog.__class__.__name__}")
        except Exception as e:
            logger.error(f"❌ Lỗi khi đăng ký cog {cog.__class__.__name__}: {e}")


async def main() -> None:
    """Hàm chính để khởi động bot."""
    try:
        await setup_cogs()
        discord_token = os.getenv("KEY_DISCORD")
        if not discord_token:
            logger.error("❌ KEY_DISCORD không được thiết lập trong biến môi trường")
            return
        await bot.start(discord_token)
    except Exception as e:
        logger.error(f"❌ Lỗi khi khởi động bot: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())