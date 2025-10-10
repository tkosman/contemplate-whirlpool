import sanic


app = sanic.Sanic("ContemplateWhirlpool")

@app.get("/")
async def hello_world(request):
    return sanic.response.text("Hello, World! v1.0.1")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=1234)