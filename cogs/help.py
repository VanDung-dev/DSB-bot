import discord
from discord import app_commands
from discord.ext import commands

from cogs.base import BaseCog
from cogs.config import Config


class Help(BaseCog):
    """Cog providing help and information commands."""

    def __init__(self, bot: commands.Bot) -> None:
        super().__init__(bot)

    @commands.command(name="hello")
    async def hello(self, ctx: commands.Context) -> None:
        self.logger.info(f"{ctx.author} called !hello in {ctx.channel}")
        await ctx.send(
            f"Hello {ctx.author.mention}, I'm {Config.BOT_NAME}! Type `!help` to see available commands! 😄"
        )

    @app_commands.command(name="hello", description="Greet the bot")
    async def slash_hello(self, interaction: discord.Interaction) -> None:
        self.logger.info(f"{interaction.user} called /hello in {interaction.channel}")
        await interaction.response.send_message(
            f"Hello {interaction.user.mention}, I'm {Config.BOT_NAME}! Use `/help` to see available commands! 😄"
        )

    @staticmethod
    def help_embed() -> discord.Embed:
        embed = discord.Embed(
            title=f"📋 {Config.BOT_NAME} Commands",
            description=f"{Config.BOT_NAME} — your AI-powered assistant on Discord.",
            color=Config.EMBED_COLOR,
        )
        embed.add_field(
            name="❓ Question",
            value=(
                "`/question <message>` — Ask the AI anything\n"
                "`!question <message>` or `!q <message>` — Same via prefix"
            ),
            inline=False,
        )
        embed.add_field(
            name="ℹ️ General",
            value=(
                "`/hello` — Greet the bot\n"
                "`/help` — Show this message\n"
                "`/forget` — Clear your conversation memory"
            ),
            inline=False,
        )
        return embed

    @commands.command(name="help", aliases=["commands"])
    async def help_command(self, ctx: commands.Context) -> None:
        self.logger.info(f"{ctx.author} called !help in {ctx.channel}")
        embed = self.help_embed()
        await ctx.send(embed=embed)

    @app_commands.command(name="help", description="Show available commands")
    async def slash_help(self, interaction: discord.Interaction) -> None:
        self.logger.info(f"{interaction.user} called /help in {interaction.channel}")
        embed = self.help_embed()
        await interaction.response.send_message(embed=embed)
