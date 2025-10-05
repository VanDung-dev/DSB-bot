import asyncio
import logging
import os
import sys
from typing import List

import colorlog
import discord
from discord.ext import commands
from dotenv import load_dotenv

from cogs.assistant import Assistant
from cogs.help import Help
from cogs.image import ImageSearch
from cogs.moderation import Moderation
from cogs.music import MusicSearch
from cogs.welcome import Welcome
from cogs.speak import Speaking

from slash_setup import initialize_slash_commands


# Kiểm tra phiên bản Python tối thiểu
if sys.version_info < (3, 11):
    print("Yêu cầu Python 3.11 trở lên.")
    sys.exit(1)

def check_and_create_env() -> None:
    """Kiểm tra file .env và tạo nếu cần thiết."""
    env_path = ".env"
    example_env_path = ".env.example"
    
    # Nếu file .env đã tồn tại, kiểm tra các biến cần thiết
    if os.path.exists(env_path):
        load_dotenv()
        discord_token = os.getenv("KEY_DISCORD")
        # Nếu đã có token hợp lệ, không cần tạo lại
        if discord_token and discord_token.strip():
            return
    
    # Đọc các giá trị mặc định từ file .env.example nếu tồn tại
    env_vars = {}
    if os.path.exists(example_env_path):
        with open(example_env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    if "=" in line:
                        key, value = line.split("=", 1)
                        env_vars[key] = value
    
    print("⚠️  File .env chưa được cấu hình hoặc thiếu thông tin.")
    print("Vui lòng nhập các giá trị sau:")
    
    # Yêu cầu người dùng nhập token Discord (bắt buộc)
    discord_token = ""
    while not discord_token.strip():
        discord_token = input(f"KEY_DISCORD (Discord Bot Token) [{'Nhập token của bạn ở đây' if not env_vars.get('KEY_DISCORD') or env_vars.get('KEY_DISCORD') == 'your_discord_bot_token_here' else env_vars.get('KEY_DISCORD')}]: ").strip()
        if not discord_token.strip():
            print("❌ KEY_DISCORD là bắt buộc. Vui lòng nhập token hợp lệ.")
    
    env_vars["KEY_DISCORD"] = discord_token
    
    # Yêu cầu người dùng nhập các giá trị tùy chọn
    gemini_api_key = input(f"GEMINI_API_KEY (Gemini API Key - để trống nếu không dùng chức năng AI) [{env_vars.get('GEMINI_API_KEY', 'your_gemini_api_key_here')}]: ").strip()
    if gemini_api_key:
        env_vars["GEMINI_API_KEY"] = gemini_api_key
    elif not env_vars.get("GEMINI_API_KEY") or env_vars.get("GEMINI_API_KEY") == "your_gemini_api_key_here":
        env_vars["GEMINI_API_KEY"] = ""
    
    spotify_client_id = input(f"SPOTIFY_CLIENT_ID (Spotify Client ID - để trống nếu không dùng chức năng phát nhạc từ Spotify) [{env_vars.get('SPOTIFY_CLIENT_ID', 'your_spotify_client_id_here')}]: ").strip()
    if spotify_client_id:
        env_vars["SPOTIFY_CLIENT_ID"] = spotify_client_id
    elif not env_vars.get("SPOTIFY_CLIENT_ID") or env_vars.get("SPOTIFY_CLIENT_ID") == "your_spotify_client_id_here":
        env_vars["SPOTIFY_CLIENT_ID"] = ""
    
    spotify_client_secret = input(f"SPOTIFY_CLIENT_SECRET (Spotify Client Secret - để trống nếu không dùng chức năng phát nhạc từ Spotify) [{env_vars.get('SPOTIFY_CLIENT_SECRET', 'your_spotify_secret_id_here')}]: ").strip()
    if spotify_client_secret:
        env_vars["SPOTIFY_CLIENT_SECRET"] = spotify_client_secret
    elif not env_vars.get("SPOTIFY_CLIENT_SECRET") or env_vars.get("SPOTIFY_CLIENT_SECRET") == "your_spotify_secret_id_here":
        env_vars["SPOTIFY_CLIENT_SECRET"] = ""
    
    # Ghi các giá trị vào file .env
    with open(env_path, "w", encoding="utf-8") as f:
        f.write("# Discord Bot Token - Nhận nó từ https://discord.com/developers/applications\n")
        f.write(f"KEY_DISCORD={env_vars.get('KEY_DISCORD', '')}\n\n")
        
        f.write("# Gemini API Key - Nhận nó từ https://aistudio.google.com/\n")
        f.write(f"GEMINI_API_KEY={env_vars.get('GEMINI_API_KEY', '')}\n\n")
        
        f.write("# Spotify Client - Nhận nó từ https://developer.spotify.com/dashboard\n")
        f.write(f"SPOTIFY_CLIENT_ID={env_vars.get('SPOTIFY_CLIENT_ID', '')}\n")
        f.write(f"SPOTIFY_CLIENT_SECRET={env_vars.get('SPOTIFY_CLIENT_SECRET', '')}\n\n")
    
    print(f"✅ Đã lưu cấu hình vào {env_path}")
    print("Vui lòng khởi động lại bot!")
    sys.exit(0)

# Kiểm tra và tạo file .env nếu cần
check_and_create_env()

# Tải biến môi trường từ file .env
load_dotenv()

# Cấu hình logging với màu sắc
LOG_FORMAT = "%(log_color)s[%(asctime)s] [%(levelname)s] %(name)s: %(message)s"
LOG_DATE = "%Y-%m-%d %H:%M:%S"
LOG_COLORS = {
    "DEBUG": "cyan",
    "INFO": "green",
    "WARNING": "yellow",
    "ERROR": "red",
    "CRITICAL": "bold_red",
}

# Thiết lập handler cho terminal
stream_handler = colorlog.StreamHandler()
stream_handler.setFormatter(
    colorlog.ColoredFormatter(LOG_FORMAT, datefmt=LOG_DATE, log_colors=LOG_COLORS)
)

# Cấu hình root logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(stream_handler)

# Thiết lập intents cho bot
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
intents.members = True

# Khởi tạo bot với intents
bot = commands.Bot(command_prefix="", intents=intents, help_command=None)


@bot.event
async def on_ready() -> None:
    """Sự kiện khi bot sẵn sàng hoạt động."""
    logger.info(f"🤖 Bot đã đăng nhập thành công: {bot.user} (ID: {bot.user.id})")
    # Khởi tạo lệnh slash
    slash_setup = await initialize_slash_commands(bot)
    logger.info("✅ Đã khởi tạo slash commands")


async def setup_cogs() -> None:
    """Đăng ký các cog cho bot."""
    cogs: List[commands.Cog] = [
        MusicSearch(bot),
        Help(bot),
        Assistant(bot),
        Welcome(bot),
        ImageSearch(bot),
        Moderation(bot),
        Speaking(bot),
    ]
    for cog in cogs:
        try:
            await bot.add_cog(cog)
            logger.info(f"✅ Đã đăng ký cog: {cog.__class__.__name__}")
        except Exception as e:
            logger.error(f"❌ Lỗi khi đăng ký cog {cog.__class__.__name__}: {e}")


async def main() -> None:
    """Hàm chính để khởi động bot."""
    try:
        await setup_cogs()
        discord_token = os.getenv("KEY_DISCORD")
        if not discord_token:
            logger.error("❌ KEY_DISCORD không được thiết lập trong biến môi trường")
            return
        await bot.start(discord_token)
    except Exception as e:
        logger.error(f"❌ Lỗi khi khởi động bot: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())