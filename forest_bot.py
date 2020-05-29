import logging

from discord.ext import commands


logger = logging.getLogger("forest")


INITIAL_EXTENSIONS = (
    "extensions.admin",
    "extensions.auto_kick",
    "extensions.auto_role",
    "extensions.image_log",
    "extensions.reaction_role",
    "extensions.embed_creator",
)


class ForestBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        logger.debug("Began to load extensions.")
        for ext in INITIAL_EXTENSIONS:
            try:
                self.load_extension(ext)
            except Exception:
                logger.warning(f"Failed to load an extension '{ext}'.", exc_info=True)
            else:
                logger.info(f"Succeeded to load an extension '{ext}'.")
        logger.debug("Ended to load extensions.")

        logger.info("Bot is initialized.")
