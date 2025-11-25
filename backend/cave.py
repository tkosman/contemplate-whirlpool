
import asyncio
from contextlib import asynccontextmanager
import random

from sanic import Websocket
from Thinker import Thinker
from thinkers.thinker_wikipedia import WikipediaThinker
from thinkers.thinker_nyt import NYTThinker
from thinkers.thinker_reddit import RedditThinker
from thinkers.thinker_guardian import GuardianThinker
from thinkers.thinker_google import GoogleSearchThinker


class Cave:
    def __init__(self):
        self.wcs: list[Websocket] = []
        self.thinkers: list[Thinker] = []
        self.shared_thought = "stake"
        self.lock = asyncio.Lock()

    def add_thinker(self, thinker: Thinker):
        self.thinkers.append(thinker)

    async def run_thinker(self, thinker: Thinker):
        while True:
            async with self.lock:
                self.shared_thought = await thinker.think(thought = self.shared_thought)
                print(f"{thinker.get_name()}: {self.shared_thought}")
            await asyncio.sleep(random.uniform(1, 3))

    async def contemplate(self):
        await asyncio.gather(*(self.run_thinker(thinker) for thinker in self.thinkers))

    @asynccontextmanager
    async def get_thought(self):
        async with self.lock:
            yield self.shared_thought

if __name__ == "__main__":
    cave = Cave()
    cave.add_thinker(WikipediaThinker("WikipediaThinker"))
    cave.add_thinker(NYTThinker("NYTThinker"))
    cave.add_thinker(RedditThinker("RedditThinker"))
    cave.add_thinker(GuardianThinker("GuardianThinker"))
    cave.add_thinker(GoogleSearchThinker("GoogleSearchThinker"))
    asyncio.run(cave.contemplate())