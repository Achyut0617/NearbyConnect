from fastapi import FastAPI

from routers import location

app = FastAPI(title="NearbyConnect API")
app.include_router(location.router)


@app.get("/health")
def health():
    """Simple check that the server is alive. No logic yet."""
    return {"status": "ok"}
