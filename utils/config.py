import asyncio
import json
import logging
import os
import uuid


# TODO: Logの実装
logger = logging.getLogger("forest.config")


class Config:
    def __init__(self, config_name: str):
        self.name = config_name
        self.filepath = f"config/{self.name}.json"
        self.loop = asyncio.get_event_loop()
        self.lock = asyncio.Lock()
        self.load_from_file(create=True)

    async def load(self, *, create=False):
        async with self.lock:
            self.loop.run_in_executor(None, self.load_from_file, create=create)

    def load_from_file(self, *, create=False):
        if create and not os.path.exists(self.filepath):
            self.data = {}
            self._dump()

        with open(self.filepath, mode="r", encoding="utf-8") as f:
            self.data = json.load(f)

    def _dump(self):
        temp = "%s-%s.tmp" % (uuid.uuid4(), self.name)
        with open(temp, "w", encoding="utf-8") as tmp:
            json.dump(self.data.copy(), tmp, ensure_ascii=True, indent=4)

        os.replace(temp, self.filepath)

    async def save(self):
        async with self.lock:
            await self.loop.run_in_executor(None, self._dump)

    def get(self, key, *, default=None):
        return self.data.get(key, default)

    def __getitem__(self, key):
        if self.data is None:
            raise Exception(
                "The load method must be called first if access to configuration data."
            )
        return self.data.__getitem__(key)

    def __setitem__(self, key, value):
        if self.data is None:
            raise Exception(
                "The load method must be called first if access to configuration data."
            )
        self.data.__setitem__(key, value)
