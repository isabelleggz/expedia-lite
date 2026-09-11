from fastapi import FastAPI

from .api import router as api_router


app = FastAPI(title="Expedia Lite API")
app.include_router(api_router)


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Return the service health state."""
    return {"status": "ok"}
