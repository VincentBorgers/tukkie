from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .api.routes import router
from .bootstrap import ROOT_DIR
from vha_config import AppSettings
from .services.runtime import build_runtime


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.runtime = build_runtime()
    yield


app = FastAPI(
    title="Tukkie",
    version="1.0.0",
    summary="Open-source, privacygerichte home intelligence stack in het Nederlands",
    lifespan=lifespan,
)

runtime_settings = AppSettings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=runtime_settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router)

dist_path = ROOT_DIR / "dashboard" / "dist"
if dist_path.exists():
    app.mount("/assets", StaticFiles(directory=dist_path / "assets"), name="dashboard-assets")


@app.get("/", include_in_schema=False)
async def root():
    index_path = dist_path / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return JSONResponse(
        {
            "message": f"{runtime_settings.app_name} API draait. Start het dashboard via npm run dev of bouw dashboard/dist.",
            "api": "/api/overview",
        }
    )


@app.get("/{full_path:path}", include_in_schema=False)
async def spa_fallback(full_path: str):
    candidate = dist_path / full_path
    if candidate.exists() and candidate.is_file():
        return FileResponse(candidate)
    index_path = dist_path / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return JSONResponse({"message": f"Pad '{full_path}' bestaat niet in de API of het dashboard."}, status_code=404)
