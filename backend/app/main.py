from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.router import api_router
from app.config import get_settings
from app.exceptions import AppError
from app.logging_config import configure_logging, get_logger

settings = get_settings()
configure_logging(debug=settings.debug)
logger = get_logger(__name__)


def _validate_startup_config() -> None:
    """Fail fast with a clear, actionable message rather than a confusing
    error the first time someone creates a database connection."""
    from cryptography.fernet import Fernet

    try:
        Fernet(settings.encryption_key.encode())
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(
            "ENCRYPTION_KEY in your .env file is not a valid Fernet key. Generate one with:\n"
            '  python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"\n'
            "and put the result in your .env file as ENCRYPTION_KEY=<the generated value>."
        ) from exc

    if not settings.groq_api_key:
        logger.warning(
            "No GROQ_API_KEY is set - chat requests will fail until you add one. "
            "Get a free key at https://console.groq.com/keys and set it in your .env file."
        )


_validate_startup_config()

app = FastAPI(title=settings.app_name, debug=settings.debug)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    # Only the safe, generic public_message ever reaches the client. The
    # full detail (which may include internals useful for debugging) is
    # logged server-side only.
    logger.warning("AppError on %s %s: %s", request.method, request.url.path, exc.log_detail)
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.public_message})


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "An unexpected error occurred."})


app.include_router(api_router)


@app.get("/")
def root():
    return {"name": settings.app_name, "status": "running"}
