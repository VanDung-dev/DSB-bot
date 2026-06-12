import discord
from discord import app_commands
from discord.ext import commands
import logging

logger = logging.getLogger(__name__)


class SlashCommandSetup:
    """Class managing slash command registration for the bot."""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.command_tree = bot.tree
        
    async def setup_all_commands(self) -> None:
        """Set up all slash commands."""
        logger.info("Setting up slash commands...")
        
        await self._register_cog_commands()
        
        try:
            synced = await self.command_tree.sync()
            logger.info(f"Successfully synced {len(synced)} slash commands")
        except Exception as e:
            logger.error(f"Error syncing slash commands: {e}")
            
    def register_command(self, command: app_commands.Command) -> None:
        """Register a single slash command."""
        self.command_tree.add_command(command)
        logger.info(f"Registered slash command: {command.name}")
        
    async def register_guild_commands(self, guild_id: int) -> None:
        """Register commands for a specific guild (for testing)."""
        guild = discord.Object(id=guild_id)
        try:
            synced = await self.command_tree.sync(guild=guild)
            logger.info(f"Successfully synced {len(synced)} guild slash commands for guild {guild_id}")
        except Exception as e:
            logger.error(f"Error syncing guild slash commands for guild {guild_id}: {e}")
            
    async def _register_cog_commands(self) -> None:
        """Register slash commands from cogs into the command tree."""
        for cog in self.bot.cogs.values():
            for attr_name in dir(cog):
                attr = getattr(cog, attr_name)
                if isinstance(attr, app_commands.Command):
                    if not self.command_tree.get_command(attr.name):
                        self.command_tree.add_command(attr)
                        logger.info(f"Registered slash command from cog: {attr.name}")


async def initialize_slash_commands(bot: commands.Bot) -> SlashCommandSetup:
    """Initialize slash command setup."""
    slash_setup = SlashCommandSetup(bot)
    await slash_setup.setup_all_commands()
    return slash_setup
