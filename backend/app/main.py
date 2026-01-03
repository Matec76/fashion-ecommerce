from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError

from redis.asyncio import Redis
from fastapi_cache import FastAPICache
from fastapi_cache.coder import JsonCoder
from app.core.cache import SafeRedisBackend

from app.core.config import settings
from app.core.db import init_db, close_db, check_db_connection

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.core.task import auto_complete_orders

from app.api.routes import (
    auth,
    payments,
    payment_methods,
    users,
    products,
    categories,
    attributes,
    cart,
    orders,
    wishlist,
    reviews,
    coupons,
    analytics,
    cms,
    notifications,
    inventory,
    loyalty,
    return_refunds,
    system,
    warehouse,
    chatbot,
)

if settings.SENTRY_DSN and settings.ENVIRONMENT != "local":
    import sentry_sdk
    sentry_sdk.init(
        dsn=str(settings.SENTRY_DSN),
        environment=settings.ENVIRONMENT,
        traces_sample_rate=1.0 if settings.ENVIRONMENT == "development" else 0.1,
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"Starting {settings.PROJECT_NAME} v{settings.VERSION}")
    print(f"Environment: {settings.ENVIRONMENT}")
    
    print("Checking database connection")
    if not await check_db_connection():
        print("ERROR: Database connection failed!")
        raise RuntimeError("Cannot start application without database")
    print("Database connection successful")

    print("Initializing FastAPI Cache (Redis)")
    redis_client = None
    try:
        redis_client = Redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=False,
            max_connections=20,
            socket_connect_timeout=5,
            socket_keepalive=True,
            retry_on_timeout=True,
        )
        
        await redis_client.ping()
        
        app.state.redis = redis_client
        
        FastAPICache.init(
            SafeRedisBackend(redis_client),
            prefix="fashion-cache:",
            coder=JsonCoder 
        )
        
        print("FastAPI Cache initialized successfully")
        print(f"Redis: {settings.REDIS_HOST}:{settings.REDIS_PORT}")
        print(f"Prefix: fashion-cache:")
        print(f"Coder: JsonCoder (human-readable)")
        print(f"decode_responses: False (JsonCoder handles decoding)")
        
    except Exception as e:
        print(f"WARNING: Cannot connect to Redis - {e}")
        print("Cache is disabled (application will continue without cache)")
        app.state.redis = None
    
    print("Initializing database tables")
    await init_db()
    print("Database tables created")

    print("Initializing System Scheduler")
    scheduler = AsyncIOScheduler()
    
    scheduler.add_job(
        auto_complete_orders, 
        'cron', 
        hour=0, 
        minute=0, 
        id='auto_complete_orders_job'
    )
    
    scheduler.start()
    print("System Scheduler started (Auto-complete orders at 00:00)")
    
    if settings.all_cors_origins:
        print("\CORS enabled for origins:")
        for origin in settings.all_cors_origins:
            print(f"   - {origin}")
    
    print("Application started successfully")
    print(f"API Docs: {settings.BACKEND_URL}{settings.API_V1_STR}/docs")
    print(f"ReDoc: {settings.BACKEND_URL}{settings.API_V1_STR}/redoc")
    print(f"DataBase: {settings.DATABASE_URL}")
    print(f"Health Check: {settings.BACKEND_URL}/health")
    
    yield
    
    print("Shutting down application")

    print("Stopping System Scheduler...")
    scheduler.shutdown()
    
    print("Closing database connections")
    await close_db()
    print("Database closed")
    
    if app.state.redis:
        print("Closing Redis connection")
        try:
            await app.state.redis.aclose()
            print("Redis connection closed")
        except Exception as e:
            print(f"Error closing Redis: {e}")
    
    print("Application shutdown complete")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=settings.DESCRIPTION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    lifespan=lifespan,
)


app.add_middleware(GZipMiddleware, minimum_size=1000)

if settings.all_cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.all_cors_origins],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Total-Count", "X-Page", "X-Page-Size"],
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError
) -> JSONResponse:
    errors = []
    for error in exc.errors():
        errors.append({
            "loc": error["loc"],
            "msg": error["msg"],
            "type": error["type"],
        })
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": errors,
            "message": "Loi xac thuc du lieu"
        },
    )


@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(
    request: Request,
    exc: SQLAlchemyError
) -> JSONResponse:
    print(f"Database error: {exc}")
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Loi database xay ra",
            "message": "Da xay ra loi khi xu ly yeu cau cua ban"
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(
    request: Request,
    exc: Exception
) -> JSONResponse:
    print(f"Unhandled error: {exc}")
    
    if settings.SENTRY_DSN and settings.ENVIRONMENT != "local":
        import sentry_sdk
        sentry_sdk.capture_exception(exc)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": str(exc) if settings.ENVIRONMENT == "local" else "Loi server noi bo",
            "message": "Da xay ra loi khong mong muon"
        },
    )


