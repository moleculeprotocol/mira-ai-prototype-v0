from chainlit.utils import mount_chainlit
from fastapi import FastAPI
from fastapi.responses import FileResponse

app = FastAPI()


@app.get("/robots.txt")
async def robots():
    return FileResponse("public/robots.txt")


mount_chainlit(app=app, target="app.py", path="/")
