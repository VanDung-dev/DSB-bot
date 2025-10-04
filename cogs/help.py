import logging
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands

# Cấu hình logger
logger = logging.getLogger(__name__)

class Help(commands.Cog):
    """Cog cung cấp các lệnh trợ giúp và thông tin về bot."""

    def __init__(self, bot: commands.Bot) -> None:
        """Khởi tạo cog Help.

        Args:
            bot: Đối tượng bot Discord.
        """
        self.bot = bot

    @commands.command(name="hello")
    async def hello(self, ctx: commands.Context) -> None:
        """Chào hỏi với bot.

        Args:
            ctx: Ngữ cảnh lệnh Discord.
        """
        logger.info(f"{ctx.author} gọi lệnh !hello trong kênh {ctx.channel}")
        await ctx.send(
            f"Chào {ctx.author.mention}, tôi là DSB Bot! Gõ `!help` để xem các lệnh nhé! 😄"
        )

    @app_commands.command(name="hello", description="Chào hỏi với bot")
    async def slash_hello(self, interaction: discord.Interaction) -> None:
        """Phiên bản lệnh chém của Hello."""
        logger.info(f"{interaction.user} gọi lệnh /hello trong kênh {interaction.channel}")
        await interaction.response.send_message(
            f"Chào {interaction.user.mention}, tôi là DSB Bot! Hãy dùng `/help` để xem các lệnh nhé! 😄"
        )

    @staticmethod
    def _basic_help() -> discord.Embed:
        """Tạo embed cho danh mục lệnh cơ bản.

        Returns:
            Embed chứa thông tin lệnh cơ bản.
        """
        embed = discord.Embed(
            title="📋 Lệnh cơ bản",
            description="Các lệnh cơ bản để tương tác với DSB Bot.",
            color=0x00FF88,
        )
        embed.add_field(
            name="Lệnh",
            value=(
                "`/hello` - Chào hỏi với bot\n"
                "`/help [danh mục]` - Hiển thị hướng dẫn (gõ `/help` để xem danh sách danh mục)"
            ),
            inline=False,
        )
        return embed

    @staticmethod
    def _music_help() -> discord.Embed:
        """Tạo embed cho danh mục lệnh nhạc."""
        embed = discord.Embed(
            title="🎵 Lệnh nhạc",
            description="Các lệnh để phát và quản lý nhạc từ **YouTube** hoặc **Spotify**.",
            color=0x00FF88,
        )
        embed.add_field(
            name="Lệnh",
            value=(
                "`/play <URL/tìm kiếm>` - Phát nhạc hoặc thêm vào hàng đợi\n"
                "`/queue` - Xem danh sách hàng đợi\n"
                "`/nowplaying` - Xem bài đang phát\n"
                "`/skip` - Bỏ qua bài hiện tại\n"
                "`/pause` - Tạm dừng nhạc\n"
                "`/resume` - Tiếp tục phát nhạc\n"
                "`/clear` - Xóa toàn bộ hàng đợi\n"
                "`/remove <số>` - Xóa bài ở vị trí cụ thể\n"
                "`/stop` - Dừng nhạc và xóa hàng đợi\n"
                "`/leave` - Bot rời voice channel"
            ),
            inline=False,
        )
        embed.add_field(
            name="💡 Ghi chú",
            value=(
                "• Bạn cần ở trong **voice channel** để sử dụng các lệnh nhạc.\n"
                "• Với album/playlist Spotify: bot sẽ phát ngay bài đầu tiên, "
                "các bài còn lại được thêm vào hàng đợi im lặng (không spam chat)."
            ),
            inline=False,
        )
        return embed

    @staticmethod
    def _speak_help() -> discord.Embed:
        """Tạo embed cho danh mục lệnh nói (text-to-speech).

        Returns:
            Embed chứa thông tin lệnh nói.
        """
        embed = discord.Embed(
            title="📢 Lệnh nói (Text-to-Speech)",
            description="Các lệnh để chuyển văn bản thành giọng nói.",
            color=0x00FF88,
        )
        embed.add_field(
            name="Lệnh",
            value=(
                "`/say <văn bản>` - Chuyển văn bản thành giọng nói\n"
            ),
            inline=False,
        )
        embed.add_field(
            name="Cách sử dụng",
            value=(
                "• Bạn cần ở trong **voice channel** để sử dụng lệnh này.\n"
                "• Bot sẽ tự động kết nối vào voice channel của bạn.\n"
                "• Bot sẽ phát âm thanh tương ứng với văn bản bạn nhập.\n"
                "• Ngôn ngữ mặc định được cấu hình trong file `.env`.\n"
            ),
            inline=False,
        )
        return embed

    @staticmethod
    def _image_help() -> discord.Embed:
        """Tạo embed cho danh mục lệnh tìm kiếm ảnh và video.

        Returns:
            Embed chứa thông tin lệnh tìm kiếm ảnh và video.
        """
        embed = discord.Embed(
            title="🖼️ Lệnh tìm kiếm ảnh và video",
            description="Các lệnh để tìm kiếm ảnh và video từ các nguồn khác nhau.",
            color=0x00FF88,
        )
        embed.add_field(
            name="Lệnh",
            value=(
                "`/image <từ khóa>` hoặc `/img` - Tìm ảnh từ DuckDuckGo\n"
                "`!meme <từ khóa>` - Tìm ảnh meme từ DuckDuckGo\n"
            ),
            inline=False,
        )
        embed.add_field(
            name="💡 Ghi chú",
            value=(
                "• Bot sẽ tự động gửi ảnh ngẫu nghiên với nguồn từ `DuckDuckGo`.\n"
            ),
            inline=False,
        )
        return embed

    @staticmethod
    def _ai_help() -> discord.Embed:
        """Tạo embed cho danh mục lệnh AI.

        Returns:
            Embed chứa thông tin lệnh AI.
        """
        embed = discord.Embed(
            title="🤖 Lệnh AI",
            description="Các lệnh để tương tác với AI (Google Gemini).",
            color=0x00FF88,
        )
        embed.add_field(
            name="Lệnh",
            value=(
                "`/ai <tin nhắn>` - Chat với AI\n"
                "`/aistatus` - Kiểm tra trạng thái AI\n"
                "`/aihelp` - Hướng dẫn chi tiết về AI\n"
                "`/aiconfig [setting] [value]` - Cấu hình AI (chỉ admin)"
            ),
            inline=False,
        )
        embed.add_field(
            name="💡 Ghi chú",
            value="Gõ `!aihelp` để biết thêm chi tiết về tính năng AI.",
            inline=False,
        )
        return embed

    @staticmethod
    def _moderation_help() -> discord.Embed:
        """Tạo embed cho danh mục lệnh kiểm duyệt.

        Returns:
            Embed chứa thông tin lệnh kiểm duyệt.
        """
        embed = discord.Embed(
            title="🚨 Lệnh kiểm duyệt",
            description="Các lệnh để quản lý nội dung và từ cấm trên server.",
            color=0x00FF88,
        )
        embed.add_field(
            name="Lệnh",
            value=(
                "`/addbadword <từ>` - Thêm từ cấm (chỉ admin)\n"
                "`/removebadword <từ>` - Xóa từ cấm (chỉ admin)\n"
                "`/listbadwords` - Xem danh sách từ cấm (chỉ admin)\n"
                "`/modhelp` - Hiển thị hướng dẫn kiểm duyệt"
            ),
            inline=False,
        )
        embed.add_field(
            name="💡 Ghi chú",
            value="Bot tự động kiểm tra và cảnh báo khi phát hiện từ cấm trong tin nhắn.",
            inline=False,
        )
        return embed

    @staticmethod
    def _admin_help() -> discord.Embed:
        """Tạo embed cho danh mục lệnh admin.

        Returns:
            Embed chứa thông tin lệnh admin.
        """
        embed = discord.Embed(
            title="⚙️ Lệnh admin",
            description="Các lệnh dành cho quản trị viên server.",
            color=0x00FF88,
        )
        embed.add_field(
            name="Lệnh",
            value=(
                "`/setwelcome [#channel]` - Thiết lập channel chào mừng\n"
                "`/testwelcome [@user]` - Kiểm tra tin nhắn chào mừng\n"
                "`/aiconfig [setting] [value]` - Cấu hình AI\n"
                "`/addbadword <từ>` - Thêm từ cấm\n"
                "`/removebadword <từ>` - Xóa từ cấm\n"
                "`/listbadwords` - Xem danh sách từ cấm"
            ),
            inline=False,
        )
        embed.add_field(
            name="💡 Ghi chú",
            value="Tất cả lệnh admin yêu cầu quyền **Administrator**.",
            inline=False,
        )
        return embed

    class HelpView(discord.ui.View):
        """View chứa các nút tương tác cho danh mục trợ giúp."""

        def __init__(self, cog: "Help") -> None:
            """Khởi tạo HelpView.

            Args:
                cog: Đối tượng cog Help.
            """
            super().__init__(timeout=60)
            self.cog = cog

        async def on_timeout(self) -> None:
            """Xử lý khi view hết thời gian."""
            for item in self.children:
                item.disabled = True
            await self.message.edit(view=self)

        @discord.ui.button(label="Cơ bản", style=discord.ButtonStyle.secondary, emoji="📋")
        async def basic_button(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
            """Xử lý nút danh mục cơ bản."""
            embed = self.cog._basic_help()
            self._set_embed_footer_and_thumbnail(embed)
            await interaction.response.edit_message(embed=embed, view=self)

        @discord.ui.button(label="Nhạc", style=discord.ButtonStyle.secondary, emoji="🎵")
        async def music_button(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
            """Xử lý nút danh mục nhạc."""
            embed = self.cog._music_help()
            self._set_embed_footer_and_thumbnail(embed)
            await interaction.response.edit_message(embed=embed, view=self)

        @discord.ui.button(label="Nói", style=discord.ButtonStyle.secondary, emoji="📢")
        async def talk_button(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
            """Xử lý nút danh mục nói (text-to-speech)."""
            embed = self.cog._speak_help()
            self._set_embed_footer_and_thumbnail(embed)
            await interaction.response.edit_message(embed=embed, view=self)

        @discord.ui.button(label="Ảnh", style=discord.ButtonStyle.secondary, emoji="🖼️")
        async def image_button(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
            """Xử lý nút danh mục ảnh."""
            embed = self.cog._image_help()
            self._set_embed_footer_and_thumbnail(embed)
            await interaction.response.edit_message(embed=embed, view=self)

        @discord.ui.button(label="AI", style=discord.ButtonStyle.secondary, emoji="🤖")
        async def ai_button(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
            """Xử lý nút danh mục AI."""
            embed = self.cog._ai_help()
            self._set_embed_footer_and_thumbnail(embed)
            await interaction.response.edit_message(embed=embed, view=self)

        @discord.ui.button(label="Kiểm duyệt", style=discord.ButtonStyle.secondary, emoji="🚨")
        async def moderation_button(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
            """Xử lý nút danh mục kiểm duyệt."""
            embed = self.cog._moderation_help()
            self._set_embed_footer_and_thumbnail(embed)
            await interaction.response.edit_message(embed=embed, view=self)

        @discord.ui.button(label="Admin", style=discord.ButtonStyle.secondary, emoji="⚙️")
        async def admin_button(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
            """Xử lý nút danh mục admin."""
            embed = self.cog._admin_help()
            self._set_embed_footer_and_thumbnail(embed)
            await interaction.response.edit_message(embed=embed, view=self)

        def _set_embed_footer_and_thumbnail(self, embed: discord.Embed) -> None:
            """Thiết lập footer và thumbnail cho embed.

            Args:
                embed: Embed cần thiết lập.
            """
            embed.set_footer(text="DSB Bot - Phát triển bởi VanDung-dev")
            embed.set_thumbnail(
                url=self.cog.bot.user.avatar.url
                if self.cog.bot.user.avatar
                else self.cog.bot.user.default_avatar.url
            )

    @commands.command(name="help", aliases=["commands"])
    async def help_command(self, ctx: commands.Context, category: Optional[str] = None) -> None:
        """Hiển thị danh sách lệnh hỗ trợ.

        Args:
            ctx: Ngữ cảnh lệnh Discord.
            category: Danh mục trợ giúp (basic, music, speak, image, ai, moderation, admin).
        """
        logger.info(f"{ctx.author} gọi lệnh !help với danh mục: {category or 'all'} trong kênh {ctx.channel}")
        await self._send_help_embed(ctx, category)

    @app_commands.command(name="help", description="Hiển thị danh sách lệnh hỗ trợ")
    @app_commands.choices(category=[
        app_commands.Choice(name="Cơ bản", value="basic"),
        app_commands.Choice(name="Nhạc", value="music"),
        app_commands.Choice(name="Nói", value="speak"),
        app_commands.Choice(name="Ảnh", value="image"),
        app_commands.Choice(name="AI", value="ai"),
        app_commands.Choice(name="Kiểm duyệt", value="moderation"),
        app_commands.Choice(name="Admin", value="admin")
    ])
    async def slash_help(self, interaction: discord.Interaction, category: Optional[app_commands.Choice[str]] = None) -> None:
        """Phiên bản lệnh chém của trợ giúp."""
        category_value = category.value if category else None
        logger.info(f"{interaction.user} gọi lệnh /help với danh mục: {category_value or 'all'} trong kênh {interaction.channel}")
        await self._send_help_embed(interaction, category_value, is_slash=True)

    async def _send_help_embed(self, target, category: Optional[str] = None, is_slash: bool = False) -> None:
        """Gửi embed trợ giúp đến người dùng.

        Args:
            target: Có thể là Context hoặc Interaction.
            category: Danh mục trợ giúp.
            is_slash: Xác định nếu đây là lệnh slash.
        """
        help_methods = {
            "basic": self._basic_help,
            "music": self._music_help,
            "speak": self._speak_help,
            "image": self._image_help,
            "ai": self._ai_help,
            "moderation": self._moderation_help,
            "admin": self._admin_help,
        }

        if category:
            category = category.lower()
            if category in help_methods:
                embed = help_methods[category]()
            else:
                embed = discord.Embed(
                    title="❌ Danh mục không hợp lệ",
                    description=(
                        f"Danh mục `{category}` không tồn tại. "
                        "Gõ `/help` để xem danh sách danh mục hoặc thử: Cơ bản, Nhạc, Nói, Ảnh, AI, Kiểm duyệt, Admin"
                    ),
                    color=0xFF0000,
                )
        else:
            embed = self._basic_help()
            # Chỉ hiển thị các nút tương tác cho các lệnh văn bản
            if not is_slash:
                view = self.HelpView(self)
                if isinstance(target, commands.Context):
                    message = await target.send(embed=embed, view=view)
                    view.message = message
                    return
                elif isinstance(target, discord.Interaction):
                    await target.response.send_message(embed=embed, view=view)
                    view.message = await target.original_response()
                    return

        embed.set_footer(text="DSB Bot - Phát triển bởi VanDung-dev")
        embed.set_thumbnail(
            url=self.bot.user.avatar.url if self.bot.user.avatar else self.bot.user.default_avatar.url
        )
        
        # Gửi một cách thích hợp dựa trên loại mục tiêu
        if isinstance(target, commands.Context):
            await target.send(embed=embed)
        elif isinstance(target, discord.Interaction):
            if is_slash and not target.response.is_done():
                await target.response.send_message(embed=embed)
            else:
                await target.followup.send(embed=embed)