# app/main.py
from fastapi import FastAPI
from .ws_stream import router as ws_router
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="AI Tutor - Teaching Assistant by Aman")
app.include_router(ws_router)

@app.get("/health")
async def health():
    return {"status": "ok"}
