from pathlib import Path
from typing import Union

import aiohttp
import discord
from discord.ext import commands
from discord import app_commands

from cogs.base import BaseCog
from cogs.config import Config, get_config
from cogs.persistence import HistoryStore, MessageList


def load_markdown(filename: str) -> str:
    return (Path(__file__).resolve().parent.parent / filename).read_text(encoding="utf-8")


def _user_id(target: Union[commands.Context, discord.Interaction]) -> int:
    return target.author.id if isinstance(target, commands.Context) else target.user.id


def _user_name(target: Union[commands.Context, discord.Interaction]) -> str:
    return target.author.name if isinstance(target, commands.Context) else target.user.name


class Assistant(BaseCog):
    """Cog handling AI question-answering via OpenRouter with per-user memory."""

    def __init__(self, bot: commands.Bot) -> None:
        super().__init__(bot)
        self.api_key = get_config().openrouter_api_key
        self.ai_config = {
            "temperature": Config.AI_TEMPERATURE,
            "top_p": Config.AI_TOP_P,
            "max_tokens": Config.AI_MAX_TOKENS,
        }
        self.store = HistoryStore()
        self._session: aiohttp.ClientSession | None = None
        self._headers: dict = {}
        self.openrouter_ok: bool = False

        if self.api_key:
            self._headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
        else:
            self.logger.warning("⚠️ OPENROUTER_API_KEY not set. AI features will be disabled.")

    async def _check_openrouter(self) -> None:
        if not self.api_key:
            self.openrouter_ok = False
            return

        payload = {
            "model": Config.AI_MODEL,
            "messages": [{"role": "user", "content": "ping"}],
            "max_tokens": 5,
        }
        data = await self._post(payload)
        if data and data.get("choices"):
            self.openrouter_ok = True
            self.logger.info(f"✅ OpenRouter OK — model {Config.AI_MODEL}")
        else:
            self.openrouter_ok = False
            self.logger.error(f"❌ OpenRouter health check FAILED — model {Config.AI_MODEL}")

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        self.logger.info(f"🤖 Cog {self.__class__.__name__} ready, checking OpenRouter...")
        await self._check_openrouter()

    async def _get_session(self) -> aiohttp.ClientSession:
        session = self._session
        if session is None or session.closed:
            session = aiohttp.ClientSession()
            self._session = session
        return session

    async def _post(self, payload: dict) -> dict | None:
        session = await self._get_session()
        async with session.post(Config.OPENROUTER_API_URL, headers=self._headers, json=payload) as resp:
            if not resp.ok:
                text = await resp.text()
                self.logger.error(f"❌ OpenRouter API error {resp.status}: {text}")
                return None
            return await resp.json()

    async def _generate_ai_response(self, message: str, history: MessageList) -> str | None:
        if not self.api_key:
            return None

        try:
            system_prompt = load_markdown(Config.SYSTEM_PROMPT_FILE)
        except Exception as e:
            self.logger.error(f"❌ Failed to load {Config.SYSTEM_PROMPT_FILE}: {e}")
            system_prompt = Config.FALLBACK_SYSTEM_PROMPT

        payload = {
            "model": Config.AI_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                *history,
                {"role": "user", "content": message},
            ],
            **self.ai_config,
        }

        data = await self._post(payload)
        if not data:
            return None

        try:
            return data["choices"][0]["message"]["content"].strip()
        except (KeyError, IndexError):
            self.logger.error(f"❌ OpenRouter response format unexpected: {data}")
            return None

    async def _handle_ai_error(self, target, error: Exception) -> None:
        self.logger.error(f"❌ AI question error: {str(error)}")
        error_msg = str(error).lower()
        if "401" in error_msg or "unauthorized" in error_msg or "api key" in error_msg:
            await self.reply(target, "❌ Invalid API key. Please check your OPENROUTER_API_KEY configuration.")
        elif "402" in error_msg or "insufficient" in error_msg or "quota" in error_msg:
            await self.reply(target, "❌ API quota exceeded or insufficient balance. Please try again later.")
        elif "429" in error_msg or "rate limit" in error_msg:
            await self.reply(target, "❌ Rate limit exceeded. Please try again later.")
        else:
            await self.reply(target, "❌ AI error: Unable to process your request. Please try again later.")

    async def _handle_question(
        self,
        target: Union[commands.Context, discord.Interaction],
        message: str,
    ) -> None:
        if not self.api_key:
            await self.reply(target, "❌ AI unavailable. Please check your OPENROUTER_API_KEY configuration.")
            return

        user_id = _user_id(target)

        self.logger.info(
            f"User {user_id} asked: '{message[:50]}{'...' if len(message) > 50 else ''}'"
        )

        if isinstance(target, discord.Interaction):
            await target.response.defer()
            send = target.followup.send
        else:
            send = target.send

        history = self.store.load_history(user_id)

        try:
            if isinstance(target, discord.Interaction):
                reply = await self._generate_ai_response(message, history)
            else:
                async with target.channel.typing():
                    reply = await self._generate_ai_response(message, history)
        except Exception as e:
            await self._handle_ai_error(target, e)
            return

        if reply is None:
            await self.reply(target, "❌ AI could not generate a response. Please try again later.")
            return

        self.store.save_turn(user_id, _user_name(target), message, reply)

        self.logger.info(f"✅ AI responded to user {user_id} (length: {len(reply)} chars)")
        embed = self.embed(
            description=f"{reply}",
            color=discord.Color(Config.EMBED_COLOR),
        )

        if len(reply) > 2000:
            chunks = self.chunk_text(reply)
            embed.description = chunks[0]
            await send(embed=embed)
            for chunk in chunks[1:]:
                await send(f"```{chunk}```")
        else:
            await send(embed=embed)

    @commands.command(name="question", aliases=["q"])
    async def question_command(self, ctx: commands.Context, *, message: str) -> None:
        await self._handle_question(ctx, message)

    @app_commands.command(name="question", description="Ask the AI a question")
    @app_commands.describe(message="Your question for the AI")
    async def slash_question(self, interaction: discord.Interaction, message: str) -> None:
        await self._handle_question(interaction, message)

    @commands.command(name="forget")
    async def forget_command(self, ctx: commands.Context) -> None:
        self.store.clear_history(_user_id(ctx))
        await ctx.send("✅ Conversation memory cleared.")

    @app_commands.command(name="forget", description="Clear your conversation history with the AI")
    async def slash_forget(self, interaction: discord.Interaction) -> None:
        self.store.clear_history(_user_id(interaction))
        await interaction.response.send_message("✅ Conversation memory cleared.")
