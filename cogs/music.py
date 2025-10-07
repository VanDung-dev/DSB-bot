import asyncio
import logging
from collections import deque
from typing import Dict, Optional

import discord
import wavelink
import os
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from dotenv import load_dotenv
from discord.ext import commands
from discord import app_commands

# Cấu hình logger
logger = logging.getLogger(__name__)


def is_spotify_url(url: str) -> bool:
    return "open.spotify.com" in url


class MusicSearch(commands.Cog):
    """Cog xử lý các lệnh phát nhạc từ YouTube/Spotify qua Lavalink."""

    def __init__(self, bot: commands.Bot) -> None:
        """Khởi tạo cog MusicSearch.

        Args:
            bot: Đối tượng bot Discord.
        """
        self.bot = bot
        self.queues: Dict[int, deque] = {}
        self.now_playing: Dict[int, dict] = {}
        self.voice_clients: Dict[int, wavelink.Player] = {}
        self.inactivity_timers: Dict[int, asyncio.Task] = {}

        load_dotenv()
        client_id = os.getenv("SPOTIFY_CLIENT_ID")
        client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")

        self.sp = None
        if client_id and client_secret:
            self.sp = spotipy.Spotify(
                auth_manager=SpotifyClientCredentials(
                    client_id=client_id,
                    client_secret=client_secret
                )
            )

        self.locks: Dict[int, asyncio.Lock] = {}

    async def cog_load(self):
        # Hàm này sẽ được gọi khi cog được load 
        await self.start_lavalink()

    async def start_lavalink(self):
        await self.bot.wait_until_ready()
        # Kết nối tới Lavalink node
        await wavelink.NodePool.create_node(
            bot=self.bot,
            host=os.getenv("LAVALINK_HOST", "localhost"),
            port=int(os.getenv("LAVALINK_PORT", 2333)),
            password=os.getenv("LAVALINK_PASSWORD", "youshallnotpass"),
            https=False,
            region="us_central"
        )

    @staticmethod
    def is_spotify_url(url: str) -> bool:
        return "open.spotify.com" in url

    def get_spotify_queries(self, url: str) -> list[str]:
        """Trả về danh sách query nhạc từ Spotify (track/album/playlist)."""
        if not self.sp:
            return []

        queries = []
        try:
            if "track" in url:
                track = self.sp.track(url)
                queries.append(f"{track['name']} {track['artists'][0]['name']}")
            elif "album" in url:
                album_id = url.split("/")[-1].split("?")[0]
                tracks = self.sp.album_tracks(album_id)
                for t in tracks["items"]:
                    queries.append(f"{t['name']} {t['artists'][0]['name']}")
            elif "playlist" in url:
                playlist_id = url.split("/")[-1].split("?")[0]
                tracks = self.sp.playlist_tracks(playlist_id)
                for item in tracks["items"]:
                    t = item["track"]
                    queries.append(f"{t['name']} {t['artists'][0]['name']}")
        except Exception as e:
            logger.error(f"❌ Lỗi khi lấy dữ liệu Spotify: {e}")

        return queries

    async def get_track(self, query: str) -> Optional[wavelink.tracks]:
        """Tìm kiếm và trả về track từ Lavalink."""
        try:
            tracks = await wavelink.YouTubeTrack.search(query=query)
            if tracks:
                return tracks[0]
        except Exception as e:
            logger.error(f"❌ Lỗi khi tìm kiếm track: {e}")
        return None

    async def disconnect_after_inactivity(self, guild_id: int, delay: int = 60) -> None:
        """Ngắt kết nối sau một khoảng thời gian không hoạt động."""
        await asyncio.sleep(delay)
        
        # Kiểm tra nếu vẫn không có hoạt động nào
        if guild_id in self.queues and len(self.queues[guild_id]) > 0:
            return  # Có bài hát trong hàng đợi, không ngắt kết nối
            
        if guild_id in self.now_playing:
            return  # Vẫn đang phát nhạc, không ngắt kết nối
            
        # Kiểm tra nếu có bot đang nói
        speaking_cog = self.bot.get_cog('Speaking')
        if speaking_cog and guild_id in speaking_cog.speaking_states:
            return  # Bot đang nói, không ngắt kết nối
            
        # Ngắt kết nối do không hoạt động
        if guild_id in self.voice_clients:
            await self.voice_clients[guild_id].disconnect()
            self.voice_clients.pop(guild_id)
            logger.info(f"✅ Đã ngắt kết nối khỏi voice channel do không hoạt động trong guild {guild_id}")

    def reset_inactivity_timer(self, guild_id: int) -> None:
        """Đặt lại bộ đếm thời gian không hoạt động."""
        # Hủy bộ đếm thời gian trước đó nếu có
        if guild_id in self.inactivity_timers:
            self.inactivity_timers[guild_id].cancel()
            
        # Tạo bộ đếm thời gian mới
        self.inactivity_timers[guild_id] = asyncio.create_task(
            self.disconnect_after_inactivity(guild_id)
        )

    async def play_next(self, guild_id: int) -> None:
        """Phát bài tiếp theo trong hàng đợi.

        Args:
            guild_id: ID của server Discord.
        """
        if guild_id not in self.queues or not self.queues[guild_id]:
            self.now_playing.pop(guild_id, None)
            # Đặt bộ đếm thời gian để ngắt kết nối sau 1 phút không hoạt động
            self.reset_inactivity_timer(guild_id)
            return

        song = self.queues[guild_id].popleft()
        self.now_playing[guild_id] = song

        try:
            player = self.voice_clients[guild_id]
            speaking_cog = self.bot.get_cog('Speaking')
            while player.is_playing() or (speaking_cog and guild_id in speaking_cog.speaking_states):
                await asyncio.sleep(0.5)
            await player.play(song["track"])
            # Gửi embed vào channel gốc của lệnh, nếu có
            text_channel = song.get("origin_channel")
            if text_channel is not None:
                embed = discord.Embed(
                    title="🎵 Đang phát",
                    description=(
                        f"[{song['track'].title}]({song['track'].uri})\n"
                        f"**Người tải lên**: {song['track'].author}\n"
                        f"**Thời lượng**: {song['track'].duration//60000}:{(song['track'].duration//1000)%60:02d}"
                    ),
                    color=discord.Color.green(),
                )
                await text_channel.send(embed=embed)
            logger.info(f"✅ Đang phát: {song['track'].title} trong guild {guild_id}")
        except Exception as e:
            logger.error(f"❌ Lỗi khi phát nhạc: {e}")
            await self.play_next(guild_id)

    @commands.command(name="play", aliases=["p"])
    async def play(self, ctx: commands.Context, *, query: str) -> None:
        guild_id = ctx.guild.id

        if guild_id not in self.locks:
            self.locks[guild_id] = asyncio.Lock()

        async with self.locks[guild_id]:
            if not ctx.author.voice:
                await ctx.send("❌ Bạn cần ở trong voice channel để sử dụng lệnh này.")
                return

            voice_channel = ctx.author.voice.channel

            if guild_id not in self.voice_clients:
                try:
                    player: wavelink.Player = await voice_channel.connect(cls=wavelink.Player)
                    self.voice_clients[guild_id] = player
                except discord.errors.ClientException:
                    await ctx.send("❌ Bot đã ở trong voice channel khác.")
                    return
                except Exception as e:
                    logger.error(f"❌ Lỗi khi kết nối voice channel: {e}")
                    await ctx.send("❌ Lỗi khi kết nối voice channel.")
                    return

            # Hủy bộ đếm thời gian không hoạt động khi có yêu cầu mới
            if guild_id in self.inactivity_timers:
                self.inactivity_timers[guild_id].cancel()
                self.inactivity_timers.pop(guild_id)

            # Kiểm tra xem bot có đang nói không
            speaking_cog = self.bot.get_cog('Speaking')
            if speaking_cog and guild_id in speaking_cog.speaking_states:
                await ctx.send("❌ Bot đang nói, vui lòng đợi nói xong rồi phát nhạc.")
                return

            # Kiểm tra nếu là link Spotify
            if self.is_spotify_url(query):
                queries = self.get_spotify_queries(query)
                if not queries:
                    await ctx.send("❌ Không lấy được nhạc từ Spotify.")
                    return

                first = True
                for q in queries:
                    track = await self.get_track(q)
                    if not track:
                        continue

                    if guild_id not in self.queues:
                        self.queues[guild_id] = deque()
                    self.queues[guild_id].append({"track": track, "origin_channel": ctx.channel})

                    if first:
                        if guild_id in self.now_playing:
                            embed = discord.Embed(
                                title="✅ Đã thêm từ Spotify vào hàng đợi",
                                description=f"[{track.title}]({track.uri})",
                                color=discord.Color.blue(),
                            )
                            await ctx.send(embed=embed)
                        else:
                            embed = discord.Embed(
                                title="🎵 Đang phát từ Spotify",
                                description=f"[{track.title}]({track.uri})",
                                color=discord.Color.green(),
                            )
                            await ctx.send(embed=embed)
                            await self.play_next(guild_id)
                        first = False
                return

            # Nếu là YouTube hoặc search
            search_msg = await ctx.send(f"🔍 Đang tìm: **{query}**...")
            track = await self.get_track(query)
            if not track:
                await ctx.send(f"❌ Không tìm thấy track cho '{query}'.")
                return

            if guild_id not in self.queues:
                self.queues[guild_id] = deque()
            self.queues[guild_id].append({"track": track, "origin_channel": ctx.channel})

            embed = discord.Embed(
                title="✅ Đã thêm vào hàng đợi",
                description=f"[{track.title}]({track.uri})",
                color=discord.Color.blue(),
            )
            await search_msg.edit(content="", embed=embed)

            if guild_id not in self.now_playing:
                await self.play_next(guild_id)

    @app_commands.command(name="play", description="Phát nhạc hoặc thêm vào hàng đợi")
    @app_commands.describe(query="URL hoặc từ khóa tìm kiếm")
    async def slash_play(self, interaction: discord.Interaction, query: str) -> None:
        """Slash command phát nhạc hoặc thêm vào hàng đợi.

        Args:
            interaction: Tương tác từ người dùng.
            query: URL hoặc từ khóa tìm kiếm.
        """
        guild_id = interaction.guild.id

        if guild_id not in self.locks:
            self.locks[guild_id] = asyncio.Lock()

        async with self.locks[guild_id]:
            await interaction.response.send_message(f"🔍 Đang tìm: **{query}**...", ephemeral=False)

            if not interaction.user.voice:
                await interaction.edit_original_response(content="❌ Bạn cần ở trong voice channel để sử dụng lệnh này.")
                return

            voice_channel = interaction.user.voice.channel

            if guild_id not in self.voice_clients:
                try:
                    player: wavelink.Player = await voice_channel.connect(cls=wavelink.Player)
                    self.voice_clients[guild_id] = player
                except discord.errors.ClientException:
                    await interaction.edit_original_response(content="❌ Bot đã ở trong voice channel khác.")
                    return
                except Exception as e:
                    logger.error(f"❌ Lỗi khi kết nối voice channel: {e}")
                    await interaction.edit_original_response(content="❌ Lỗi khi kết nối voice channel.")
                    return

            # Hủy bộ đếm thời gian không hoạt động khi có yêu cầu mới
            if guild_id in self.inactivity_timers:
                self.inactivity_timers[guild_id].cancel()
                self.inactivity_timers.pop(guild_id)

            # Kiểm tra xem bot có đang nói không
            speaking_cog = self.bot.get_cog('Speaking')
            if speaking_cog and guild_id in speaking_cog.speaking_states:
                await interaction.edit_original_response(content="❌ Bot đang nói, vui lòng đợi nói xong rồi phát nhạc.")
                return

            # Kiểm tra nếu là link Spotify
            if self.is_spotify_url(query):
                queries = self.get_spotify_queries(query)
                if not queries:
                    await interaction.edit_original_response(content="❌ Không lấy được nhạc từ Spotify.")
                    return

                first = True
                for q in queries:
                    track = await self.get_track(q)
                    if not track:
                        continue

                    if guild_id not in self.queues:
                        self.queues[guild_id] = deque()
                    self.queues[guild_id].append({"track": track, "origin_channel": interaction.channel})

                    if first:
                        if guild_id in self.now_playing:
                            embed = discord.Embed(
                                title="✅ Đã thêm từ Spotify vào hàng đợi",
                                description=f"[{track.title}]({track.uri})",
                                color=discord.Color.blue(),
                            )
                            await interaction.edit_original_response(content="", embed=embed)
                        else:
                            embed = discord.Embed(
                                title="🎵 Đang phát từ Spotify",
                                description=f"[{track.title}]({track.uri})",
                                color=discord.Color.green(),
                            )
                            await interaction.edit_original_response(content="", embed=embed)
                            await self.play_next(guild_id)
                        first = False
                return

            track = await self.get_track(query)
            if not track:
                await interaction.edit_original_response(content=f"❌ Không tìm thấy track cho '{query}'.")
                return

            if guild_id not in self.queues:
                self.queues[guild_id] = deque()
            self.queues[guild_id].append({"track": track, "origin_channel": interaction.channel})

            embed = discord.Embed(
                title="✅ Đã thêm vào hàng đợi",
                description=f"[{track.title}]({track.uri})",
                color=discord.Color.blue(),
            )
            await interaction.edit_original_response(content="", embed=embed)

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
                f"{i+1}. [{song['track'].title}]({song['track'].uri}) ({song['track'].duration//60000}:{(song['track'].duration//1000)%60:02d})"
                for i, song in enumerate(self.queues[guild_id])
            ),
            color=discord.Color.purple(),
        )
        if guild_id in self.now_playing:
            embed.add_field(
                name="Đang phát",
                value=f"[{self.now_playing[guild_id]['track'].title}]({self.now_playing[guild_id]['track'].uri})",
                inline=False,
            )
        await ctx.send(embed=embed)
        
    @app_commands.command(name="queue", description="Hiển thị danh sách hàng đợi")
    async def slash_queue(self, interaction: discord.Interaction) -> None:
        """Slash command hiển thị danh sách hàng đợi.

        Args:
            interaction: Tương tác từ người dùng.
        """
        guild_id = interaction.guild.id
        if guild_id not in self.queues or not self.queues[guild_id]:
            await interaction.response.send_message("📭 Hàng đợi hiện đang trống.", ephemeral=True)
            return

        embed = discord.Embed(
            title="📜 Danh sách hàng đợi",
            description="\n".join(
                f"{i+1}. [{song['track'].title}]({song['track'].uri}) ({song['track'].duration//60000}:{(song['track'].duration//1000)%60:02d})"
                for i, song in enumerate(self.queues[guild_id])
            ),
            color=discord.Color.purple(),
        )
        if guild_id in self.now_playing:
            embed.add_field(
                name="Đang phát",
                value=f"[{self.now_playing[guild_id]['track'].title}]({self.now_playing[guild_id]['track'].uri})",
                inline=False,
            )
        await interaction.response.send_message(embed=embed)

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
                f"[{song['track'].title}]({song['track'].uri})\n"
                f"**Người tải lên**: {song['track'].author}\n"
                f"**Thời lượng**: {song['track'].duration//60000}:{(song['track'].duration//1000)%60:02d}"
            ),
            color=discord.Color.green(),
        )
        await ctx.send(embed=embed)
        
    @app_commands.command(name="nowplaying", description="Hiển thị bài đang phát")
    async def slash_now_playing(self, interaction: discord.Interaction) -> None:
        """Slash command hiển thị bài đang phát.

        Args:
            interaction: Tương tác từ người dùng.
        """
        guild_id = interaction.guild.id
        if guild_id not in self.now_playing:
            await interaction.response.send_message("📭 Hiện không có bài nào đang phát.", ephemeral=True)
            return

        song = self.now_playing[guild_id]
        embed = discord.Embed(
            title="🎵 Đang phát",
            description=(
                f"[{song['track'].title}]({song['track'].uri})\n"
                f"**Người tải lên**: {song['track'].author}\n"
                f"**Thời lượng**: {song['track'].duration//60000}:{(song['track'].duration//1000)%60:02d}"
            ),
            color=discord.Color.green(),
        )
        await interaction.response.send_message(embed=embed)

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

        await self.voice_clients[guild_id].stop()
        await ctx.send("⏭ Đã bỏ qua bài hiện tại.")
        logger.info(f"✅ Đã bỏ qua bài trong guild {guild_id}")
        
    @app_commands.command(name="skip", description="Bỏ qua bài hiện tại")
    async def slash_skip(self, interaction: discord.Interaction) -> None:
        """Slash command bỏ qua bài hiện tại.

        Args:
            interaction: Tương tác từ người dùng.
        """
        guild_id = interaction.guild.id
        if guild_id not in self.voice_clients or not self.voice_clients[guild_id].is_playing():
            await interaction.response.send_message("❌ Không có bài nào đang phát.", ephemeral=True)
            return

        await self.voice_clients[guild_id].stop()
        await interaction.response.send_message("⏭ Đã bỏ qua bài hiện tại.")
        logger.info(f"✅ Đã bỏ qua bài trong guild {guild_id}")

    @commands.command(name="pause")
    async def pause(self, ctx: commands.Context) -> None:
        """Tạm dừng nhạc.

        Args:
            ctx: Ngữ cảnh lệnh Discord.
        """
        guild_id = ctx.guild.id
        if guild_id not in self.voice_clients:
            await ctx.send("❌ Bot không ở trong voice channel.")
            return

        vc = self.voice_clients[guild_id]

        if vc.is_playing():
            await vc.pause()
            await ctx.send("⏸ Đã tạm dừng nhạc.")
            logger.info(f"✅ Đã tạm dừng nhạc trong guild {guild_id}")
        elif vc.is_paused():
            await vc.resume()
            await ctx.send("▶ Đã tiếp tục phát nhạc.")
            logger.info(f"✅ Đã tiếp tục nhạc trong guild {guild_id}")
        else:
            await ctx.send("❌ Không có nhạc để dừng/tiếp tục.")

    @app_commands.command(name="pause", description="Tạm dừng hoặc tiếp tục nhạc")
    async def slash_pause(self, interaction: discord.Interaction) -> None:
        """Slash command tạm dừng nhạc.

        Args:
            interaction: Tương tác từ người dùng.
        """
        guild_id = interaction.guild.id
        if guild_id not in self.voice_clients:
            await interaction.response.send_message("❌ Bot không ở trong voice channel.", ephemeral=True)
            return

        vc = self.voice_clients[guild_id]

        if vc.is_playing():
            await vc.pause()
            await interaction.response.send_message("⏸ Đã tạm dừng nhạc.")
            logger.info(f"✅ Đã tạm dừng nhạc trong guild {guild_id}")
        elif vc.is_paused():
            await vc.resume()
            await interaction.response.send_message("▶ Đã tiếp tục phát nhạc.")
            logger.info(f"✅ Đã tiếp tục nhạc trong guild {guild_id}")
        else:
            await interaction.response.send_message("❌ Không có nhạc để dừng/tiếp tục.", ephemeral=True)

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

        await self.voice_clients[guild_id].resume()
        await ctx.send("▶ Đã tiếp tục phát nhạc.")
        logger.info(f"✅ Đã tiếp tục nhạc trong guild {guild_id}")
        
    @app_commands.command(name="resume", description="Tiếp tục phát nhạc")
    async def slash_resume(self, interaction: discord.Interaction) -> None:
        """Slash command tiếp tục phát nhạc.

        Args:
            interaction: Tương tác từ người dùng.
        """
        guild_id = interaction.guild.id
        if guild_id not in self.voice_clients or not self.voice_clients[guild_id].is_paused():
            await interaction.response.send_message("❌ Nhạc không bị tạm dừng.", ephemeral=True)
            return

        await self.voice_clients[guild_id].resume()
        await interaction.response.send_message("▶ Đã tiếp tục phát nhạc.")
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

        # Hủy bộ đếm thời gian không hoạt động
        if guild_id in self.inactivity_timers:
            self.inactivity_timers[guild_id].cancel()
            self.inactivity_timers.pop(guild_id)

        if guild_id in self.queues:
            self.queues[guild_id].clear()
        self.now_playing.pop(guild_id, None)
        await self.voice_clients[guild_id].stop()
        await self.voice_clients[guild_id].disconnect()
        self.voice_clients.pop(guild_id)
        await ctx.send("⏹ Đã dừng nhạc và rời voice channel.")
        logger.info(f"✅ Đã dừng nhạc trong guild {guild_id}")

    @app_commands.command(name="stop", description="Dừng nhạc và xóa hàng đợi")
    async def slash_stop(self, interaction: discord.Interaction) -> None:
        guild_id = interaction.guild.id
        if guild_id not in self.voice_clients:
            await interaction.response.send_message("❌ Bot không ở trong voice channel.", ephemeral=True)
            return

        # Hủy bộ đếm thời gian không hoạt động
        if guild_id in self.inactivity_timers:
            self.inactivity_timers[guild_id].cancel()
            self.inactivity_timers.pop(guild_id)

        # Trả lời ngay cho Discord
        await interaction.response.send_message("⏹ Đang dừng nhạc và thoát...")

        if guild_id in self.queues:
            self.queues[guild_id].clear()
        self.now_playing.pop(guild_id, None)

        await self.voice_clients[guild_id].stop()
        await self.voice_clients[guild_id].disconnect()
        self.voice_clients.pop(guild_id)

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
        
    @app_commands.command(name="clear", description="Xóa toàn bộ hàng đợi")
    async def slash_clear(self, interaction: discord.Interaction) -> None:
        """Slash command xóa toàn bộ hàng đợi.

        Args:
            interaction: Tương tác từ người dùng.
        """
        guild_id = interaction.guild.id
        if guild_id not in self.queues or not self.queues[guild_id]:
            await interaction.response.send_message("📭 Hàng đợi hiện đang trống.", ephemeral=True)
            return

        self.queues[guild_id].clear()
        await interaction.response.send_message("🗑 Đã xóa toàn bộ hàng đợi.")
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
        await ctx.send(f"🗑 Đã xóa: {song['track'].title}.")
        logger.info(f"✅ Đã xóa bài {song['track'].title} trong guild {guild_id}")
        
    @app_commands.command(name="remove", description="Xóa bài ở vị trí cụ thể trong hàng đợi")
    @app_commands.describe(index="Vị trí bài cần xóa (bắt đầu từ 1)")
    async def slash_remove(self, interaction: discord.Interaction, index: int) -> None:
        """Slash command xóa bài ở vị trí cụ thể trong hàng đợi.

        Args:
            interaction: Tương tác từ người dùng.
            index: Vị trí bài cần xóa (bắt đầu từ 1).
        """
        guild_id = interaction.guild.id
        if guild_id not in self.queues or not self.queues[guild_id]:
            await interaction.response.send_message("📭 Hàng đợi hiện đang trống.", ephemeral=True)
            return

        if index < 1 or index > len(self.queues[guild_id]):
            await interaction.response.send_message("❌ Vị trí không hợp lệ.", ephemeral=True)
            return

        song = list(self.queues[guild_id])[index - 1]
        self.queues[guild_id].remove(song)
        await interaction.response.send_message(f"🗑 Đã xóa: {song['track'].title}.")
        logger.info(f"✅ Đã xóa bài {song['track'].title} trong guild {guild_id}")

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

        # Hủy bộ đếm thời gian không hoạt động
        if guild_id in self.inactivity_timers:
            self.inactivity_timers[guild_id].cancel()
            self.inactivity_timers.pop(guild_id)

        if guild_id in self.queues:
            self.queues[guild_id].clear()
        self.now_playing.pop(guild_id, None)
        await self.voice_clients[guild_id].disconnect()
        self.voice_clients.pop(guild_id)
        await ctx.send("👋 Đã rời voice channel.")
        logger.info(f"✅ Đã rời voice channel trong guild {guild_id}")
        
    @app_commands.command(name="leave", description="Rời voice channel")
    async def slash_leave(self, interaction: discord.Interaction) -> None:
        """Slash command rời voice channel.

        Args:
            interaction: Tương tác từ người dùng.
        """
        guild_id = interaction.guild.id
        if guild_id not in self.voice_clients:
            await interaction.response.send_message("❌ Bot không ở trong voice channel.", ephemeral=True)
            return

        # Hủy bộ đếm thời gian không hoạt động
        if guild_id in self.inactivity_timers:
            self.inactivity_timers[guild_id].cancel()
            self.inactivity_timers.pop(guild_id)

        if guild_id in self.queues:
            self.queues[guild_id].clear()
        self.now_playing.pop(guild_id, None)
        await self.voice_clients[guild_id].disconnect()
        self.voice_clients.pop(guild_id)
        await interaction.response.send_message("👋 Đã rời voice channel.")
        logger.info(f"✅ Đã rời voice channel trong guild {guild_id}")

    async def cog_unload(self) -> None:
        """Ngắt kết nối tất cả voice clients khi cog được gỡ."""
        # Hủy tất cả bộ đếm thời gian không hoạt động
        for timer in self.inactivity_timers.values():
            timer.cancel()
        self.inactivity_timers.clear()
        
        for voice_client in self.voice_clients.values():
            await voice_client.disconnect()
        self.voice_clients.clear()