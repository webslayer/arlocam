from server.app import app
import uvicorn


if __name__ == "__main__":
    uvicorn.run("main:app", port=8000, workers=4)
