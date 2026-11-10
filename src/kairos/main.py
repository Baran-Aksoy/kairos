from fastapi import FastAPI

from kairos import __version__
from kairos.inventory import router as inventory_router
from kairos.web import router as web_router

app = FastAPI(title="Kairos", version=__version__)
app.include_router(inventory_router)
app.include_router(web_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "version": __version__}
