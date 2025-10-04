import asyncio
import logging
import os
from typing import Optional

import discord
import google.generativeai as genai
from discord.ext import commands
from dotenv import load_dotenv

# Tải biến môi trường
load_dotenv()

# Cấu hình logger
logger = logging.getLogger(__name__)

# Định nghĩa model AI
AI_MODEL = "gemma-3-27b-it"


def load_markdown(filename: str) -> str:
    """Tải nội dung file markdown từ đường dẫn tương đối.

    Args:
        filename: Tên file markdown (ví dụ: system_prompt.md).

    Returns:
        Nội dung của file markdown.
    """
    path = os.path.join(os.path.dirname(__file__), "..", filename)
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


class Assistant(commands.Cog):
    """Cog xử lý các lệnh tương tác với AI sử dụng Google Gemini."""

    def __init__(self, bot: commands.Bot) -> None:
        """Khởi tạo cog Assistant.

        Args:
            bot: Đối tượng bot Discord.
        """
        self.bot = bot
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.model = None
        self.ai_config = {
            "temperature": 0.7,
            "top_p": 0.8,
            "top_k": 40,
            "max_output_tokens": 800,
        }

        # Thiết lập kết nối với Google Gemini
        if self.api_key:
            genai.configure(api_key=self.api_key)
            try:
                self.model = genai.GenerativeModel(AI_MODEL)
                logger.info(f"✅ Đã kết nối Gemini AI với model {AI_MODEL}")
            except Exception as e:
                logger.error(f"❌ Không thể kết nối Gemini AI: {e}")
        else:
            logger.warning("⚠️ GEMINI_API_KEY không được thiết lập. Tính năng AI sẽ không hoạt động.")

    @commands.command(name="ai", aliases=["chat", "ask"])
    async def ai_chat(self, ctx: commands.Context, *, message: str) -> None:
        """Lệnh để trò chuyện với AI Gemini.

        Args:
            ctx: Ngữ cảnh lệnh Discord.
            message: Tin nhắn người dùng gửi tới AI.
        """
        logger.info(
            f"{ctx.author} gọi lệnh !ai trong kênh {ctx.channel} với tin nhắn: "
            f"'{message[:50]}{'...' if len(message) > 50 else ''}'"
        )

        if not self.model:
            await ctx.send("❌ AI không khả dụng. Vui lòng kiểm tra cấu hình GEMINI_API_KEY.")
            return

        async with ctx.typing():
            try:
                # Tạo prompt với system prompt và tin nhắn hiện tại
                try:
                    system_prompt = load_markdown("system_prompt.md")
                    full_conversation = f"{system_prompt}\n\nUser: {message}\nAI: "
                except Exception as e:
                    logger.error(f"❌ Không thể tải nội dung file system_prompt.md: {e}")
                    full_conversation = f"User: {message}\nAI: "

                # Gửi yêu cầu tới Gemini AI
                response = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: self.model.generate_content(
                        full_conversation,
                        generation_config=genai.types.GenerationConfig(**self.ai_config),
                    ),
                )

                if response.text:
                    ai_response = response.text.strip()
                    logger.info(
                        f"✅ AI đã phản hồi thành công cho {ctx.author} "
                        f"(độ dài phản hồi: {len(ai_response)} ký tự)"
                    )

                    embed = discord.Embed(
                        title="🤖 Trợ lý DSB AI",
                        description=ai_response,
                        color=0x00FF88,
                    )
                    embed.set_footer(text=f"Được yêu cầu bởi {ctx.author.display_name}")

                    # Chia nhỏ tin nhắn nếu quá dài
                    if len(ai_response) > 2000:
                        chunks = [ai_response[i : i + 1900] for i in range(0, len(ai_response), 1900)]
                        for i, chunk in enumerate(chunks):
                            if i == 0:
                                embed.description = chunk
                                await ctx.send(embed=embed)
                            else:
                                await ctx.send(f"```{chunk}```")
                    else:
                        await ctx.send(embed=embed)
                else:
                    await ctx.send("❌ AI không thể tạo phản hồi. Vui lòng thử lại.")
            except Exception as e:
                logger.error(f"❌ Lỗi AI chat: {str(e)}")
                error_msg = str(e).lower()
                if "404" in error_msg and "model" in error_msg:
                    await ctx.send("❌ Model AI không khả dụng. Vui lòng kiểm tra API key hoặc thử lại sau.")
                elif "quota" in error_msg or "limit" in error_msg:
                    await ctx.send("❌ Đã đạt giới hạn API. Vui lòng thử lại sau.")
                elif "api key" in error_msg:
                    await ctx.send("❌ API key không hợp lệ. Vui lòng kiểm tra cấu hình.")
                else:
                    await ctx.send("❌ Lỗi AI: Không thể xử lý yêu cầu. Vui lòng thử lại sau.")

    @commands.command(name="aiconfig")
    @commands.has_permissions(administrator=True)
    async def ai_config_command(self, ctx: commands.Context, setting: Optional[str] = None, value: Optional[str] = None) -> None:
        """Cấu hình tham số AI (chỉ dành cho admin).

        Args:
            ctx: Ngữ cảnh lệnh Discord.
            setting: Tên tham số cần cấu hình (temperature, top_p, top_k, max_output_tokens).
            value: Giá trị mới cho tham số.
        """
        logger.info(
            f"{ctx.author} (ADMIN) gọi lệnh !aiconfig trong kênh {ctx.channel} "
            f"với setting: {setting}, value: {value}"
        )

        if not setting:
            embed = discord.Embed(title="⚙️ Cấu hình AI hiện tại", color=0x0099FF)
            for key, val in self.ai_config.items():
                embed.add_field(name=key, value=val, inline=True)
            await ctx.send(embed=embed)
            return

        if setting in self.ai_config and value:
            try:
                if setting in ["temperature", "top_p"]:
                    self.ai_config[setting] = float(value)
                elif setting in ["top_k", "max_output_tokens"]:
                    self.ai_config[setting] = int(value)
                logger.info(f"⚙️ {ctx.author} đã cập nhật AI config: {setting} = {self.ai_config[setting]}")
                await ctx.send(f"✅ Đã cập nhật {setting} = {self.ai_config[setting]}")
            except ValueError:
                await ctx.send("❌ Giá trị không hợp lệ.")
        else:
            await ctx.send("❌ Tham số không hợp lệ.")

    @commands.command(name="aihelp")
    async def ai_help(self, ctx: commands.Context) -> None:
        """Hiển thị hướng dẫn sử dụng các lệnh AI.

        Args:
            ctx: Ngữ cảnh lệnh Discord.
        """
        logger.info(f"{ctx.author} gọi lệnh !aihelp trong kênh {ctx.channel}")
        embed = discord.Embed(
            title="🤖 Hướng dẫn sử dụng AI",
            description="DSB AI sử dụng Google Gemini để trò chuyện thông minh.",
            color=0x00FF88,
        )
        embed.add_field(
            name="📝 Lệnh cơ bản",
            value=(
                "`!ai <tin nhắn>` - Chat với AI\n"
                "`!chat <tin nhắn>` - Alias của !ai\n"
                "`!ask <câu hỏi>` - Alias của !ai\n"
                "`!aihelp` - Hiển thị hướng dẫn này\n"
                "`!aistatus` - Kiểm tra trạng thái AI\n"
                "`!aiconfig [setting] [value]` - Cấu hình AI (chỉ admin)"
            ),
            inline=False,
        )
        embed.add_field(
            name="💡 Ví dụ sử dụng",
            value=(
                "`!ai Xin chào, bạn có thể làm gì?`\n"
                "`!ask Python là gì?`\n"
                "`!chat Hãy giải thích về Discord bot`"
            ),
            inline=False,
        )
        embed.add_field(
            name="🔧 Tính năng",
            value=(
                "• Trả lời bằng tiếng Việt hoặc tiếng Anh\n"
                "• Hỗ trợ câu hỏi đa dạng\n"
                "• Tự động chia tin nhắn dài\n"
                "• Cấu hình linh hoạt cho admin"
            ),
            inline=False,
        )
        await ctx.send(embed=embed)

    @commands.command(name="aistatus")
    async def ai_status(self, ctx: commands.Context) -> None:
        """Kiểm tra trạng thái hoạt động của AI.

        Args:
            ctx: Ngữ cảnh lệnh Discord.
        """
        logger.info(f"{ctx.author} gọi lệnh !aistatus trong kênh {ctx.channel}")
        if not self.api_key:
            await ctx.send("❌ GEMINI_API_KEY chưa được cấu hình.")
            return

        if not self.model:
            await ctx.send("❌ AI model chưa được khởi tạo.")
            return

        try:
            test_response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.model.generate_content(
                    "Hello",
                    generation_config=genai.types.GenerationConfig(max_output_tokens=10),
                ),
            )
            if test_response.text:
                embed = discord.Embed(
                    title="✅ AI Status",
                    description="Gemini AI đang hoạt động bình thường",
                    color=0x00FF88,
                )
                embed.add_field(name="Model", value=AI_MODEL, inline=True)
                embed.add_field(name="API Key", value="✅ Đã cấu hình", inline=True)
                await ctx.send(embed=embed)
            else:
                await ctx.send("⚠️ AI có thể hoạt động nhưng không trả về phản hồi.")
        except Exception as e:
            await ctx.send(f"❌ AI không hoạt động: {str(e)}")

    @ai_config_command.error
    async def ai_config_error(self, ctx: commands.Context, error: Exception) -> None:
        """Xử lý lỗi cho lệnh aiconfig.

        Args:
            ctx: Ngữ cảnh lệnh Discord.
            error: Lỗi được ném ra.
        """
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ Bạn cần quyền Administrator để sử dụng lệnh này.")