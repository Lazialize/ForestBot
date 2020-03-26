import ast

from discord import Embed, TextChannel
from discord.ext import commands


class EmbedCreator(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def embed(self, ctx, dict_str: str, channel: TextChannel = None):
        embed_dict = ast.literal_eval(dict_str)
        embed = Embed.from_dict(embed_dict)

        if channel is None:
            await ctx.send(embed=embed)
            return

        await channel.send(embed=embed)


def setup(bot):
    bot.add_cog(EmbedCreator(bot))
