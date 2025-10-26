from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .config import get_settings
from .schemas import AdvancedOptInRequest, SubscriptionResponse, SubscriptionCreate
from .services import SubscriptionService
from .supabase_client import get_supabase_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    settings = get_settings()
    if settings.allowed_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.allowed_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    yield
    # Shutdown (필요한 경우 여기에 정리 코드 추가)


app = FastAPI(title="PM Letter Subscription API")


def get_subscription_service() -> SubscriptionService:
    supabase_client = get_supabase_client()
    return SubscriptionService(supabase_client)


@app.post("/subscriptions", response_model=SubscriptionResponse, status_code=201)
def create_subscription(
    payload: SubscriptionCreate,
    service: SubscriptionService = Depends(get_subscription_service),
) -> SubscriptionResponse:
    try:
        subscription = service.create_subscription(payload)
    except HTTPException as exc:  # FastAPI re-raises
        raise exc

    return SubscriptionResponse(success=True, data=subscription)


@app.post("/subscriptions/advanced-opt-in", response_model=SubscriptionResponse, status_code=200)
def opt_in_advanced_subscription(
    payload: AdvancedOptInRequest,
    service: SubscriptionService = Depends(get_subscription_service),
) -> SubscriptionResponse:
    subscription = service.opt_in_advanced_content(payload)
    return SubscriptionResponse(success=True, data=subscription)


@app.get("/health", tags=["health"])
def health_check() -> dict[str, str]:
    return {"status": "ok"}
