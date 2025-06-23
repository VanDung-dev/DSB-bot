import logging
import random

import discord
from discord.ext import commands
from duckduckgo_search import DDGS

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
            with DDGS() as ddgs:
                results = list(ddgs.images(query, max_results=10))
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
