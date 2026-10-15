from fastapi import APIRouter

from app.api.v1 import auth, cases, documents, facts, health, reviews, webhooks

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(cases.router)
api_router.include_router(documents.router)
api_router.include_router(facts.router)
api_router.include_router(reviews.router)
api_router.include_router(webhooks.router)

