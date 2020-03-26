import uuid
import unicodedata

from discord import Role, Message, RawReactionActionEvent, Embed
from discord.ext import commands

from utils.config import Config


IS_ENABLED = "is_enabled"
CONTENTS = "contents"
CHANNEL_ID = "channel_id"
MESSAGE_ID = "message_id"
ROLE_ID = "role_id"
EMOJI = "emoji"


class ReactionRole(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config("reactionrole")

    async def cog_before_invoke(self, ctx):
        guild_id = str(ctx.guild.id)
        if self.config.get(guild_id) is not None:
            return

        params = {
            IS_ENABLED: False,
            CONTENTS: {},
        }
        self.config[guild_id] = params

        await self.config.save()

    @commands.group()
    async def reactionrole(self, ctx):
        if ctx.invoked_subcommand is not None:
            return

        guild_id = str(ctx.guild.id)

        embeds = []
        embed = Embed()
        count = 0

        for k, v in self.config[guild_id][CONTENTS].items():
            channel_name = ctx.guild.get_channel(v[CHANNEL_ID]).name
            role_name = ctx.guild.get_role(v[ROLE_ID]).name
            emoji = unicodedata.lookup(v[EMOJI])
            embed.add_field(
                name=k,
                value=f"チャンネル: {channel_name}, メッセージID: {v[MESSAGE_ID]}, 役職: {role_name}, Emoji: {emoji}",
            )
            count += 1

            if count >= 20:
                embeds.append(embed)
                embed = Embed()
                count = 0

        if count != 0:
            embeds.append(embed)

        for embed in embeds:
            await ctx.send(embed=embed)

    @reactionrole.command()
    async def enable(self, ctx, is_enabled: bool = None):
        guild_id = str(ctx.guild.id)
        if is_enabled is None:
            is_enabled = not self.config[guild_id][IS_ENABLED]

        str_is_enabled = "有効" if is_enabled else "無効"

        if self.config[guild_id][IS_ENABLED] is is_enabled:
            await ctx.send(f"リアクションロール機能は既に{str_is_enabled}です。")
            return

        self.config[guild_id][IS_ENABLED] = is_enabled
        await self.config.save()
        await ctx.send(f"リアクションロール機能を{str_is_enabled}にしました。")

    @reactionrole.command(name="add")
    async def add_reaction_role(self, ctx, message: Message, role: Role, emoji):
        guild_id = str(ctx.guild.id)
        for k, v in self.config[guild_id][CONTENTS].items():
            if (
                v[CHANNEL_ID] == message.channel.id
                and v[MESSAGE_ID] == message.id
                and v[EMOJI] == unicodedata.name(emoji)
            ):
                await ctx.send(f"その設定は既に存在するか、重複しています。ID: {k}")
                return

        settings_id = str(uuid.uuid4())
        setting_content = {
            CHANNEL_ID: message.channel.id,
            MESSAGE_ID: message.id,
            ROLE_ID: role.id,
            EMOJI: unicodedata.name(emoji),
        }

        self.config[guild_id][CONTENTS][settings_id] = setting_content
        await self.config.save()
        await message.add_reaction(emoji)
        await ctx.send(f"MessageID '{message.id}'に{role.name}-{emoji}を設定しました。")

    @reactionrole.command(name="remove")
    async def remove_reaction_role(self, ctx, setting_id):
        guild_id = str(ctx.guild.id)

        if setting_id not in self.config[guild_id][CONTENTS].keys():
            await ctx.send("指定のIDを持つ設定は存在しません。")
            return

        pop_item = self.config[guild_id][CONTENTS].pop(setting_id, None)
        if pop_item is None:
            return

        channel = ctx.guild.get_channel(pop_item[CHANNEL_ID])
        message = await channel.fetch_message(pop_item[MESSAGE_ID])
        await message.remove_reaction(
            unicodedata.lookup(pop_item[EMOJI]), self.bot.user
        )
        await self.config.save()
        await ctx.send("設定を削除しました。")

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: RawReactionActionEvent):
        guild = self.bot.get_guild(payload.guild_id)
        guild_id = str(guild.id)
        user = guild.get_member(payload.user_id)
        if user.bot:
            return
        if self.config.get(guild_id) is None:
            return
        if not self.config[guild_id][IS_ENABLED]:
            return

        role = None
        for v in self.config[guild_id][CONTENTS].values():
            if (
                v[CHANNEL_ID] != payload.channel_id
                or v[MESSAGE_ID] != payload.message_id
                or v[EMOJI] != unicodedata.name(payload.emoji.name)
            ):
                continue

            role = guild.get_role(v[ROLE_ID])
            break
        if role is None:
            return

        if role not in user.roles:
            await user.add_roles(role)
        else:
            await user.remove_roles(role)
        message = await guild.get_channel(payload.channel_id).fetch_message(
            payload.message_id
        )
        await message.remove_reaction(payload.emoji, user)


def setup(bot):
    bot.add_cog(ReactionRole(bot))
