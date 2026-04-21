import asyncio
from sleeper import get_league

async def test():
    # Use one of your real League IDs here
    data = await get_league("1314405890798927872")
    print(f"Connection Successful! League Name: {data.get('name')}")

asyncio.run(test())