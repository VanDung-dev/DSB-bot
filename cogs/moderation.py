import json
import logging
import re
from pathlib import Path
from typing import List

import discord
from discord.ext import commands
from discord import app_commands

# Cấu hình logger
logger = logging.getLogger(__name__)


class Moderation(commands.Cog):
    """Cog xử lý kiểm duyệt tin nhắn và quản lý từ cấm."""

    def __init__(self, bot: commands.Bot) -> None:
        """Khởi tạo cog Moderation.

        Args:
            bot: Đối tượng bot Discord.
        """
        self.bot = bot
        self.bad_words_file = Path("bad_words.json")
        self.bad_words = self.load_bad_words()

    def load_bad_words(self) -> List[str]:
        """Tải danh sách từ cấm từ file JSON.

        Returns:
            Danh sách các từ cấm. Nếu file không tồn tại hoặc lỗi, trả về danh sách mặc định.
        """
        default_bad_words = ["curse", "swear", "offensive", "inappropriate", "rude"]
        try:
            if self.bad_words_file.exists():
                with self.bad_words_file.open("r", encoding="utf-8") as f:
                    content = f.read().strip()
                    if not content:
                        logger.warning("⚠️ Tệp bad_words.json rỗng, sử dụng danh sách mặc định")
                        self.save_bad_words(default_bad_words)
                        return default_bad_words
                    return json.loads(content)
            logger.info("📝 Tệp bad_words.json không tồn tại, tạo mới với danh sách mặc định")
            self.save_bad_words(default_bad_words)
            return default_bad_words
        except json.JSONDecodeError as e:
            logger.error(f"❌ Lỗi định dạng JSON trong bad_words.json: {e}. Sử dụng danh sách mặc định")
            self.save_bad_words(default_bad_words)
            return default_bad_words
        except Exception as e:
            logger.error(f"❌ Lỗi khi đọc bad_words.json: {e}. Sử dụng danh sách mặc định")
            self.save_bad_words(default_bad_words)
            return default_bad_words

    def save_bad_words(self, bad_words: List[str] = None) -> None:
        """Lưu danh sách từ cấm vào file JSON.

        Args:
            bad_words: Danh sách từ cấm cần lưu. Nếu None, sử dụng self.bad_words.
        """
        try:
            with self.bad_words_file.open("w", encoding="utf-8") as f:
                json.dump(bad_words or self.bad_words, f, indent=4, ensure_ascii=False)
            logger.info("✅ Đã lưu danh sách từ cấm vào bad_words.json")
        except Exception as e:
            logger.error(f"❌ Lỗi khi lưu bad_words.json: {e}")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        """Kiểm tra tin nhắn chứa từ cấm và gửi cảnh báo.

        Args:
            message: Tin nhắn Discord cần kiểm tra.
        """
        if message.author.bot or not message.guild:
            return

        content = message.content.lower()
        if content.startswith(("/addbadword", "/removebadword")):
            logger.info(f"📝 Bỏ qua kiểm tra từ cấm cho lệnh: {content} từ {message.author}")
            try:
                await message.delete()
                logger.info(f"🗑 Đã xóa tin nhắn lệnh từ {message.author}")
            except discord.Forbidden:
                logger.warning(f"⚠️ Không có quyền xóa tin nhắn lệnh trong {message.channel}")
            except Exception as e:
                logger.error(f"❌ Lỗi khi xóa tin nhắn lệnh: {e}")
            return

        if not content.startswith(self.bot.command_prefix):
            for word in self.bad_words:
                if re.search(rf"\b{re.escape(word)}\b", content, re.IGNORECASE):
                    logger.warning(
                        f"⚠️ Phát hiện từ cấm '{word}' từ {message.author} trong kênh {message.channel}"
                    )
                    embed = discord.Embed(
                        title="🚨 Cảnh báo từ DSB Bot",
                        description=(
                            f"{message.author.mention}, tin nhắn của bạn chứa từ ngữ không phù hợp: **{word}**. "
                            "Vui lòng tuân thủ quy tắc server/"
                        ),
                        color=discord.Color.red(),
                    )
                    embed.set_footer(text="Liên hệ admin nếu có thắc mắc.")

                    try:
                        await message.channel.send(embed=embed)
                        await message.author.send(embed=embed)
                        await message.delete()
                    except discord.Forbidden:
                        logger.warning(
                            f"⚠️ Không có quyền gửi tin nhắn hoặc xóa tin nhắn trong {message.channel}"
                        )
                        await message.channel.send(
                            f"{message.author.mention}, tin nhắn của bạn chứa từ cấm nhưng bot không có quyền xóa. "
                            "Vui lòng tự chỉnh sửa/"
                        )
                    except Exception as e:
                        logger.error(f"❌ Lỗi khi xử lý vi phạm: {e}")
                    return

    @commands.command(name="addbadword")
    @commands.has_permissions(administrator=True)
    async def add_bad_word(self, ctx: commands.Context, *, word: str) -> None:
        """Thêm từ cấm vào danh sách (chỉ admin).

        Args:
            ctx: Ngữ cảnh lệnh Discord.
            word: Từ cần thêm vào danh sách từ cấm.
        """
        logger.info(f"{ctx.author} gọi lệnh /addbadword với từ: {word}")
        word = word.lower().strip()
        if not word:
            await ctx.send("❌ Vui lòng cung cấp từ cấm hợp lệ.")
            return
        if word in self.bad_words:
            await ctx.send(f"❌ Từ '{word}' đã có trong danh sách từ cấm.")
            return

        self.bad_words.append(word)
        self.save_bad_words()
        embed = discord.Embed(
            title="✅ Thành công",
            description=f"Đã thêm từ cấm: **{word}**.",
            color=discord.Color.green(),
        )
        await ctx.send(embed=embed)
        logger.info(f"✅ Đã thêm từ cấm: {word}")
        
    @app_commands.command(name="addbadword", description="Thêm từ cấm vào danh sách (chỉ admin)")
    @app_commands.describe(word="Từ cần thêm vào danh sách từ cấm")
    @app_commands.default_permissions(administrator=True)
    async def slash_add_bad_word(self, interaction: discord.Interaction, word: str) -> None:
        """Slash command thêm từ cấm vào danh sách (chỉ admin).

        Args:
            interaction: Tương tác từ người dùng.
            word: Từ cần thêm vào danh sách từ cấm.
        """
        logger.info(f"{interaction.user} gọi slash command /addbadword với từ: {word}")
        word = word.lower().strip()
        if not word:
            await interaction.response.send_message("❌ Vui lòng cung cấp từ cấm hợp lệ.", ephemeral=True)
            return
        if word in self.bad_words:
            await interaction.response.send_message(f"❌ Từ '{word}' đã có trong danh sách từ cấm.", ephemeral=True)
            return

        self.bad_words.append(word)
        self.save_bad_words()
        embed = discord.Embed(
            title="✅ Thành công",
            description=f"Đã thêm từ cấm: **{word}**.",
            color=discord.Color.green(),
        )
        await interaction.response.send_message(embed=embed)
        logger.info(f"✅ Đã thêm từ cấm: {word}")

    @commands.command(name="removebadword")
    @commands.has_permissions(administrator=True)
    async def remove_bad_word(self, ctx: commands.Context, *, word: str) -> None:
        """Xóa từ cấm khỏi danh sách (chỉ admin).

        Args:
            ctx: Ngữ cảnh lệnh Discord.
            word: Từ cần xóa khỏi danh sách từ cấm.
        """
        logger.info(f"{ctx.author} gọi lệnh /removebadword với từ: {word}")
        word = word.lower().strip()
        if not word:
            await ctx.send("❌ Vui lòng cung cấp từ cấm hợp lệ.")
            return
        if word not in self.bad_words:
            await ctx.send(f"❌ Từ '{word}' không có trong danh sách từ cấm.")
            return

        self.bad_words.remove(word)
        self.save_bad_words()
        embed = discord.Embed(
            title="✅ Thành công",
            description=f"Đã xóa từ cấm: **{word}**.",
            color=discord.Color.green(),
        )
        await ctx.send(embed=embed)
        logger.info(f"✅ Đã xóa từ cấm: {word}")
        
    @app_commands.command(name="removebadword", description="Xóa từ cấm khỏi danh sách (chỉ admin)")
    @app_commands.describe(word="Từ cần xóa khỏi danh sách từ cấm")
    @app_commands.default_permissions(administrator=True)
    async def slash_remove_bad_word(self, interaction: discord.Interaction, word: str) -> None:
        """Slash command xóa từ cấm khỏi danh sách (chỉ admin).

        Args:
            interaction: Tương tác từ người dùng.
            word: Từ cần xóa khỏi danh sách từ cấm.
        """
        logger.info(f"{interaction.user} gọi slash command /removebadword với từ: {word}")
        word = word.lower().strip()
        if not word:
            await interaction.response.send_message("❌ Vui lòng cung cấp từ cấm hợp lệ.", ephemeral=True)
            return
        if word not in self.bad_words:
            await interaction.response.send_message(f"❌ Từ '{word}' không có trong danh sách từ cấm.", ephemeral=True)
            return

        self.bad_words.remove(word)
        self.save_bad_words()
        embed = discord.Embed(
            title="✅ Thành công",
            description=f"Đã xóa từ cấm: **{word}**.",
            color=discord.Color.green(),
        )
        await interaction.response.send_message(embed=embed)
        logger.info(f"✅ Đã xóa từ cấm: {word}")

    @commands.command(name="listbadwords")
    @commands.has_permissions(administrator=True)
    async def list_bad_words(self, ctx: commands.Context) -> None:
        """Hiển thị danh sách từ cấm (chỉ admin).

        Args:
            ctx: Ngữ cảnh lệnh Discord.
        """
        logger.info(f"{ctx.author} gọi lệnh /listbadwords")
        if not self.bad_words:
            embed = discord.Embed(
                title="📜 Danh sách từ cấm",
                description="Danh sách từ cấm hiện đang trống.",
                color=discord.Color.blue(),
            )
            await ctx.send(embed=embed)
            return

        words_str = "\n".join(self.bad_words)
        if len(words_str) > 1000:
            words_chunks = [self.bad_words[i : i + 50] for i in range(0, len(self.bad_words), 50)]
            for i, chunk in enumerate(words_chunks):
                embed = discord.Embed(
                    title="📜 Danh sách từ cấm" if i == 0 else f"📜 Danh sách từ cấm (phần {i+1})",
                    description="\n".join(chunk),
                    color=discord.Color.blue(),
                )
                await ctx.send(embed=embed)
        else:
            embed = discord.Embed(
                title="📜 Danh sách từ cấm",
                description=words_str,
                color=discord.Color.blue(),
            )
            await ctx.send(embed=embed)
            
    @app_commands.command(name="listbadwords", description="Hiển thị danh sách từ cấm (chỉ admin)")
    @app_commands.default_permissions(administrator=True)
    async def slash_list_bad_words(self, interaction: discord.Interaction) -> None:
        """Slash command hiển thị danh sách từ cấm (chỉ admin).

        Args:
            interaction: Tương tác từ người dùng.
        """
        logger.info(f"{interaction.user} gọi slash command /listbadwords")
        if not self.bad_words:
            embed = discord.Embed(
                title="📜 Danh sách từ cấm",
                description="Danh sách từ cấm hiện đang trống.",
                color=discord.Color.blue(),
            )
            await interaction.response.send_message(embed=embed)
            return

        words_str = "\n".join(self.bad_words)
        if len(words_str) > 1000:
            words_chunks = [self.bad_words[i : i + 50] for i in range(0, len(self.bad_words), 50)]
            # For the first chunk, we send as the response
            embed = discord.Embed(
                title="📜 Danh sách từ cấm",
                description="\n".join(words_chunks[0]),
                color=discord.Color.blue(),
            )
            await interaction.response.send_message(embed=embed)
            
            # For subsequent chunks, we send as followups
            for i, chunk in enumerate(words_chunks[1:], start=2):
                embed = discord.Embed(
                    title=f"📜 Danh sách từ cấm (phần {i})",
                    description="\n".join(chunk),
                    color=discord.Color.blue(),
                )
                await interaction.followup.send(embed=embed)
        else:
            embed = discord.Embed(
                title="📜 Danh sách từ cấm",
                description=words_str,
                color=discord.Color.blue(),
            )
            await interaction.response.send_message(embed=embed)

    @commands.command(name="modhelp")
    async def moderation_help(self, ctx: commands.Context) -> None:
        """Hiển thị hướng dẫn sử dụng các lệnh kiểm duyệt.

        Args:
            ctx: Ngữ cảnh lệnh Discord.
        """
        logger.info(f"{ctx.author} gọi lệnh /modhelp")
        embed = discord.Embed(
            title="🚨 Hướng dẫn kiểm duyệt",
            description="Các lệnh để quản lý nội dung vi phạm trên server.",
            color=discord.Color.orange(),
        )
        embed.add_field(
            name="📋 Lệnh kiểm duyệt",
            value=(
                "`/addbadword <từ>` - Thêm từ cấm (chỉ admin)\n"
                "`/removebadword <từ>` - Xóa từ cấm (chỉ admin)\n"
                "`/listbadwords` - Xem danh sách từ cấm (chỉ admin)\n"
                "`/modhelp` - Hiển thị hướng dẫn này"
            ),
            inline=False,
        )
        embed.add_field(
            name="💡 Ghi chú",
            value="Bot tự động kiểm tra tin nhắn và gửi cảnh báo khi phát hiện từ cấm, "
            "ngoại trừ các lệnh /addbadword và /removebadword.",
            inline=False,
        )
        await ctx.send(embed=embed)
        
    @app_commands.command(name="modhelp", description="Hiển thị hướng dẫn sử dụng các lệnh kiểm duyệt")
    async def slash_moderation_help(self, interaction: discord.Interaction) -> None:
        """Slash command hiển thị hướng dẫn sử dụng các lệnh kiểm duyệt.

        Args:
            interaction: Tương tác từ người dùng.
        """
        logger.info(f"{interaction.user} gọi slash command /modhelp")
        embed = discord.Embed(
            title="🚨 Hướng dẫn kiểm duyệt",
            description="Các lệnh để quản lý nội dung vi phạm trên server.",
            color=discord.Color.orange(),
        )
        embed.add_field(
            name="📋 Lệnh kiểm duyệt",
            value=(
                "`/addbadword <từ>` - Thêm từ cấm (chỉ admin)\n"
                "`/removebadword <từ>` - Xóa từ cấm (chỉ admin)\n"
                "`/listbadwords` - Xem danh sách từ cấm (chỉ admin)\n"
                "`/modhelp` - Hiển thị hướng dẫn này"
            ),
            inline=False,
        )
        embed.add_field(
            name="💡 Ghi chú",
            value="Bot tự động kiểm tra tin nhắn và gửi cảnh báo khi phát hiện từ cấm, "
            "ngoại trừ các lệnh /addbadword và /removebadword.",
            inline=False,
        )
        await interaction.response.send_message(embed=embed)

    @add_bad_word.error
    @remove_bad_word.error
    @list_bad_words.error
    async def moderation_command_error(self, ctx: commands.Context, error: Exception) -> None:
        """Xử lý lỗi cho các lệnh kiểm duyệt.

        Args:
            ctx: Ngữ cảnh lệnh Discord.
            error: Lỗi được ném ra.
        """
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ Bạn cần quyền Administrator để sử dụng lệnh này.")
            logger.warning(f"⚠️ {ctx.author} cố gắng dùng lệnh admin mà không có quyền")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("❌ Vui lòng cung cấp từ cấm hợp lệ.")
            
    @slash_add_bad_word.error
    @slash_remove_bad_word.error
    async def slash_moderation_command_error(self, interaction: discord.Interaction, error: Exception) -> None:
        """Xử lý lỗi cho các slash command kiểm duyệt.

        Args:
            interaction: Tương tác từ người dùng.
            error: Lỗi được ném ra.
        """
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message("❌ Bạn cần quyền Administrator để sử dụng lệnh này.", ephemeral=True)
            logger.warning(f"⚠️ {interaction.user} cố gắng dùng lệnh admin mà không có quyền")