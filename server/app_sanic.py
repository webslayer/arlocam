from sanic import Sanic
from sanic import response
import time
import asyncio

app = Sanic(__name__)


@app.route("/")
async def test(request):
    while True:
        await asyncio.sleep(10)
        print("10s elapsed")

    return await response.json({"test": True})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
