from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from starlette.responses import JSONResponse


def create_application() -> FastAPI:
    app = FastAPI(
        title="Movie App",
        version="1.0.0",
        debug=True,
    )
    
    @app.exception_handler(RateLimitExceeded)
    async def _rate_limit_exceeded_handler(request, exc: RateLimitExceeded):
        return JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded. Try again later."},
            headers={"Retry-After": "60"},
        )

    app.add_middleware(SlowAPIMiddleware)
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins="",
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["X-Total-Count", "X-API-Version", "Retry-After"],
    )

    @app.get("/health", tags=["Health"])
    async def health_check() -> dict[str, str]:
        return {"status": "Server is running smoothly!"}

        
    return app

app = create_application()