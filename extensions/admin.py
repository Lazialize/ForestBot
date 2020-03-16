import subprocess

from discord.ext import commands
from discord.ext.commands import Context

from forest_bot import ForestBot


class Admin(commands.Cog):
    def __init__(self, bot: ForestBot):
        self.bot = bot

    async def cog_check(self, ctx: Context):
        return await self.bot.is_owner(ctx.author)

    @commands.command(name="load")
    async def _load(self, ctx, extension):
        try:
            self.bot.load_extension(extension)
        except Exception:
            pass

    @commands.command(name="unload")
    async def _unload(self, ctx, extension):
        try:
            self.bot.unload_extension(extension)
        except Exception:
            pass

    @commands.command(name="reload")
    async def _reload(self, ctx, extension):
        try:
            self.bot.reload_extension(extension)
        except Exception:
            pass

    @commands.command()
    async def update(self, ctx):
        # ファイルの更新
        cmd = ["git", "pull", "origin", "master"]
        subprocess.call(cmd)

        cmd = ["python", "launcher.py"]
        subprocess.call(cmd)

        await self.shutdown.invoke()

    @commands.command()
    async def shutdown(self, ctx):
        await self.bot.logout()


def setup(bot: ForestBot):
    bot.add_cog(Admin(bot))
