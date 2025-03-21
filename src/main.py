import logging
from fastapi import FastAPI
import asyncio
import time
import os
from src.telegram.telegram_service import start_telegram_bot

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(start_telegram_bot())
#     asyncio.create_task(cleanup_old_files())
#
# async def cleanup_old_files():
#     while True:
#         now = time.time()
#         for root, dirs, files in os.walk("content"):
#             for file in files:
#                 file_path = os.path.join(root, file)
#                 if os.path.isfile(file_path):
#                     file_age = now - os.path.getmtime(file_path)
#                     if file_age > 300:  # 5 min
#                         try:
#                             os.remove(file_path)
#                             logging.info(f"File {file_path} deleted by timeout (age {file_age:.0f} seconds).")
#                         except Exception as e:
#                             logging.error(f"Error delete file {file_path}: {e}")
#         await asyncio.sleep(60)
