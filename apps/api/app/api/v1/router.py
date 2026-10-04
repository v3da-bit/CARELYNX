from fastapi import APIRouter

from app.api.v1 import cases, documents, health, facts

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(cases.router)
api_router.include_router(documents.router)
api_router.include_router(facts.router)
