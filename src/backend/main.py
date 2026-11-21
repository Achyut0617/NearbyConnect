from contextlib import asynccontextmanager

from fastapi import FastAPI

from db import create_tables
from routers import connect, location, people, profile, sharing


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_tables()  # make sure DB tables exist when the server starts
    yield


app = FastAPI(title="NearbyConnect API", lifespan=lifespan)
app.include_router(location.router)
app.include_router(profile.router)
app.include_router(sharing.router)
app.include_router(people.router)
app.include_router(connect.router)


@app.get("/health")
def health():
    """Simple check that the server is alive. No logic yet."""
    return {"status": "ok"}
