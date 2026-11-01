from trailblazers.app import app
from trailblazers.settings import settings

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=settings.host, port=settings.port)
