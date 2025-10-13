import sanic
from prometheus_client import Counter, CollectorRegistry, generate_latest
from prometheus_client import CONTENT_TYPE_LATEST

app = sanic.Sanic("ContemplateWhirlpool")

hello_world_counter = Counter(
    'hello_world_requests_total',
    'Total number of requests to hello_world endpoint'
)

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


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=1234)
