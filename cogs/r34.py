import asyncio
import random
from typing import Union

import discord
from discord import app_commands
from discord.ext import commands
from rule34Py import rule34Py
from rule34Py.post import Post

from cogs.base import BaseCog
from cogs.config import Config, get_config


class R34(BaseCog):
    """Rule34 image search — auto-enabled when API credentials are set."""

    def __init__(self, bot: commands.Bot) -> None:
        super().__init__(bot)
        self._api: rule34Py | None = None
        self._ready: bool = False
        self._seen_ids: set[int] = set()
        self._init_api()

    def _init_api(self) -> None:
        config = get_config()
        api_key = config.r34_api_key
        user_id = config.r34_user_id
        if api_key and user_id:
            self._api = rule34Py()
            self._api.api_key = api_key
            self._api.user_id = user_id
            self._ready = True
            self.logger.info("🔞 R34 ready — API credentials configured")
        else:
            self.logger.warning("🔞 R34 disabled — missing R34_API_KEY / R34_USER_ID")

    # ── NSFW channel check ─────────────────────────────────────────

    @staticmethod
    def _is_nsfw_channel(channel: Union[discord.TextChannel, discord.Thread, discord.DMChannel]) -> bool:
        if isinstance(channel, discord.DMChannel):
            return True
        if isinstance(channel, discord.Thread):
            parent = channel.parent
            return parent.is_nsfw() if parent else False
        return channel.is_nsfw()

    # ── API call via rule34Py ──────────────────────────────────────

    async def _search(self, query: str, limit: int) -> list[Post]:
        try:
            include_video = "video" in query.lower()
            tag_list = query.strip().split()
            all_fresh: list[Post] = []
            fallback: list[Post] = []
            for page in range(5):
                result = await asyncio.to_thread(self._api.search, tag_list, True, page, 100)
                if not isinstance(result, list) or not result:
                    continue
                if not include_video:
                    result = [p for p in result if p.content_type != "video"]
                if not result:
                    continue
                if not fallback:
                    fallback = result
                random.shuffle(result)
                all_fresh.extend(p for p in result if p.id not in self._seen_ids)
                if len(all_fresh) >= limit:
                    return all_fresh[:limit]
            return (all_fresh or fallback)[:limit]
        except TypeError as e:
            self.logger.error("rule34Py search error (invalid API credentials?): %s", e)
            return []
        except Exception as e:
            self.logger.error("rule34Py search error: %s", e)
            return []

    # ── Search ─────────────────────────────────────────────────────

    async def _send_results(
        self,
        target: Union[commands.Context, discord.Interaction],
        query: str,
    ) -> None:
        if not self._ready:
            await self.reply(target, "❌ R34 is not configured yet. Need to set `R34_API_KEY` and `R34_USER_ID` in .env.", ephemeral=True)
            return

        if not self._is_nsfw_channel(target.channel):
            await self.reply(target, "❌ This command can only be used in NSFW channels.", ephemeral=True)
            return

        if isinstance(target, discord.Interaction):
            await target.response.defer()

        full_query = f"{query}".strip()

        posts = await self._search(full_query, Config.R34_MAX_RESULTS)

        if not posts:
            await self.reply(target, f"❌ No results were found for `{full_query}`.", ephemeral=True)
            return

        total = min(len(posts), Config.R34_MAX_RESULTS)
        selected = posts[:total]

        if len(self._seen_ids) > 100:
            self._seen_ids.clear()
        self._seen_ids.update(p.id for p in selected)

        content = "\n".join(p.image or p.video or "" for p in selected)

        if isinstance(target, discord.Interaction):
            await target.followup.send(content)
        else:
            await target.send(content)

    @commands.command(name="r34")
    async def r34_command(self, ctx: commands.Context, *, query: str) -> None:
        await self._send_results(ctx, query)

    @app_commands.command(name="r34", description="Find photos on Rule34 (NSFW channel only)", nsfw=True)
    @app_commands.describe(query="Search keywords (tags)")
    async def slash_r34(self, interaction: discord.Interaction, query: str) -> None:
        await self._send_results(interaction, query)
