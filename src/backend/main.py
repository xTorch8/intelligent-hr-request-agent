
from fastapi import FastAPI
from .configs import logging_config
from .controllers.ingestion_controller import router as ingestion_router

app = FastAPI()

app.include_router(ingestion_router)

@app.get("/")
async def root():
    return {"message": "Welcome to the API"}
