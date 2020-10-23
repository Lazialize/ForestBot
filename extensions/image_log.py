import datetime

from discord.ext import commands

class ImageLog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
            
        if message.guild.id != 408139758490091521:
            return

        if not message.attachments:
            return

        log_channel = message.guild.get_channel(617393066554425362)

        for attachment in message.attachments:
            file = await attachment.to_file()

            time = message.created_at.astimezone(datetime.timezone(datetime.timedelta(hours=+9)))
            time_stamp = datetime.datetime.strftime(time, '%Y-%m-%d %H:%M:%S')

            await log_channel.send(f"{message.author}から送信された画\n{message.channel.mention}\n{time_stamp}", file=file)


def setup(bot):
    bot.add_cog(ImageLog(bot))
