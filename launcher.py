import asyncio
import logging
import os

from utils.config import Config
from utils.constants import API_TOKEN_KEY
from forest_bot import ForestBot

fmt = "[%(asctime)s][%(levelname)s]%(name)s: %(message)s"
logging.basicConfig(level=logging.INFO, format=fmt, filename="./forest.log")
logging.getLogger("discord").setLevel(logging.WARNING)
logger = logging.getLogger("forest.launcher")


def load_config():
    # 設定ファイルの読み込みを行う。ファイルが存在しない場合は終了する。
    config = Config("bot")

    # 設定データにAPIキーがあるかを確認し、存在しなければ環境変数の値を取得する。
    if config.get(API_TOKEN_KEY) is None:
        logger.warning("Bot token does not exist in config data.")
        env_var = os.environ.get(API_TOKEN_KEY)
        if env_var is None:
            logger.error("Bot token does not exist also in environment variables")
            exit(1)

        config[API_TOKEN_KEY] = env_var

    return config


async def run_bot():
    config = load_config()
    bot = ForestBot("f!")
    try:
        await bot.start(config[API_TOKEN_KEY])
    except KeyboardInterrupt:
        logger.warn("KeyboardInterrupted: Logout bot")
        await bot.logout()


def main():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run_bot())
    loop.close()


if __name__ == "__main__":
    main()
