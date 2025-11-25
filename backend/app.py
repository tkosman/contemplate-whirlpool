import sanic
import asyncio
from sanic.log import logger
from prometheus_client import Counter, CollectorRegistry, generate_latest
from prometheus_client import CONTENT_TYPE_LATEST
from sanic import Request, Websocket

from cave import Cave, Thinker, WikipediaThinker, NYTThinker, RedditThinker, GuardianThinker, GoogleSearchThinker, LOCThinker


app = sanic.Sanic("ContemplateWhirlpool")

# Enable CORS
app.config.CORS_ORIGINS = "*"

hello_world_counter = Counter(
    'hello_world_requests_total',
    'Total number of requests to hello_world endpoint'
)

@app.before_server_start
async def setup_cave(app, loop):
    app.ctx.cave = Cave()
    app.ctx.cave.add_thinker(WikipediaThinker("WikipediaThinker"))
    app.ctx.cave.add_thinker(LOCThinker("LOCThinker"))
    app.add_task(app.ctx.cave.contemplate())


@app.get("/")
async def hello_world(request):
    hello_world_counter.inc()
    return sanic.response.text("Hello, World! v1.0.2")


@app.get("/prometheus")
async def prometheus_metrics(request):
    registry = CollectorRegistry()
    registry.register(hello_world_counter)

    return sanic.response.raw(
        generate_latest(registry),
        content_type=CONTENT_TYPE_LATEST
    )


@app.websocket("/ws")
async def feed(request: Request, ws: Websocket):
    try:
        app.ctx.cave.wcs.append(ws)
        last_thought = ""
        while True:
            async with app.ctx.cave.get_thought() as thought:
                if thought != last_thought:
                    await ws.send(thought)
                    last_thought = thought
            await asyncio.sleep(0.5)
    except Exception:
        logger.warning(f"WebSocket error with: {ws}")
    finally:
        logger.info(f"WebSocket disconnected: {ws}")
        app.ctx.cave.wcs.remove(ws)



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=1234)
