from fastapi import FastAPI

from kairos import __version__
from kairos.inventory import router as inventory_router

app = FastAPI(title="Kairos", version=__version__)
app.include_router(inventory_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "version": __version__}
