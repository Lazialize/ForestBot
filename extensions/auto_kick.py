from datetime import timedelta, datetime

from discord import Embed, TextChannel
from discord.ext import commands, tasks

from forest_bot import ForestBot
from utils.config import Config


IS_ENABLED = "is_enabled"
NOTIFY_CHANNEL = "notify_channel"
LIMIT_DAY = "limit_day"


class AutoKick(commands.Cog):
    def __init__(self, bot: ForestBot):
        self.bot = bot
        self.config = Config("autokick")
        self.auto_kick_task.start()

    def cog_unload(self):
        self.auto_kick_task.cancel()

    async def cog_before_invoke(self, ctx):
        guild_id = str(ctx.guild.id)
        if self.config.get(guild_id) is not None:
            return

        params = {IS_ENABLED: False, NOTIFY_CHANNEL: None, LIMIT_DAY: 7}
        self.config[guild_id] = params

        await self.config.save()

    @commands.group()
    @commands.has_permissions(manage_guild=True)
    async def autokick(self, ctx):
        if ctx.invoked_subcommand is not None:
            return
        guild_id = str(ctx.guild.id)

        is_enabled = self.config[guild_id][IS_ENABLED]
        notify_channel_id = self.config[guild_id][NOTIFY_CHANNEL]
        notify_channel = (
            None
            if notify_channel_id is None
            else ctx.guild.get_channel(notify_channel_id).mention
        )
        limit_days = self.config[guild_id][LIMIT_DAY]

        embed = Embed()
        embed.title = "自動キック機能の現在の設定"
        embed.add_field(
            name="機能の有効/無効", value="有効" if is_enabled else "無効", inline=False
        )
        embed.add_field(name="通知チャンネル", value=notify_channel, inline=False)
        embed.add_field(name="制限日数", value=limit_days, inline=False)

        await ctx.send(embed=embed)

    @autokick.command(name="setlog")
    @commands.has_permissions(manage_guild=True)
    async def set_log_channel(self, ctx, channel: TextChannel):
        try:
            self.config[str(ctx.guild.id)][NOTIFY_CHANNEL] = channel.id
            await self.config.save()
        except Exception:
            await ctx.send("通知チャンネルの設定に失敗しました。")
        else:
            await ctx.send(f"{channel.mention}を通知チャンネルに設定しました。")

    @autokick.command(name="setlimit")
    @commands.has_permissions(manage_guild=True)
    async def set_limit_days(self, ctx, limit_days):
        try:
            self.config[str(ctx.guild.id)][LIMIT_DAY] = limit_days
            await self.config.save()
        except Exception:
            await ctx.send("制限日数の設定に失敗しました。")
        else:
            await ctx.send(f"制限日数を{limit_days}に設定しました。")

    @autokick.command()
    @commands.has_permissions(manage_guild=True)
    async def enable(self, ctx, is_enabled=None):
        guild_id = str(ctx.guild.id)
        if is_enabled is None:
            is_enabled = not self.config[guild_id][IS_ENABLED]

        str_is_enabled = "有効" if is_enabled else "無効"

        if self.config[guild_id][IS_ENABLED] is is_enabled:
            await ctx.send(f"自動キックの機能は既に{str_is_enabled}です。")
            return

        self.config[guild_id][IS_ENABLED] = is_enabled
        await self.config.save()
        await ctx.send(f"自動キック機能を{str_is_enabled}にしました。")

    @tasks.loop(hours=24)
    async def auto_kick_task(self):
        for guild in self.bot.guilds:
            guild_id = str(guild.id)
            if guild_id not in self.config:
                continue

            if not self.config[guild_id][IS_ENABLED]:
                continue

            notify_channel = guild.get_channel(self.config[guild_id][NOTIFY_CHANNEL])
            role = guild.get_role(690207601635491890)
            role_2 = guild.get_role(436246853713920010)

            if role is None:
                continue

            for member in guild.members:
                if role in member.roles:
                    continue

                if role_2 in member.roles:
                    continue

                limit_date = (
                    member.joined_at + timedelta(days=self.config[guild_id][LIMIT_DAY])
                ).date()

                if datetime.today().date() < limit_date:
                    continue

                await member.kick(
                    reason=f"{self.config[guild_id][LIMIT_DAY]}日以上プロフィールの記入がないため。"
                )
                await notify_channel.send(
                    f"長期間プロフィールの記入がなかったため、{member.name}さんをキックしました。"
                )


def setup(bot: ForestBot):
    bot.add_cog(AutoKick(bot))
