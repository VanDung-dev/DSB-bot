import asyncio
import json
import logging
from collections import deque
from pathlib import Path
from typing import Dict, Optional

import discord
import yt_dlp
from discord.ext import commands

# Cấu hình logger
logger = logging.getLogger(__name__)


class MusicSearch(commands.Cog):
    """Cog xử lý các lệnh phát nhạc từ YouTube."""

    FFMPEG_OPTIONS = {
        "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
        "options": "-vn",
    }

    def __init__(self, bot: commands.Bot) -> None:
        """Khởi tạo cog MusicSearch.

        Args:
            bot: Đối tượng bot Discord.
        """
        self.bot = bot
        self.queues: Dict[int, deque] = {}
        self.now_playing: Dict[int, dict] = {}
        self.voice_clients: Dict[int, discord.VoiceClient] = {}
        self.ydl_options = self.load_ydl_config()

    @staticmethod
    def load_ydl_config() -> dict:
        """Tải cấu hình yt_dlp từ file JSON.

        Returns:
            Cấu hình yt_dlp.

        Raises:
            FileNotFoundError: Nếu file ydl_config.json không tồn tại.
            json.JSONDecodeError: Nếu file JSON không hợp lệ.
        """
        config_file = Path("ydl_config.json")
        try:
            if config_file.exists():
                with config_file.open("r", encoding="utf-8") as f:
                    return json.load(f)
            raise FileNotFoundError("ydl_config.json không tồn tại")
        except json.JSONDecodeError as e:
            logger.error(f"❌ Lỗi khi đọc ydl_config.json: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ Lỗi khi tải ydl_config.json: {e}")
            raise

    async def get_video_info(self, query: str) -> Optional[dict]:
        """Lấy thông tin video từ YouTube.

        Args:
            query: URL hoặc từ khóa tìm kiếm.

        Returns:
            Thông tin video (title, url, webpage_url, duration, uploader) hoặc None nếu lỗi.
        """
        try:
            with yt_dlp.YoutubeDL(self.ydl_options) as ydl:
                loop = asyncio.get_event_loop()
                info = await loop.run_in_executor(None, lambda: ydl.extract_info(query, download=False))
                if "entries" in info:
                    info = info["entries"][0]
                return {
                    "title": info.get("title", "Unknown Title"),
                    "url": info.get("url", ""),
                    "webpage_url": info.get("webpage_url", ""),
                    "duration": info.get("duration", 0),
                    "uploader": info.get("uploader", "Unknown Uploader"),
                }
        except Exception as e:
            logger.error(f"❌ Lỗi khi tải thông tin video: {e}")
            return None

    async def play_next(self, guild_id: int) -> None:
        """Phát bài tiếp theo trong hàng đợi.

        Args:
            guild_id: ID của server Discord.
        """
        if guild_id not in self.queues or not self.queues[guild_id]:
            self.now_playing.pop(guild_id, None)
            if guild_id in self.voice_clients:
                await self.voice_clients[guild_id].disconnect()
                self.voice_clients.pop(guild_id)
            return

        song = self.queues[guild_id].popleft()
        self.now_playing[guild_id] = song

        try:
            source = discord.FFmpegPCMAudio(song["url"], **self.FFMPEG_OPTIONS)
            self.voice_clients[guild_id].play(
                source,
                after=lambda e: asyncio.run_coroutine_threadsafe(self.play_next(guild_id), self.bot.loop),
            )
            embed = discord.Embed(
                title="🎵 Đang phát",
                description=(
                    f"[{song['title']}]({song['webpage_url']})\n"
                    f"**Người tải lên**: {song['uploader']}\n"
                    f"**Thời lượng**: {song['duration']//60}:{song['duration']%60:02d}"
                ),
                color=discord.Color.green(),
            )
            await self.voice_clients[guild_id].channel.send(embed=embed)
            logger.info(f"✅ Đang phát: {song['title']} trong guild {guild_id}")
        except Exception as e:
            logger.error(f"❌ Lỗi khi phát nhạc: {e}")
            await self.play_next(guild_id)

    @commands.command(name="play", aliases=["p"])
    async def play(self, ctx: commands.Context, *, query: str) -> None:
        """Phát nhạc từ URL hoặc tìm kiếm trên YouTube.

        Args:
            ctx: Ngữ cảnh lệnh Discord.
            query: URL hoặc từ khóa tìm kiếm.
        """
        if not ctx.author.voice:
            await ctx.send("❌ Bạn cần ở trong voice channel để sử dụng lệnh này.")
            return

        voice_channel = ctx.author.voice.channel
        guild_id = ctx.guild.id

        if guild_id not in self.voice_clients:
            try:
                self.voice_clients[guild_id] = await voice_channel.connect()
            except discord.errors.ClientException:
                await ctx.send("❌ Bot đã ở trong voice channel khác.")
                return
            except Exception as e:
                logger.error(f"❌ Lỗi khi kết nối voice channel: {e}")
                await ctx.send("❌ Lỗi khi kết nối voice channel.")
                return

        search_msg = await ctx.send(f"🔍 Đang tìm: **{query}**...")
        video_info = await self.get_video_info(query)
        if not video_info:
            await search_msg.edit(content="❌ Không tìm thấy video.")
            return

        if guild_id not in self.queues:
            self.queues[guild_id] = deque()
        self.queues[guild_id].append(video_info)

        embed = discord.Embed(
            title="✅ Đã thêm vào hàng đợi",
            description=(
                f"[{video_info['title']}]({video_info['webpage_url']})\n"
                f"**Người tải lên**: {video_info['uploader']}\n"
                f"**Thời lượng**: {video_info['duration']//60}:{video_info['duration']%60:02d}"
            ),
            color=discord.Color.blue(),
        )
        await search_msg.edit(content="", embed=embed)
        logger.info(f"✅ Đã thêm: {video_info['title']} vào hàng đợi guild {guild_id}")

        if guild_id not in self.now_playing:
            await self.play_next(guild_id)

    @commands.command(name="queue", aliases=["q"])
    async def queue(self, ctx: commands.Context) -> None:
        """Hiển thị danh sách hàng đợi.

        Args:
            ctx: Ngữ cảnh lệnh Discord.
        """
        guild_id = ctx.guild.id
        if guild_id not in self.queues or not self.queues[guild_id]:
            await ctx.send("📭 Hàng đợi hiện đang trống.")
            return

        embed = discord.Embed(
            title="📜 Danh sách hàng đợi",
            description="\n".join(
                f"{i+1}. [{song['title']}]({song['webpage_url']}) ({song['duration']//60}:{song['duration']%60:02d})"
                for i, song in enumerate(self.queues[guild_id])
            ),
            color=discord.Color.purple(),
        )
        if guild_id in self.now_playing:
            embed.add_field(
                name="Đang phát",
                value=f"[{self.now_playing[guild_id]['title']}]({self.now_playing[guild_id]['webpage_url']})",
                inline=False,
            )
        await ctx.send(embed=embed)

    @commands.command(name="nowplaying", aliases=["np"])
    async def now_playing(self, ctx: commands.Context) -> None:
        """Hiển thị bài đang phát.

        Args:
            ctx: Ngữ cảnh lệnh Discord.
        """
        guild_id = ctx.guild.id
        if guild_id not in self.now_playing:
            await ctx.send("📭 Hiện không có bài nào đang phát.")
            return

        song = self.now_playing[guild_id]
        embed = discord.Embed(
            title="🎵 Đang phát",
            description=(
                f"[{song['title']}]({song['webpage_url']})\n"
                f"**Người tải lên**: {song['uploader']}\n"
                f"**Thời lượng**: {song['duration']//60}:{song['duration']%60:02d}"
            ),
            color=discord.Color.green(),
        )
        await ctx.send(embed=embed)

    @commands.command(name="skip", aliases=["s"])
    async def skip(self, ctx: commands.Context) -> None:
        """Bỏ qua bài hiện tại.

        Args:
            ctx: Ngữ cảnh lệnh Discord.
        """
        guild_id = ctx.guild.id
        if guild_id not in self.voice_clients or not self.voice_clients[guild_id].is_playing():
            await ctx.send("❌ Không có bài nào đang phát.")
            return

        self.voice_clients[guild_id].stop()
        await ctx.send("⏭ Đã bỏ qua bài hiện tại.")
        logger.info(f"✅ Đã bỏ qua bài trong guild {guild_id}")

    @commands.command(name="pause")
    async def pause(self, ctx: commands.Context) -> None:
        """Tạm dừng nhạc.

        Args:
            ctx: Ngữ cảnh lệnh Discord.
        """
        guild_id = ctx.guild.id
        if guild_id not in self.voice_clients or not self.voice_clients[guild_id].is_playing():
            await ctx.send("❌ Không có bài nào đang phát.")
            return

        self.voice_clients[guild_id].pause()
        await ctx.send("⏸ Đã tạm dừng nhạc.")
        logger.info(f"✅ Đã tạm dừng nhạc trong guild {guild_id}")

    @commands.command(name="resume")
    async def resume(self, ctx: commands.Context) -> None:
        """Tiếp tục phát nhạc.

        Args:
            ctx: Ngữ cảnh lệnh Discord.
        """
        guild_id = ctx.guild.id
        if guild_id not in self.voice_clients or not self.voice_clients[guild_id].is_paused():
            await ctx.send("❌ Nhạc không bị tạm dừng.")
            return

        self.voice_clients[guild_id].resume()
        await ctx.send("▶ Đã tiếp tục phát nhạc.")
        logger.info(f"✅ Đã tiếp tục nhạc trong guild {guild_id}")

    @commands.command(name="stop")
    async def stop(self, ctx: commands.Context) -> None:
        """Dừng nhạc và xóa hàng đợi.

        Args:
            ctx: Ngữ cảnh lệnh Discord.
        """
        guild_id = ctx.guild.id
        if guild_id not in self.voice_clients:
            await ctx.send("❌ Bot không ở trong voice channel.")
            return

        if guild_id in self.queues:
            self.queues[guild_id].clear()
        self.now_playing.pop(guild_id, None)
        self.voice_clients[guild_id].stop()
        await self.voice_clients[guild_id].disconnect()
        self.voice_clients.pop(guild_id)
        await ctx.send("⏹ Đã dừng nhạc và rời voice channel.")
        logger.info(f"✅ Đã dừng nhạc trong guild {guild_id}")

    @commands.command(name="clear")
    async def clear(self, ctx: commands.Context) -> None:
        """Xóa toàn bộ hàng đợi.

        Args:
            ctx: Ngữ cảnh lệnh Discord.
        """
        guild_id = ctx.guild.id
        if guild_id not in self.queues or not self.queues[guild_id]:
            await ctx.send("📭 Hàng đợi hiện đang trống.")
            return

        self.queues[guild_id].clear()
        await ctx.send("🗑 Đã xóa toàn bộ hàng đợi.")
        logger.info(f"✅ Đã xóa hàng đợi trong guild {guild_id}")

    @commands.command(name="remove", aliases=["rm"])
    async def remove(self, ctx: commands.Context, index: int) -> None:
        """Xóa bài ở vị trí cụ thể trong hàng đợi.

        Args:
            ctx: Ngữ cảnh lệnh Discord.
            index: Vị trí bài cần xóa (bắt đầu từ 1).
        """
        guild_id = ctx.guild.id
        if guild_id not in self.queues or not self.queues[guild_id]:
            await ctx.send("📭 Hàng đợi hiện đang trống.")
            return

        if index < 1 or index > len(self.queues[guild_id]):
            await ctx.send("❌ Vị trí không hợp lệ.")
            return

        song = list(self.queues[guild_id])[index - 1]
        self.queues[guild_id].remove(song)
        await ctx.send(f"🗑 Đã xóa: {song['title']}.")
        logger.info(f"✅ Đã xóa bài {song['title']} trong guild {guild_id}")

    @commands.command(name="leave")
    async def leave(self, ctx: commands.Context) -> None:
        """Rời voice channel.

        Args:
            ctx: Ngữ cảnh lệnh Discord.
        """
        guild_id = ctx.guild.id
        if guild_id not in self.voice_clients:
            await ctx.send("❌ Bot không ở trong voice channel.")
            return

        if guild_id in self.queues:
            self.queues[guild_id].clear()
        self.now_playing.pop(guild_id, None)
        await self.voice_clients[guild_id].disconnect()
        self.voice_clients.pop(guild_id)
        await ctx.send("👋 Đã rời voice channel.")
        logger.info(f"✅ Đã rời voice channel trong guild {guild_id}")

    async def cog_unload(self) -> None:
        """Ngắt kết nối tất cả voice clients khi cog được gỡ."""
        for voice_client in self.voice_clients.values():
            await voice_client.disconnect()
        self.voice_clients.clear()