@app.get("/health", tags=["Health"])
async def health(request: Request):
    
    db_healthy = await check_db_connection()
    
    redis_healthy = False
    redis_info = {
        "status": "disconnected",
        "type": "Redis Cloud (FastAPI-Cache2)",
        "coder": "JsonCoder",
    }
    
    try:
        if request.app.state.redis:
            await request.app.state.redis.ping()
            redis_healthy = True
            redis_info["status"] = "connected"
            redis_info["host"] = settings.REDIS_HOST
            redis_info["port"] = settings.REDIS_PORT
    except Exception as e:
        redis_info["error"] = str(e)
    
    overall_status = "healthy" if (db_healthy and redis_healthy) else "degraded"
    
    return {
        "status": overall_status,
        "app": {
            "name": settings.PROJECT_NAME,
            "version": settings.VERSION,
            "environment": settings.ENVIRONMENT,
        },
        "database": {
            "status": "connected" if db_healthy else "disconnected"
        },
        "cache": redis_info
    }


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information"""
    return {
        "message": f"Chao mung den voi {settings.PROJECT_NAME} API",
        "version": settings.VERSION,
        "docs": f"{settings.API_V1_STR}/docs",
        "redoc": f"{settings.API_V1_STR}/redoc",
        "health": "/health",
        "environment": settings.ENVIRONMENT,
    }


app.include_router(
    auth.router,
    prefix=f"{settings.API_V1_STR}/auth",
    tags=["Authentication"]
)

app.include_router(
    users.router,
    prefix=f"{settings.API_V1_STR}/users",
    tags=["Users"]
)

app.include_router(
    products.router,
    prefix=f"{settings.API_V1_STR}/products",
    tags=["Products"]
)

app.include_router(
    categories.router,
    prefix=f"{settings.API_V1_STR}/categories",
    tags=["Categories"]
)

app.include_router(
    attributes.router,
    prefix=f"{settings.API_V1_STR}/attributes",
    tags=["Attributes"]
)

app.include_router(
    cart.router,
    prefix=f"{settings.API_V1_STR}/cart",
    tags=["Cart"]
)

app.include_router(
    orders.router,
    prefix=f"{settings.API_V1_STR}/orders",
    tags=["Orders"]
)

app.include_router(
    wishlist.router,
    prefix=f"{settings.API_V1_STR}/wishlist",
    tags=["Wishlist"]
)

app.include_router(
    reviews.router,
    prefix=f"{settings.API_V1_STR}/reviews",
    tags=["Reviews"]
)

app.include_router(
    coupons.router,
    prefix=f"{settings.API_V1_STR}/coupons",
    tags=["Coupons"]
)

app.include_router(
    payments.router,
    prefix=f"{settings.API_V1_STR}/payment",
    tags=["Payment"]
)

app.include_router(
    payment_methods.router,
    prefix=f"{settings.API_V1_STR}/payment_methods",
    tags=["Payment Methods"]
)

app.include_router(
    analytics.router,
    prefix=f"{settings.API_V1_STR}/analytics",
    tags=["Analytics"]
)

app.include_router(
    cms.router,
    prefix=f"{settings.API_V1_STR}/cms",
    tags=["CMS"]
)

app.include_router(
    notifications.router,
    prefix=f"{settings.API_V1_STR}/notifications",
    tags=["Notifications"]
)

app.include_router(
    inventory.router,
    prefix=f"{settings.API_V1_STR}/inventory",
    tags=["Inventory"]
)

app.include_router(
    loyalty.router,
    prefix=f"{settings.API_V1_STR}/loyalty",
    tags=["Loyalty"]
)

app.include_router(
    return_refunds.router,
    prefix=f"{settings.API_V1_STR}/return_refunds",
    tags=["Return Refunds"]
)

app.include_router(
    system.router,
    prefix=f"{settings.API_V1_STR}/system",
    tags=["System"]
)

app.include_router(
    warehouse.router,
    prefix=f"{settings.API_V1_STR}/warehouse",
    tags=["Warehouse"]
)

app.include_router(
    chatbot.router,
    prefix=f"{settings.API_V1_STR}/chatbot",
    tags=["Chatbot AI"]
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    if settings.ENVIRONMENT == "local":
        print(f"{request.method} {request.url.path}")
    
    response = await call_next(request)
    
    return response


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )