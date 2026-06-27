from fastapi import APIRouter, Depends

from app.core.context import Context
from app.schemas.bootstrap import BootstrapResponse
from app.api.deps import get_context
from app.services.bootstrap import bootstrap

router = APIRouter()

@router.get('', response_model=BootstrapResponse)
async def bootstrap_endpoint(
    ctx: Context = Depends(get_context),
):
    return await bootstrap(ctx)
