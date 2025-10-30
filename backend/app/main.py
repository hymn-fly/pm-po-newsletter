from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from .click_tracker import ClickTracker
from .config import get_settings
from .schemas import AdvancedOptInRequest, ClickEvent, SubscriptionResponse, SubscriptionCreate
from .services import SubscriptionService
from .supabase_client import get_supabase_client

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    if not hasattr(app.state, "click_tracker"):
        supabase_client = get_supabase_client()
        app.state.click_tracker = ClickTracker(supabase_client)
    yield
    # Shutdown (필요한 경우 여기에 정리 코드 추가)


app = FastAPI(title="PM Letter Subscription API", lifespan=lifespan)

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


def get_click_tracker(request: Request) -> ClickTracker:
    tracker: ClickTracker | None = getattr(request.app.state, "click_tracker", None)
    if tracker is None:
        raise HTTPException(status_code=500, detail="Click tracker is not initialized.")
    return tracker


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


@app.post("/track-click", status_code=204)
def track_click(
    event: ClickEvent,
    tracker: ClickTracker = Depends(get_click_tracker),
) -> Response:
    try:
        tracker.increment(event.href)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    return Response(status_code=204)
