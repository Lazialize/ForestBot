import asyncio
import logging
import uuid

from discord import Embed, TextChannel, Role
from discord.ext import commands

from forest_bot import ForestBot
from utils.config import Config


logger = logging.getLogger("forest.autorole")


IS_ENABLED = "is_enabled"
TEMPLATE_MSG = "template_message"
LOG_CHANNEL = "log_channel"
CONTENTS = "contents"
CHANNEL_ID = "channel_id"
ROLE_ID = "role_id"


class AutoRole(commands.Cog):
    def __init__(self, bot: ForestBot):
        self.bot = bot
        self.config = Config("autorole")
        logger.info("Cog 'AutoRole' is initialized.")

    async def cog_before_invoke(self, ctx):
        guild_id = str(ctx.guild.id)
        if self.config.get(guild_id) is not None:
            return

        params = {
            IS_ENABLED: False,
            TEMPLATE_MSG: None,
            LOG_CHANNEL: None,
            CONTENTS: {},
        }
        self.config[guild_id] = params

        await self.config.save()

    @commands.command(name="list")
    @commands.has_permissions(manage_guild=True)
    async def _list(self, ctx):
        embeds = []
        embed = Embed()
        count = 0

        for role in reversed(ctx.guild.roles):
            embed.add_field(name=role.name, value=f"ID: {role.id}", inline=False)
            count += 1

            if count >= 20:
                embeds.append(embed)
                embed = Embed()
                count = 0
        if count != 0:
            embeds.append(embed)

        for embed in embeds:
            await ctx.send(embed=embed)

    @commands.group()
    @commands.has_permissions(manage_guild=True)
    async def autorole(self, ctx):
        if ctx.invoked_subcommand is not None:
            return

        guild_id = str(ctx.guild.id)

        embeds = []
        embed = Embed()
        count = 0

        for k, v in self.config[guild_id][CONTENTS].items():
            channel_name = ctx.guild.get_channel(v[CHANNEL_ID]).name
            role_name = ctx.guild.get_role(v[ROLE_ID]).name
            embed.add_field(name=k, value=f"チャンネル: {channel_name}, 役職: {role_name}")
            count += 1

            if count >= 20:
                embeds.append(embed)
                embed = Embed()
                count = 0

        if count != 0:
            embeds.append(embed)

        for embed in embeds:
            await ctx.send(embed=embed)

    @autorole.command()
    @commands.has_permissions(manage_guild=True)
    async def enable(self, ctx, is_enabled: bool = None):
        guild_id = str(ctx.guild.id)
        if is_enabled is None:
            is_enabled = not self.config[guild_id][IS_ENABLED]

        str_is_enabled = "有効" if is_enabled else "無効"

        if self.config[guild_id][IS_ENABLED] is is_enabled:
            await ctx.send(f"自動役職付与機能は既に{str_is_enabled}です。")
            return

        self.config[guild_id][IS_ENABLED] = is_enabled
        await self.config.save()
        await ctx.send(f"自動役職機能を{str_is_enabled}にしました。")

    @autorole.command(name="setmsg")
    @commands.has_permissions(manage_guild=True)
    async def set_template_message(self, ctx):
        guild_id = str(ctx.guild.id)
        await ctx.send("設定したいテンプレートメッセージを入力してください。")

        def check(m):
            return ctx.author == m.author and ctx.channel == m.channel

        try:
            message = await self.bot.wait_for("message", check=check, timeout=60.0)

            self.config[guild_id][TEMPLATE_MSG] = message.content
            await self.config.save()
        except asyncio.TimeoutError:
            await ctx.send("テンプレートメッセージ入力期限が過ぎました。最初かrやりなおしてください。")
        except Exception:
            await ctx.send("テンプレートメッセージの設定に失敗しました。")
        else:
            await ctx.send("テンプレートメッセージを設定しました。")

    @autorole.command(name="setlog")
    @commands.has_permissions(manage_guild=True)
    async def set_log_channel(self, ctx, channel: TextChannel):
        guild_id = str(ctx.guild.id)
        try:
            self.config[guild_id][LOG_CHANNEL] = channel.id
            await self.config.save()
        except Exception:
            await ctx.send("通知チャンネルの設定に失敗しました。")
        else:
            await ctx.send(f"{channel.mention}を通知チャンネルに設定しました。")

    @autorole.command(name="add")
    @commands.has_permissions(manage_guild=True)
    async def add_role(self, ctx, channel: TextChannel, role: Role):
        guild_id = str(ctx.guild.id)
        for k, v in self.config[guild_id][CONTENTS].items():
            if v[CHANNEL_ID] == channel.id and v[ROLE_ID] == role.id:
                await ctx.send(f"その設定は既に存在します。ID: {k}")
                return

        settings_id = str(uuid.uuid4())
        setting_content = {CHANNEL_ID: channel.id, ROLE_ID: role.id}

        self.config[guild_id][CONTENTS][settings_id] = setting_content
        await self.config.save()
        await ctx.send(f"{channel.name}に{role.name}を設定しました。")

    @autorole.command(name="remove")
    @commands.has_permissions(manage_guild=True)
    async def remove_role(self, ctx, setting_id: str):
        guild_id = str(ctx.guild.id)

        if setting_id not in self.config[guild_id][CONTENTS].keys():
            await ctx.send("指定のIDを持つ設定は存在しません。")
            return

        del self.config[guild_id][setting_id]
        await self.config.save()
        await ctx.send("設定を削除しました。")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        guild = message.guild
        guild_id = str(guild.id)

        if self.config.get(guild_id) is None:
            return

        if not self.config[guild_id][IS_ENABLED]:
            return

        sender = message.author

        channel_id = message.channel.id
        roles = [
            guild.get_role(i[ROLE_ID])
            for i in self.config[guild_id][CONTENTS].values()
            if i[CHANNEL_ID] == channel_id
            and i[ROLE_ID] not in [r.id for r in sender.roles]
        ]

        if len(roles) <= 0:
            return

        await sender.add_roles(*roles)

        if self.config[guild_id][LOG_CHANNEL] is None:
            return
        await guild.get_channel(self.config[guild_id][LOG_CHANNEL]).send(
            f"{sender.mention}さんに{', '.join(r.name for r in roles)}を付与しました。"
        )


def setup(bot: ForestBot):
    bot.add_cog(AutoRole(bot))
