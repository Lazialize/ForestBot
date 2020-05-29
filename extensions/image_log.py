from discord.ext import commands

class ImageLog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.guild.id != 408139758490091521:
            return

        if not message.attachments:
            return

        log_channel = message.guild.get_channel(617393066554425362)

        for attachment in message.attachments:
            file = await attachment.to_file()

            await log_channel.send(f"{message.author}から送信された画像", file=file)


def setup(bot):
    bot.add_cog(ImageLog(bot))
