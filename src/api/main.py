from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.api.routers import analytics, system
from src.api.services import clear_data_store, load_data_to_store
from src.utils.logging_config import setup_logging

logger = setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    load_data_to_store()
    yield
    clear_data_store()


app = FastAPI(
    title="PAM Paraná Analytics API",
    description="API para exposição de dados históricos e clusterização de Soja, Milho e Trigo (2010-2024)",
    version="1.0.0",
    lifespan=lifespan,
)

# Acoplamento de rotas desacopladas (Routers)
app.include_router(system.router)
app.include_router(analytics.router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=["src/api", "src/features", "src/models", "src/utils"],
    )
