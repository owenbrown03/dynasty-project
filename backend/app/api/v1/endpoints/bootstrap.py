from fastapi import APIRouter

from app.schemas.bootstrap import BootstrapResponse
from app.api.deps import ContextDep
from app.services.bootstrap import bootstrap

router = APIRouter()

@router.get('', response_model=BootstrapResponse)
async def bootstrap_endpoint(
    ctx: ContextDep,
):
    return await bootstrap(ctx)
