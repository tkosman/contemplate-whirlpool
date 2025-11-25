
import asyncio
from contextlib import asynccontextmanager
import json
import random

from sanic import Websocket
from thinker import Thinker
from thinkers.thinker_wikipedia import WikipediaThinker
from thinkers.thinker_loc import LOCThinker


class Cave:
    def __init__(self):
        self.wcs: list[Websocket] = []
        self.thinkers: list[Thinker] = []
        self.shared_thought = "stake"
        self.shared_message = ""
        self.lock = asyncio.Lock()

    def add_thinker(self, thinker: Thinker):
        self.thinkers.append(thinker)

    async def run_thinker(self, thinker: Thinker):
        while True:
            async with self.lock:
                self.shared_thought = await thinker.think(thought = self.shared_thought)
                self.shared_message = json.dumps({
                    "thinker": thinker.get_name(),
                    "thought": self.shared_thought
                })
            await asyncio.sleep(random.uniform(1, 3))

    async def contemplate(self):
        await asyncio.gather(*(self.run_thinker(thinker) for thinker in self.thinkers))

    @asynccontextmanager
    async def get_thought(self):
        async with self.lock:
            yield self.shared_message

if __name__ == "__main__":
    cave = Cave()
    cave.add_thinker(WikipediaThinker("WikipediaThinker"))
    cave.add_thinker(LOCThinker("LOCThinker"))
    asyncio.run(cave.contemplate())