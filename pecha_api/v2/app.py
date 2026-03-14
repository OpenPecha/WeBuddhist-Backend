from fastapi import FastAPI
from starlette import status
from fastapi.middleware.cors import CORSMiddleware

from pecha_api.v2 import collections_views

api_v2 = FastAPI(
    title="Pecha API v2",
    description="Pecha API v2 - Integrated with OpenPecha",
    root_path="/api/v2",
    redoc_url="/docs",
)

api_v2.include_router(collections_views.collections_v2_router)

api_v2.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@api_v2.get("/health", status_code=status.HTTP_204_NO_CONTENT)
async def get_health():
    return {'status': 'up'}
