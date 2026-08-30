import re

file_path = "backend/app/api/v1/endpoints/sleeper/users.py"
with open(file_path, "r") as f:
    content = f.read()

# Add schemas imports
schemas_import = """    CommissionerWorkspaceLeague,
    CommissionerWorkspaceResponse,
    CommissionerCutdownLeague,
    CommissionerCutdownActionRequest,
    CommissionerCutdownActionResponse,
"""
content = re.sub(r"    CommissionerWorkspaceLeague,\n    CommissionerWorkspaceResponse,", schemas_import.strip("\n"), content)

# Add service imports
service_import = """from app.services.commissioner.workspace import (
    get_commissioner_workspace,
    save_commissioner_dues,
    save_commissioner_note,
    save_commissioner_settings,
)
from app.services.commissioner.cutdowns import (
    get_commissioner_cutdown_violations,
    execute_cutdown_action,
)
"""
content = re.sub(r"from app.services.commissioner.workspace import \([\s\S]*?\)", service_import.strip("\n"), content)

# Add endpoints
endpoints = """
@router.get(
    "/commissioner/cutdowns",
    response_model=list[CommissionerCutdownLeague],
)
async def get_commissioner_cutdowns_endpoint(
    ctx: ContextDep,
):
    return await get_commissioner_cutdown_violations(ctx)

@router.post(
    "/commissioner/cutdowns/action",
    response_model=CommissionerCutdownActionResponse,
)
async def execute_commissioner_cutdowns_action_endpoint(
    body: CommissionerCutdownActionRequest,
    ctx: ContextDep,
):
    return await execute_cutdown_action(body, ctx)
"""

content += endpoints

with open(file_path, "w") as f:
    f.write(content)
