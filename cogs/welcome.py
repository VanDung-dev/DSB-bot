import logging
from typing import Optional

import discord
from discord.ext import commands

# Cấu hình logger
logger = logging.getLogger(__name__)


class Welcome(commands.Cog):
    """Cog xử lý tin nhắn chào mừng và tạm biệt thành viên."""

    def __init__(self, bot: commands.Bot) -> None:
        """Khởi tạo cog Welcome.

        Args:
            bot: Đối tượng bot Discord.
        """
        self.bot = bot

    @staticmethod
    def _find_suitable_channel(guild: discord.Guild, keywords: list) -> Optional[discord.TextChannel]:
        """Tìm channel phù hợp để gửi tin nhắn.

        Args:
            guild: Server Discord.
            keywords: Danh sách từ khóa để ưu tiên tìm channel (ví dụ: ['general', 'welcome']).

        Returns:
            Channel văn bản phù hợp hoặc None nếu không tìm thấy.
        """
        for channel in guild.text_channels:
            if any(keyword in channel.name.lower() for keyword in keywords):
                if channel.permissions_for(guild.me).send_messages:
                    return channel
        for channel in guild.text_channels:
            if channel.permissions_for(guild.me).send_messages:
                return channel
        return None

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        """Sự kiện khi thành viên mới tham gia server.

        Args:
            member: Thành viên vừa tham gia.
        """
        logger.info(
            f"🆕 Thành viên mới {member.name} (ID: {member.id}) đã tham gia server {member.guild.name}"
        )
        channel = self._find_suitable_channel(
            member.guild, ["general", "welcome", "chào-mừng", "lobby"]
        )
        if not channel:
            logger.warning(
                f"⚠️ Không tìm thấy channel nào để gửi tin nhắn chào mừng trong {member.guild.name}"
            )
            return

        embed = discord.Embed(
            title="🎉 Chào mừng thành viên mới!",
            description=f"Xin chào {member.mention}! Chào mừng bạn đến với **{member.guild.name}**! 🎊",
            color=0x00FF88,
        )
        embed.add_field(
            name="🤖 Về DSB Bot",
            value="Tôi là DSB Bot, có thể giúp bạn:\n• Phát nhạc với `!play`\n• Chat AI với `!ai`\n• Xem hướng dẫn với `!help`",
            inline=False,
        )
        embed.add_field(
            name="📋 Bắt đầu",
            value="Hãy gõ `!help` để xem tất cả lệnh có sẵn!",
            inline=False,
        )
        embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
        embed.set_footer(text=f"Thành viên thứ {member.guild.member_count} • {member.guild.name}")
        embed.timestamp = discord.utils.utcnow()

        try:
            await channel.send(embed=embed)
            logger.info(f"✅ Đã gửi tin nhắn chào mừng cho {member.name} trong {channel.name}")
        except discord.Forbidden:
            logger.warning(f"⚠️ Không có quyền gửi tin nhắn trong {channel.name}")
        except Exception as e:
            logger.error(f"❌ Lỗi khi gửi tin nhắn chào mừng: {e}")

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member) -> None:
        """Sự kiện khi thành viên rời khỏi server.

        Args:
            member: Thành viên vừa rời đi.
        """
        logger.info(
            f"👋 Thành viên {member.name} (ID: {member.id}) đã rời khỏi server {member.guild.name}"
        )
        channel = self._find_suitable_channel(
            member.guild, ["general", "goodbye", "tạm-biệt", "lobby", "log"]
        )
        if not channel:
            logger.warning(
                f"⚠️ Không tìm thấy channel nào để gửi tin nhắn tạm biệt trong {member.guild.name}"
            )
            return

        embed = discord.Embed(
            title="👋 Tạm biệt!",
            description=f"**{member.name}** đã rời khỏi server. Chúc bạn may mắn! 🍀",
            color=0xFF6B6B,
        )
        embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
        embed.set_footer(text=f"Còn lại {member.guild.member_count} thành viên • {member.guild.name}")
        embed.timestamp = discord.utils.utcnow()

        try:
            await channel.send(embed=embed)
            logger.info(f"✅ Đã gửi tin nhắn tạm biệt cho {member.name} trong {channel.name}")
        except discord.Forbidden:
            logger.warning(f"⚠️ Không có quyền gửi tin nhắn trong {channel.name}")
        except Exception as e:
            logger.error(f"❌ Lỗi khi gửi tin nhắn tạm biệt: {e}")

    @commands.command(name="setwelcome")
    @commands.has_permissions(administrator=True)
    async def set_welcome_channel(
        self, ctx: commands.Context, channel: Optional[discord.TextChannel] = None
    ) -> None:
        """Thiết lập channel cho tin nhắn chào mừng (chỉ admin).

        Args:
            ctx: Ngữ cảnh lệnh Discord.
            channel: Channel văn bản để thiết lập (mặc định là channel hiện tại).
        """
        logger.info(f"{ctx.author} (ADMIN) gọi lệnh !setwelcome trong kênh {ctx.channel}")
        channel = channel or ctx.channel
        if not channel.permissions_for(ctx.guild.me).send_messages:
            await ctx.send(f"❌ Bot không có quyền gửi tin nhắn trong {channel.mention}")
            return

        embed = discord.Embed(
            title="✅ Đã thiết lập channel chào mừng",
            description=f"Channel {channel.mention} sẽ được ưu tiên cho tin nhắn chào mừng.",
            color=0x00FF88,
        )
        embed.add_field(
            name="💡 Lưu ý",
            value="Bot sẽ tự động tìm channel phù hợp nếu không tìm thấy channel được thiết lập.",
            inline=False,
        )
        await ctx.send(embed=embed)
        logger.info(f"✅ {ctx.author} đã thiết lập {channel.name} làm welcome channel")

    @commands.command(name="testwelcome")
    @commands.has_permissions(administrator=True)
    async def test_welcome(self, ctx: commands.Context, member: Optional[discord.Member] = None) -> None:
        """Kiểm tra tin nhắn chào mừng (chỉ admin).

        Args:
            ctx: Ngữ cảnh lệnh Discord.
            member: Thành viên để kiểm tra (mặc định là người gọi lệnh).
        """
        logger.info(f"{ctx.author} (ADMIN) gọi lệnh !testwelcome trong kênh {ctx.channel}")
        member = member or ctx.author
        await self.on_member_join(member)
        await ctx.send(f"✅ Đã test tin nhắn chào mừng cho {member.mention}")

    @set_welcome_channel.error
    @test_welcome.error
    async def welcome_command_error(self, ctx: commands.Context, error: Exception) -> None:
        """Xử lý lỗi cho các lệnh chào mừng.

        Args:
            ctx: Ngữ cảnh lệnh Discord.
            error: Lỗi được ném ra.
        """
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ Bạn cần quyền Administrator để sử dụng lệnh này.")
            logger.warning(f"⚠️ {ctx.author} cố gắng dùng lệnh admin mà không có quyền")