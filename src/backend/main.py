from fastapi import FastAPI

from .configs import logging_config
from .controllers.agent_controller import router as agent_router
from .controllers.auth_controller import router as auth_router
from .controllers.employee_controller import router as employee_router
from .controllers.ingestion_controller import router as ingestion_router
from .controllers.request_controller import router as request_router
from .controllers.retrieval_controller import router as retrieval_router

app = FastAPI()

app.include_router(auth_router)
app.include_router(ingestion_router)
app.include_router(retrieval_router)
app.include_router(agent_router)
app.include_router(employee_router)
app.include_router(request_router)


@app.get("/")
async def root():
    return {"message": "Welcome to the API"}
