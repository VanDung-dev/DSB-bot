import discord
from discord import app_commands
from discord.ext import commands
import logging

logger = logging.getLogger(__name__)


class SlashCommandSetup:
    """Lớp để quản lý thiết lập lệnh slash cho bot."""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.command_tree = bot.tree
        
    async def setup_all_commands(self) -> None:
        """Thiết lập tất cả các lệnh slash cho bot."""
        logger.info("Đang thiết lập các lệnh slash...")
        
        # Đăng ký các lệnh slash từ các cog
        await self._register_cog_commands()
        
        # Đồng bộ hóa các lệnh
        try:
            synced = await self.command_tree.sync()
            logger.info(f"Đã đồng bộ hóa thành công {len(synced)} lệnh slash")
        except Exception as e:
            logger.error(f"Lỗi khi đồng bộ hóa các lệnh slash: {e}")
            
    def register_command(self, command: app_commands.Command) -> None:
        """Đăng ký một lệnh slash đơn lẻ."""
        self.command_tree.add_command(command)
        logger.info(f"Đã đăng ký lệnh slash: {command.name}")
        
    async def register_guild_commands(self, guild_id: int) -> None:
        """Đăng ký các lệnh cho một guild cụ thể (để kiểm tra)."""
        guild = discord.Object(id=guild_id)
        try:
            synced = await self.command_tree.sync(guild=guild)
            logger.info(f"Đã đồng bộ hóa thành công {len(synced)} lệnh slash của guild cho guild {guild_id}")
        except Exception as e:
            logger.error(f"Lỗi khi đồng bộ hóa các lệnh slash của guild cho guild {guild_id}: {e}")
            
    async def _register_cog_commands(self) -> None:
        """Đăng ký các lệnh slash từ các cog."""
        for cog in self.bot.cogs.values():
            # Thêm các lệnh slash command từ cog vào command tree
            for attr_name in dir(cog):
                attr = getattr(cog, attr_name)
                if isinstance(attr, app_commands.Command):
                    # Kiểm tra xem lệnh đã được đăng ký chưa
                    if not self.command_tree.get_command(attr.name):
                        self.command_tree.add_command(attr)
                        logger.info(f"Đã đăng ký slash command từ cog: {attr.name}")


async def initialize_slash_commands(bot: commands.Bot) -> SlashCommandSetup:
    """Khởi tạo thiết lập lệnh slash."""
    slash_setup = SlashCommandSetup(bot)
    await slash_setup.setup_all_commands()
    return slash_setup