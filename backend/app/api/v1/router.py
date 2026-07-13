from fastapi import APIRouter

from app.api.v1.routes import auth, charts, connections, history, sql

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(connections.router)
api_router.include_router(sql.router)
api_router.include_router(history.router)
api_router.include_router(charts.router)
