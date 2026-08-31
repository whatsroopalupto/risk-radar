"""FastAPI startup entrypoint."""
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from .db import init_db
from .logging_conf import configure_logging
from .api.routes import router
configure_logging(); app=FastAPI(title="Geopolitical Risk Radar",version="0.1.0")
app.add_middleware(CORSMiddleware,allow_origins=["http://localhost:8501","http://127.0.0.1:8501"],allow_methods=["*"],allow_headers=["*"])
@app.on_event("startup")
def startup()->None: init_db(); logging.getLogger(__name__).info("Phase 1 startup: heuristic fallback available")
@app.exception_handler(Exception)
async def errors(_:Request, exc:Exception)->JSONResponse: return JSONResponse(status_code=500,content={"error":{"message":"Internal server error","type":type(exc).__name__}})
app.include_router(router)
