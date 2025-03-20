from fastapi import FastAPI
import asyncio
from src.telegram.telegram_service import start_telegram_bot

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(start_telegram_bot())


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}