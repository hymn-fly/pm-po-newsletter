from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .schemas import SubscriptionResponse, SubscriptionCreate
from .services import SubscriptionService
from .supabase_client import get_supabase_client


app = FastAPI(title="PM Letter Subscription API")


@app.on_event("startup")
def configure_cors() -> None:
    settings = get_settings()
    if settings.allowed_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.allowed_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )


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


@app.get("/health", tags=["health"])
def health_check() -> dict[str, str]:
    return {"status": "ok"}
