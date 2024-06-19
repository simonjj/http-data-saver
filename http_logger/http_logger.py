from fastapi import FastAPI, Request
from starlette.responses import Response
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"])
async def catch_all(request: Request, path: str):
    body = await request.body()
    logger.info(f"Path: {path}\nHeaders: {request.headers}, \nBody: {body}")
    return Response("OK")