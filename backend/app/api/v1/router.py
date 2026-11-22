"""Router agregador da versão 1 da API."""

from fastapi import APIRouter

from app.api.v1.routes import (
    auth,
    catalog,
    categories,
    courses,
    lessons,
    me,
    purchases,
    users,
    webhooks,
)

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(me.router, prefix="/me", tags=["me"])
api_router.include_router(catalog.router, prefix="/catalog", tags=["catalog"])
api_router.include_router(categories.router, prefix="/categories", tags=["categories"])
api_router.include_router(courses.router, prefix="/courses", tags=["courses"])
api_router.include_router(lessons.router, prefix="/lessons", tags=["lessons"])
api_router.include_router(purchases.router, prefix="/purchases", tags=["purchases"])
api_router.include_router(webhooks.router, prefix="/webhooks", tags=["webhooks"])
