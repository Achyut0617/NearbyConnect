from fastapi import FastAPI

app = FastAPI(title="NearbyConnect API")


@app.get("/health")
def health():
    """Simple check that the server is alive. No logic yet."""
    return {"status": "ok"}
