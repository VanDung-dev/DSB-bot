import logging
from typing import Optional
import os

import discord
from discord.ext import commands
from discord import app_commands
import gtts
import io
import asyncio
from dotenv import load_dotenv

# Cấu hình logger
logger = logging.getLogger(__name__)

# Tải biến môi trường
load_dotenv()


class Speaking(commands.Cog):
    """Cog xử lý chức năng text-to-speech cho bot."""

    def __init__(self, bot: commands.Bot) -> None:
        """Khởi tạo cog Speaking.

        Args:
            bot: Đối tượng bot Discord.
        """
        self.bot = bot
        # Lấy ngôn ngữ mặc định từ biến môi trường, mặc định là tiếng Việt nếu không có
        self.default_language = os.getenv("TTS_DEFAULT_LANGUAGE", "vi")

    async def generate_tts_audio(self, text: str, lang: str = None) -> Optional[discord.File]:
        """Tạo audio file từ văn bản sử dụng gTTS.

        Args:
            text: Văn bản cần chuyển thành giọng nói.
            lang: Mã ngôn ngữ (mặc định lấy từ cấu hình).

        Returns:
            File âm thanh dưới dạng discord.File hoặc None nếu có lỗi.
        """
        # Nếu không có ngôn ngữ được chỉ định, sử dụng ngôn ngữ mặc định
        if lang is None:
            lang = self.default_language
            
        try:
            # Sử dụng asyncio để chạy gTTS trong executor tránh blocking
            loop = asyncio.get_event_loop()
            # Cấu hình gTTS với các tùy chọn để tránh lỗi kết nối
            tts = gtts.gTTS(text, lang=lang, lang_check=False)
            await loop.run_in_executor(None, tts.save, "temp_tts.mp3")
            
            # Mở file âm thanh và trả về
            with open("temp_tts.mp3", "rb") as f:
                audio_buffer = io.BytesIO(f.read())
                audio_buffer.seek(0)
            
            # Xóa file tạm thời
            import os
            os.remove("temp_tts.mp3")
            
            # Trả về file âm thanh
            return discord.File(audio_buffer, filename="speech.mp3")
        except Exception as e:
            logger.error(f"❌ Lỗi khi tạo audio từ văn bản: {e}")
            return None

    @app_commands.command(name="say", description="Chuyển văn bản thành giọng nói")
    @app_commands.describe(
        text="Văn bản bạn muốn bot nói",
        language="Ngôn ngữ (mặc định được cấu hình trong .env)"
    )
    async def say(self, interaction: discord.Interaction, text: str, language: str = None) -> None:
        """Chuyển văn bản thành giọng nói và gửi vào kênh thoại.

        Args:
            interaction: Interaction từ người dùng.
            text: Văn bản cần chuyển thành giọng nói.
            language: Mã ngôn ngữ (mặc định lấy từ cấu hình).
        """
        await interaction.response.defer(thinking=True)
        
        # Nếu không có ngôn ngữ được chỉ định, sử dụng ngôn ngữ mặc định
        if language is None:
            language = self.default_language
        
        # Kiểm tra xem người dùng có ở trong voice channel không
        if not interaction.user.voice:
            await interaction.followup.send("❌ Bạn cần ở trong voice channel để sử dụng lệnh này.")
            return
        
        voice_channel = interaction.user.voice.channel
        guild_id = interaction.guild.id
        
        # Kết nối vào voice channel nếu chưa kết nối
        voice_client = discord.utils.get(self.bot.voice_clients, guild=interaction.guild)
        if not voice_client:
            try:
                voice_client = await voice_channel.connect()
            except discord.errors.ClientException:
                await interaction.followup.send("❌ Bot đã ở trong voice channel khác.")
                return
            except Exception as e:
                logger.error(f"❌ Lỗi khi kết nối voice channel: {e}")
                await interaction.followup.send("❌ Lỗi khi kết nối voice channel.")
                return
        
        # Tạo audio từ văn bản
        audio_file = await self.generate_tts_audio(text, language)
        if not audio_file:
            await interaction.followup.send("❌ Không thể tạo âm thanh từ văn bản. Có thể do lỗi kết nối mạng hoặc ngôn ngữ không được hỗ trợ.")
            return
        
        # Gửi thông báo đang xử lý
        await interaction.followup.send(f"🔊 Đang nói: {text}")
        
        # Phát âm thanh trong voice channel
        try:
            # Lưu tên file để phát
            filename = f"temp_{interaction.id}.mp3"
            
            # Lưu audio vào file tạm thời
            audio_fp = audio_file.fp
            audio_fp.seek(0)
            
            with open(filename, "wb") as f:
                f.write(audio_fp.read())
            
            # Phát audio
            source = discord.FFmpegPCMAudio(filename)
            voice_client.play(source)
            
            # Chờ đến khi phát xong
            while voice_client.is_playing():
                await asyncio.sleep(1)
            
            # Xóa file tạm thời
            import os
            if os.path.exists(filename):
                os.remove(filename)
                
        except Exception as e:
            logger.error(f"❌ Lỗi khi phát âm thanh: {e}")
            await interaction.followup.send("❌ Có lỗi xảy ra khi phát âm thanh.")

    @commands.command(name="say", aliases=["speak"])
    async def say_legacy(self, ctx: commands.Context, *, text: str) -> None:
        """Phiên bản lệnh say dành cho prefix commands.

        Args:
            ctx: Ngữ cảnh lệnh.
            text: Văn bản cần chuyển thành giọng nói.
        """
        # Kiểm tra xem người dùng có ở trong voice channel không
        if not ctx.author.voice:
            await ctx.send("❌ Bạn cần ở trong voice channel để sử dụng lệnh này.")
            return
        
        voice_channel = ctx.author.voice.channel
        guild_id = ctx.guild.id
        
        # Kết nối vào voice channel nếu chưa kết nối
        voice_client = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        if not voice_client:
            try:
                voice_client = await voice_channel.connect()
            except discord.errors.ClientException:
                await ctx.send("❌ Bot đã ở trong voice channel khác.")
                return
            except Exception as e:
                logger.error(f"❌ Lỗi khi kết nối voice channel: {e}")
                await ctx.send("❌ Lỗi khi kết nối voice channel.")
                return
        
        # Tạo audio từ văn bản với ngôn ngữ mặc định
        audio_file = await self.generate_tts_audio(text, self.default_language)
        if not audio_file:
            await ctx.send("❌ Không thể tạo âm thanh từ văn bản. Có thể do lỗi kết nối mạng hoặc ngôn ngữ không được hỗ trợ.")
            return
        
        # Gửi thông báo đang xử lý
        await ctx.send(f"🔊 Đang nói: {text}")
        
        # Phát âm thanh trong voice channel
        try:
            # Lưu tên file để phát
            filename = f"temp_{ctx.message.id}.mp3"
            
            # Lưu audio vào file tạm thời
            audio_fp = audio_file.fp
            audio_fp.seek(0)
            
            with open(filename, "wb") as f:
                f.write(audio_fp.read())
            
            # Phát audio
            source = discord.FFmpegPCMAudio(filename)
            voice_client.play(source)
            
            # Chờ đến khi phát xong
            while voice_client.is_playing():
                await asyncio.sleep(1)
            
            # Xóa file tạm thời
            import os
            if os.path.exists(filename):
                os.remove(filename)
                
        except Exception as e:
            logger.error(f"❌ Lỗi khi phát âm thanh: {e}")
            await ctx.send("❌ Có lỗi xảy ra khi phát âm thanh.")


async def setup(bot: commands.Bot) -> None:
    """Thiết lập cog Speaking."""
    await bot.add_cog(Speaking(bot))