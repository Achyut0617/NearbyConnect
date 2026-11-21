import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from db import create_tables
from routers import connect, location, people, profile, push_tokens, sharing


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_tables()  # make sure DB tables exist when the server starts
    yield


app = FastAPI(title="NearbyConnect API", lifespan=lifespan)

# CORS: lets the app's WEB version (browser) call this API. Phones don't need it.
# Login uses a header token, not cookies, so "*" is acceptable for development.
# For production, set CORS_ORIGINS to your real web address(es), comma separated.
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(location.router)
app.include_router(profile.router)
app.include_router(sharing.router)
app.include_router(people.router)
app.include_router(connect.router)
app.include_router(push_tokens.router)


@app.get("/health")
def health():
    """Simple check that the server is alive. No logic yet."""
    return {"status": "ok"}
