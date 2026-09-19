from fastapi import FastAPI
from sqlalchemy import text

from app.database.connection import engine

from fastapi.middleware.cors import CORSMiddleware

from app.routers.auth import router as auth_router
from app.routers.artists import router as artists_router
from app.routers.composers import router as composers_router
from app.routers.songs import router as songs_router
from app.routers.rhythms import router as rhythms_router
from app.routers.maqamat import router as maqamat_router
from app.routers.ajnas import router as ajnas_router
from app.routers.semantic import router as semantic_router
from app.routers.song_sources import router as song_sources_router
from app.routers.assistant import router as assistant_router



app = FastAPI(
    title="Nagham AI API"
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth_router)
app.include_router(artists_router)
app.include_router(composers_router)
app.include_router(songs_router)
app.include_router(rhythms_router)
app.include_router(maqamat_router)
app.include_router(ajnas_router)
app.include_router(song_sources_router)
app.include_router(semantic_router)
app.include_router(assistant_router)



@app.get("/")
def root():
    return {
        "message": "Nagham AI API is running"
    }


@app.get("/db-test")
def db_test():
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))

    return {
        "message": "Database connection successful"
    }