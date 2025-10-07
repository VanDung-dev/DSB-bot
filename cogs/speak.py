import logging
from typing import Optional

import discord
from discord.ext import commands
from discord import app_commands
import gtts
import io
import asyncio

# Cấu hình logger
logger = logging.getLogger(__name__)


class Speaking(commands.Cog):
    """Cog xử lý chức năng text-to-speech cho bot."""

    def __init__(self, bot: commands.Bot) -> None:
        """Khởi tạo cog Speaking.

        Args:
            bot: Đối tượng bot Discord.
        """
        self.bot = bot
        self.speaking_states: dict = {}

    # Danh sách ngôn ngữ phổ biến cho autocomplete
    common_languages = {
        'en': 'English',
        'vi': 'Vietnamese',
        'fr': 'French',
        'es': 'Spanish',
        'de': 'German',
        'ja': 'Japanese',
        'ko': 'Korean',
        'zh-CN': 'Chinese (Simplified)',
        'ru': 'Russian',
    }

    def get_voice_client(self, guild: discord.Guild) -> Optional[discord.VoiceClient]:
        """Nhận ứng dụng khách giọng nói từ music cog nếu có."""
        # Cố gắng lấy máy khách bằng giọng nói từ âm nhạc đầu tiên
        music_cog = self.bot.get_cog('MusicSearch')
        if music_cog and guild.id in music_cog.voice_clients:
            return music_cog.voice_clients[guild.id]
        
        # Dự phòng của khách hàng giọng nói của bot
        return discord.utils.get(self.bot.voice_clients, guild=guild)

    async def connect_to_voice(self, guild: discord.Guild, channel: discord.VoiceChannel) -> Optional[discord.VoiceClient]:
        """Kết nối với kênh thoại, sử dụng music cog nếu có."""
        # Kiểm tra xem music cog có quản lý kết nối giọng nói không
        music_cog = self.bot.get_cog('MusicSearch')
        if music_cog and guild.id in music_cog.voice_clients:
            return music_cog.voice_clients[guild.id]
        
        # Nếu không thì kết nối bằng phương pháp riêng của chúng tôi
        voice_client = discord.utils.get(self.bot.voice_clients, guild=guild)
        if not voice_client:
            try:
                voice_client = await channel.connect()
                # Nếu music cog tồn tại, hãy đăng ký kết nối này với nó
                if music_cog:
                    music_cog.voice_clients[guild.id] = voice_client
            except discord.errors.ClientException:
                return None
            except Exception as e:
                logger.error(f"❌ Lỗi khi kết nối voice channel: {e}")
                return None
        return voice_client

    @staticmethod
    async def generate_tts_audio(text: str, lang: str = None) -> Optional[discord.File]:
        """Tạo audio file từ văn bản sử dụng gTTS.

        Args:
            text: Văn bản cần chuyển thành giọng nói.
            lang: Mã ngôn ngữ (mặc định lấy từ cấu hình).

        Returns:
            File âm thanh dưới dạng discord.File hoặc None nếu có lỗi.
        """
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
        language="Chọn ngôn ngữ trước",
        text="Văn bản bạn muốn bot nói"
    )
    @app_commands.choices(language=[
        app_commands.Choice(name=name, value=code) 
        for code, name in list(common_languages.items())[:25]
    ])  # Giới hạn 25 choices do Discord API giới hạn
    @app_commands.rename(language="language", text="text")
    async def say(self, interaction: discord.Interaction, language: str, text: str) -> None:
        """Chuyển văn bản thành giọng nói và gửi vào kênh thoại.

        Args:
            interaction: Interaction từ người dùng.
            language: Mã ngôn ngữ được chọn.
            text: Văn bản cần chuyển thành giọng nói.
        """
        # Kiểm tra xem người dùng có ở trong voice channel không
        if not interaction.user.voice:
            await interaction.response.send_message("❌ Bạn cần ở trong voice channel để sử dụng lệnh này.", ephemeral=True)
            return
        
        voice_channel = interaction.user.voice.channel
        guild_id = interaction.guild.id
        
        # Kiểm tra xem bot có đang phát nhạc không
        music_cog = self.bot.get_cog('MusicSearch')
        if music_cog:
            # Nếu có hàng đợi nhạc, từ chối thực hiện nói
            if guild_id in music_cog.queues and music_cog.queues[guild_id]:
                await interaction.response.send_message("❌ Không thể nói khi đang phát nhạc có hàng đợi. Hãy dùng /stop hoặc /clear trước.", ephemeral=True)
                return
        
        # Đánh dấu trạng thái nói cho guild này
        self.speaking_states[guild_id] = True
        
        # Trả lời ngay lập tức để tránh timeout
        await interaction.response.send_message(f"🔊 Đang xử lý yêu cầu nói...", ephemeral=False)
        
        # Kết nối vào voice channel nếu chưa kết nối
        voice_client = self.get_voice_client(interaction.guild)
        if not voice_client:
            try:
                voice_client = await self.connect_to_voice(interaction.guild, voice_channel)
                if not voice_client:
                    await interaction.edit_original_response(content="❌ Bot đã ở trong voice channel khác.")
                    del self.speaking_states[guild_id]
                    return
            except Exception as e:
                logger.error(f"❌ Lỗi khi kết nối voice channel: {e}")
                await interaction.edit_original_response(content="❌ Lỗi khi kết nối voice channel.")
                del self.speaking_states[guild_id]
                return
        
        # Tạo audio từ văn bản
        audio_file = await self.generate_tts_audio(text, language)
        if not audio_file:
            await interaction.edit_original_response(content="❌ Không thể tạo âm thanh từ văn bản. Có thể do lỗi kết nối mạng hoặc ngôn ngữ không được hỗ trợ.")
            del self.speaking_states[guild_id]
            return
        
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
            
            # Chờ bất kỳ âm thanh hiện đang phát hiện đang phát
            while voice_client.is_playing():
                await asyncio.sleep(0.5)
                
            voice_client.play(source)
            
            # Chờ đến khi phát xong
            while voice_client.is_playing():
                await asyncio.sleep(1)
            
            # Cập nhật tin nhắn để thông báo đã nói xong
            await interaction.edit_original_response(content=f"✅ Đã nói xong ({self.common_languages.get(language, language)}): {text}")
            
            # Xóa file tạm thời
            import os
            if os.path.exists(filename):
                os.remove(filename)
                
        except Exception as e:
            logger.error(f"❌ Lỗi khi phát âm thanh: {e}")
            await interaction.edit_original_response(content="❌ Có lỗi xảy ra khi phát âm thanh.")
        finally:
            # Xóa trạng thái nói
            if guild_id in self.speaking_states:
                del self.speaking_states[guild_id]

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
        
        # Kiểm tra xem bot có đang phát nhạc không
        music_cog = self.bot.get_cog('MusicSearch')
        if music_cog:
            # Nếu có hàng đợi nhạc, từ chối thực hiện nói
            if guild_id in music_cog.queues and music_cog.queues[guild_id]:
                await ctx.send("❌ Không thể nói khi đang phát nhạc có hàng đợi. Hãy dùng !stop hoặc !clear trước.")
                return
        
        # Đánh dấu trạng thái nói cho guild này
        self.speaking_states[guild_id] = True
        
        # Gửi thông báo đang xử lý
        processing_msg = await ctx.send(f"🔊 Đang xử lý yêu cầu nói...")
        
        # Kết nối vào voice channel nếu chưa kết nối
        voice_client = self.get_voice_client(ctx.guild)
        if not voice_client:
            try:
                voice_client = await self.connect_to_voice(ctx.guild, voice_channel)
                if not voice_client:
                    await processing_msg.edit(content="❌ Bot đã ở trong voice channel khác.")
                    del self.speaking_states[guild_id]
                    return
            except Exception as e:
                logger.error(f"❌ Lỗi khi kết nối voice channel: {e}")
                await processing_msg.edit(content="❌ Lỗi khi kết nối voice channel.")
                del self.speaking_states[guild_id]
                return
        
        # Tạo audio từ văn bản với ngôn ngữ mặc định
        audio_file = await self.generate_tts_audio(text)
        if not audio_file:
            await processing_msg.edit(content="❌ Không thể tạo âm thanh từ văn bản. Có thể do lỗi kết nối mạng hoặc ngôn ngữ không được hỗ trợ.")
            del self.speaking_states[guild_id]
            return
        
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
            
            # Chờ bất kỳ âm thanh hiện đang phát hiện đang phát
            while voice_client.is_playing():
                await asyncio.sleep(0.5)
                
            voice_client.play(source)
            
            # Chờ đến khi phát xong
            while voice_client.is_playing():
                await asyncio.sleep(1)
            
            # Cập nhật tin nhắn để thông báo đã nói xong
            await processing_msg.edit(content=f"✅ Đã nói xong: {text}")
            
            # Xóa file tạm thời
            import os
            if os.path.exists(filename):
                os.remove(filename)
                
        except Exception as e:
            logger.error(f"❌ Lỗi khi phát âm thanh: {e}")
            await processing_msg.edit(content="❌ Có lỗi xảy ra khi phát âm thanh.")
        finally:
            # Xóa trạng thái nói
            if guild_id in self.speaking_states:
                del self.speaking_states[guild_id]


async def setup(bot: commands.Bot) -> None:
    """Thiết lập cog Speaking."""
    await bot.add_cog(Speaking(bot))