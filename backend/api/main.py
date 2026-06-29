from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.api.auth import router as auth_router
from backend.api.orders import router as orders_router
from backend.api.approval import router as approval_router
from backend.api.products import router as products_router
from backend.api.batch_orders import router as batch_router
from backend.api.management import router as management_router
from backend.api.admin import router as admin_router
from backend.core.logger import get_logger
from backend.schemas.response import StandardResponse
from backend.utils.exceptions import AppError
from backend.database.connection import init_pool, close_pool

logger = get_logger("main")


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_pool(minconn=2, maxconn=20)
    logger.info("Manual Production Order API started")
    yield
    close_pool()
    logger.info("Manual Production Order API stopped")


app = FastAPI(
    title="Manual Production Order API",
    version="3.0.0",
    description="Bull Machines — Manual Production Order Management System",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(orders_router)
app.include_router(approval_router)
app.include_router(products_router)
app.include_router(batch_router)
app.include_router(management_router)
app.include_router(admin_router)


@app.exception_handler(AppError)
async def app_error_handler(_: Request, exc: AppError):
    return JSONResponse(
        status_code=exc.status_code,
        content=StandardResponse(success=False, message=exc.message).model_dump(),
    )


@app.exception_handler(Exception)
async def unhandled_error_handler(_: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content=StandardResponse(success=False, message="An unexpected error occurred").model_dump(),
    )


@app.get("/health")
def health():
    return {"status": "ok", "version": "3.0.0"}
