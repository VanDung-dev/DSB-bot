import logging
from typing import Union, cast

import discord
from discord.ext import commands
from discord import app_commands

from cogs.config import Config


async def defer_response(
        target: Union[commands.Context, discord.Interaction],
    content: str = "⏳ Processing...",
) -> discord.Message:
    if isinstance(target, discord.Interaction):
        await target.response.send_message(content=content)
        return await target.original_response()
    return await target.send(content=content)


class BaseCog(commands.Cog):
    """Base class for all cogs providing common utilities."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self._logger: logging.Logger | None = None

    @property
    def logger(self) -> logging.Logger:
        if self._logger is None:
            self._logger = logging.getLogger(self.__class__.__module__)
        return cast(logging.Logger, self._logger)

    # ── Embed helpers ──────────────────────────────────────────

    def bot_thumbnail_url(self) -> str:
        user = self.bot.user
        if user is None:
            return ""
        avatar = user.avatar
        return avatar.url if avatar else user.default_avatar.url

    @staticmethod
    def make_embed(
        title: str = "",
        description: str = "",
        color: discord.Color = discord.Color.green(),
        **kwargs,
    ) -> discord.Embed:
        return discord.Embed(title=title, description=description, color=color, **kwargs)

    def embed(
        self,
        title: str = "",
        description: str = "",
        color: discord.Color = discord.Color.green(),
        footer: str = Config.EMBED_FOOTER,
        thumbnail: bool = False,
        **kwargs,
    ) -> discord.Embed:
        e = discord.Embed(title=title, description=description, color=color, **kwargs)
        if footer:
            e.set_footer(text=footer)
        if thumbnail:
            e.set_thumbnail(url=self.bot_thumbnail_url())
        return e

    # ── Response utilities ─────────────────────────────────────

    @staticmethod
    def _filter_kwargs(content, embed, view):
        kwargs = {}
        if content is not None:
            kwargs["content"] = content
        if embed is not None:
            kwargs["embed"] = embed
        if view is not None:
            kwargs["view"] = view
        return kwargs

    async def reply(
        self,
        target: Union[commands.Context, discord.Interaction],
        content: str | None = None,
        embed: discord.Embed | None = None,
        view: discord.ui.View | None = None,
        ephemeral: bool = False,
    ) -> discord.Message | None:
        kwargs = self._filter_kwargs(content, embed, view)

        if isinstance(target, discord.Interaction):
            if target.response.is_done():
                return await target.followup.send(**kwargs, ephemeral=ephemeral)
            await target.response.send_message(**kwargs, ephemeral=ephemeral)
            return await target.original_response()

        return await target.send(**kwargs)

    async def edit(
        self,
        target: Union[commands.Context, discord.Interaction, discord.Message],
        content: str | None = None,
        embed: discord.Embed | None = None,
        view: discord.ui.View | None = None,
    ) -> None:
        kwargs = self._filter_kwargs(content, embed, view)

        if isinstance(target, discord.Interaction):
            await target.edit_original_response(**kwargs)
        elif isinstance(target, discord.Message):
            await target.edit(**kwargs)

    # ── Error handling ─────────────────────────────────────────

    async def send_permission_error(
        self,
        target: Union[commands.Context, discord.Interaction],
        user: Union[discord.User, discord.Member],
        command_name: str = "",
    ) -> None:
        msg = "❌ You need Administrator permission to use this command."
        if isinstance(target, discord.Interaction):
            await target.response.send_message(msg, ephemeral=True)
        else:
            await target.send(msg)
        self.logger.warning(
            f"⚠️ {user} tried to use admin command{' (' + command_name + ')' if command_name else ''} without permission"
        )

    @staticmethod
    def prefix_command_error(error: Exception) -> str | None:
        if isinstance(error, commands.MissingPermissions):
            return "❌ You need Administrator permission to use this command."
        if isinstance(error, commands.MissingRequiredArgument):
            return "❌ Please provide all required information."
        return None

    @staticmethod
    def slash_command_error(error: Exception) -> str | None:
        if isinstance(error, app_commands.MissingPermissions):
            return "❌ You need Administrator permission to use this command."
        return None

    # ── Chunking helper ────────────────────────────────────────

    @staticmethod
    def chunk_text(text: str, limit: int = Config.CHUNK_SIZE) -> list[str]:
        return [text[i : i + limit] for i in range(0, len(text), limit)]
