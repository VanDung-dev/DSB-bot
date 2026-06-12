import asyncio
import logging
import sys

import colorlog
import discord
from discord.ext import commands

from cogs.assistant import Assistant
from cogs.config import Config, get_config
from cogs.help import Help
from cogs.r34 import R34

from slash_setup import initialize_slash_commands


if sys.version_info < (3, 11):
    print("Requires Python 3.11 or higher.")
    sys.exit(1)

stream_handler = colorlog.StreamHandler()
stream_handler.setFormatter(
    colorlog.ColoredFormatter(Config.LOG_FORMAT, datefmt=Config.LOG_DATE, log_colors=Config.LOG_COLORS)
)

logger = logging.getLogger()
logger.setLevel(Config.LOG_LEVEL)
logger.addHandler(stream_handler)

intents = discord.Intents.default()
intents.message_content = True  # type: ignore[attr-defined]

bot = commands.Bot(command_prefix=Config.COMMAND_PREFIX, intents=intents, help_command=None)


@bot.event
async def on_ready() -> None:
    """Event fired when the bot is ready."""
    user = bot.user
    if user:
        logger.info(f"🤖 Bot logged in successfully: {user} (ID: {user.id})")
    await initialize_slash_commands(bot)
    logger.info("✅ Slash commands initialized")


@bot.event
async def on_command_error(ctx, error) -> None:
    if isinstance(error, commands.CommandNotFound):
        return
    raise error


async def setup_cogs() -> None:
    """Register all cogs with the bot."""
    cogs: list[commands.Cog] = [
        Help(bot),
        Assistant(bot),
        R34(bot),
    ]
    for cog in cogs:
        try:
            await bot.add_cog(cog)
            logger.info(f"✅ Registered cog: {cog.__class__.__name__}")
        except Exception as e:
            logger.error(f"❌ Error registering cog {cog.__class__.__name__}: {e}")


async def main() -> None:
    """Main entry point to start the bot."""
    try:
        await setup_cogs()
        config = get_config()
        await bot.start(config.discord_token)
    except Exception as e:
        logger.error(f"❌ Error starting bot: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
