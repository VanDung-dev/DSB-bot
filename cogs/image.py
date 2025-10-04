import logging
import random
import time

import discord
from discord.ext import commands
from discord import app_commands
from ddgs import DDGS

# Cấu hình logger
logger = logging.getLogger(__name__)


class ImageSearch(commands.Cog):
    """Cog xử lý tìm kiếm ảnh từ DuckDuckGo."""

    def __init__(self, bot: commands.Bot) -> None:
        """Khởi tạo cog ImageSearch.

        Args:
            bot: Đối tượng bot Discord.
        """
        self.bot = bot

    @commands.command(name="image", aliases=["img"])
    async def image_search(self, ctx: commands.Context, *, query: str) -> None:
        """Tìm kiếm và gửi một ảnh từ DuckDuckGo.

        Args:
            ctx: Ngữ cảnh lệnh Discord.
            query: Từ khóa tìm kiếm ảnh.
        """
        logger.info(f"📸 {ctx.author} gọi lệnh !image với truy vấn: {query}")
        search_msg = await ctx.send(f"🔍 Đang tìm ảnh cho: **{query}**...")

        try:
            # Add a delay to help with rate limiting
            time.sleep(1)
            with DDGS() as ddgs:
                results = []
                retries = 3
                for attempt in range(retries):
                    try:
                        results = list(ddgs.images(query, max_results=10))
                        break
                    except Exception as e:
                        if "403" in str(e) or "Ratelimit" in str(e):
                            if attempt < retries - 1:  # Not the last attempt
                                time.sleep(2 ** attempt)  # Exponential backoff
                                continue
                        raise e
                
                if not results:
                    await search_msg.edit(content="❌ Không tìm thấy ảnh nào.")
                    logger.warning(f"⚠️ Không tìm thấy ảnh cho truy vấn: {query}")
                    return

                result = random.choice(results)
                image_url = result["image"]
                source_url = result.get("source", "")

                embed = discord.Embed(
                    title=f"Kết quả cho: {query}",
                    description=f"[Xem ảnh tại nguồn]({source_url})" if source_url else "",
                    color=discord.Color.blurple(),
                )
                embed.set_image(url=image_url)
                embed.set_footer(text="Nguồn: DuckDuckGo Image Search")

                await search_msg.edit(content="", embed=embed)
                logger.info(f"✅ Đã gửi ảnh cho truy vấn: {query}")
        except Exception as e:
            await search_msg.edit(content=f"❌ Lỗi khi tìm ảnh: {str(e)}")
            logger.error(f"❌ Lỗi khi tìm ảnh: {e}")
    
    @app_commands.command(name="image", description="Tìm kiếm ảnh từ DuckDuckGo")
    @app_commands.describe(query="Từ khóa tìm kiếm ảnh")
    async def slash_image(self, interaction: discord.Interaction, query: str) -> None:
        """Slash command tìm kiếm và gửi một ảnh từ DuckDuckGo.

        Args:
            interaction: Tương tác từ người dùng.
            query: Từ khóa tìm kiếm ảnh.
        """
        logger.info(f"📸 {interaction.user} gọi slash command /image với truy vấn: {query}")
        await interaction.response.send_message(f"🔍 Đang tìm ảnh cho: **{query}**...", ephemeral=False)
        
        try:
            # Add a delay to help with rate limiting
            time.sleep(1)
            with DDGS() as ddgs:
                results = []
                retries = 3
                for attempt in range(retries):
                    try:
                        results = list(ddgs.images(query, max_results=10))
                        break
                    except Exception as e:
                        if "403" in str(e) or "Ratelimit" in str(e):
                            if attempt < retries - 1:  # Not the last attempt
                                time.sleep(2 ** attempt)  # Exponential backoff
                                continue
                        raise e
                
                if not results:
                    await interaction.edit_original_response(content="❌ Không tìm thấy ảnh nào.")
                    logger.warning(f"⚠️ Không tìm thấy ảnh cho truy vấn: {query}")
                    return

                result = random.choice(results)
                image_url = result["image"]
                source_url = result.get("source", "")

                embed = discord.Embed(
                    title=f"Kết quả cho: {query}",
                    description=f"[Xem ảnh tại nguồn]({source_url})" if source_url else "",
                    color=discord.Color.blurple(),
                )
                embed.set_image(url=image_url)
                embed.set_footer(text="Nguồn: DuckDuckGo Image Search")

                await interaction.edit_original_response(content="", embed=embed)
                logger.info(f"✅ Đã gửi ảnh cho truy vấn: {query}")
        except Exception as e:
            await interaction.edit_original_response(content=f"❌ Lỗi khi tìm ảnh: {str(e)}")
            logger.error(f"❌ Lỗi khi tìm ảnh: {e}")

    @commands.command(name="meme")
    async def meme_search(self, ctx: commands.Context, *, query: str) -> None:
        """Tìm kiếm và gửi một meme từ DuckDuckGo.

        Args:
            ctx: Ngữ cảnh lệnh Discord.
            query: Từ khóa tìm kiếm meme.
        """
        query = f"{query} meme"  # Thêm từ "meme" vào truy vấn
        logger.info(f"📸 {ctx.author} gọi lệnh !meme với truy vấn: {query}")
        search_msg = await ctx.send(f"🔍 Đang tìm meme cho: **{query}**...")

        try:
            # Add a delay to help with rate limiting
            time.sleep(1)
            with DDGS() as ddgs:
                results = []
                retries = 3
                for attempt in range(retries):
                    try:
                        results = list(ddgs.images(query, max_results=10))
                        break
                    except Exception as e:
                        if "403" in str(e) or "Ratelimit" in str(e):
                            if attempt < retries - 1:  # Not the last attempt
                                time.sleep(2 ** attempt)  # Exponential backoff
                                continue
                        raise e

                if not results:
                    await search_msg.edit(content="❌ Không tìm thấy meme nào.")
                    logger.warning(f"⚠️ Không tìm thấy meme cho truy vấn: {query}")
                    return

                result = random.choice(results)
                image_url = result["image"]
                source_url = result.get("source", "")

                embed = discord.Embed(
                    title=f"Meme về: {query}",
                    description=f"[Xem ảnh tại nguồn]({source_url})" if source_url else "",
                    color=discord.Color.blurple(),
                )
                embed.set_image(url=image_url)
                embed.set_footer(text="Nguồn: DuckDuckGo Image Search")

                await search_msg.edit(content="", embed=embed)
                logger.info(f"✅ Đã gửi meme cho truy vấn: {query}")
        except Exception as e:
            await search_msg.edit(content=f"❌ Lỗi khi tìm meme: {str(e)}")
            logger.error(f"❌ Lỗi khi tìm meme: {e}")
            
    @app_commands.command(name="meme", description="Tìm kiếm meme từ DuckDuckGo")
    @app_commands.describe(query="Từ khóa tìm kiếm meme")
    async def slash_meme(self, interaction: discord.Interaction, query: str) -> None:
        """Slash command tìm kiếm và gửi một meme từ DuckDuckGo.

        Args:
            interaction: Tương tác từ người dùng.
            query: Từ khóa tìm kiếm meme.
        """
        query = f"{query} meme"  # Thêm từ "meme" vào truy vấn
        logger.info(f"📸 {interaction.user} gọi slash command /meme với truy vấn: {query}")
        await interaction.response.send_message(f"🔍 Đang tìm meme cho: **{query}**...", ephemeral=False)
        
        try:
            # Add a delay to help with rate limiting
            time.sleep(1)
            with DDGS() as ddgs:
                results = []
                retries = 3
                for attempt in range(retries):
                    try:
                        results = list(ddgs.images(query, max_results=10))
                        break
                    except Exception as e:
                        if "403" in str(e) or "Ratelimit" in str(e):
                            if attempt < retries - 1:  # Not the last attempt
                                time.sleep(2 ** attempt)  # Exponential backoff
                                continue
                        raise e

                if not results:
                    await interaction.edit_original_response(content="❌ Không tìm thấy meme nào.")
                    logger.warning(f"⚠️ Không tìm thấy meme cho truy vấn: {query}")
                    return

                result = random.choice(results)
                image_url = result["image"]
                source_url = result.get("source", "")

                embed = discord.Embed(
                    title=f"Meme về: {query}",
                    description=f"[Xem ảnh tại nguồn]({source_url})" if source_url else "",
                    color=discord.Color.blurple(),
                )
                embed.set_image(url=image_url)
                embed.set_footer(text="Nguồn: DuckDuckGo Image Search")

                await interaction.edit_original_response(content="", embed=embed)
                logger.info(f"✅ Đã gửi meme cho truy vấn: {query}")
        except Exception as e:
            await interaction.edit_original_response(content=f"❌ Lỗi khi tìm meme: {str(e)}")
            logger.error(f"❌ Lỗi khi tìm meme: {e}")