import logging, asyncio, httpx
from typing import Optional

logger = logging.getLogger(__name__)

MAX_CONCURRENT_REQUESTS = 20
limit = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)

client: httpx.AsyncClient = None
error_count = 0

async def open_client():
    global client
    if client is None:
        client = httpx.AsyncClient(timeout=10.0)
        logger.info("Sleeper API client initialized.")

async def close_client():
    global client
    if client:
        await client.aclose()
        client = None

async def fetch_sleeper(endpoint: str, retries: int = 3) -> Optional[dict]:
    global error_count
    
    if client is None:
        logger.warning("Emergency lazy-init of Sleeper client.")
        await open_client()

    url = f"https://api.sleeper.app/v1/{endpoint}"

    async with limit:
        if error_count > 50:
            logger.critical("Circuit breaker tripped: error count exceeded 50!")
            raise RuntimeError("Error count exceeded!")

        for attempt in range(retries):
            try:
                response = await client.get(url)
                
                # Handle Explicit Missing/Bad Input States Cleanly
                if response.status_code == 404:
                    logger.warning(f"Resource not found (404) for: {endpoint}")
                    return None
                if response.status_code == 400:
                    logger.error(f"Bad Request (400) for: {endpoint}. Check parameters.")
                    return None
                
                # Handle Rate Limiting
                if response.status_code == 429:
                    error_count += 5 
                    logger.warning(f"Rate limited (429) by Sleeper on {endpoint}. Cooling down 10s...")
                    await asyncio.sleep(10)
                    continue 

                # Throw an exception for any other bad status (500s, etc) to trigger the retry loop
                response.raise_for_status()
                
                # If we made it here, it's a 200 OK success
                if error_count > 0:
                    error_count -= 1 
                return response.json()

            except (httpx.HTTPStatusError, httpx.RequestError) as e:
                error_count += 1
                
                # Check if it was a server status error vs network timeout
                status_code = e.response.status_code if isinstance(e, httpx.HTTPStatusError) else None

                # Backoff Retry Logic
                if attempt < retries - 1:
                    wait_time = (2 ** attempt) + 1
                    error_type = "Timeout/Connection" if status_code is None else f"Server Error ({status_code})"
                    logger.warning(f"Sleeper {error_type} for {endpoint}. Retry {attempt+1}/{retries} in {wait_time}s.")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"Final catastrophic failure for {endpoint} after {retries} attempts: {e}")
                    raise e

# General
async def get_NFL_state():
    return await fetch_sleeper(f"state/nfl")

# User
async def get_username_details(username):
    return await fetch_sleeper(f"user/{username}")
async def get_user_id_details(user_id):
    return await fetch_sleeper(f"user/{user_id}")

# Avatars
async def get_avatar_full(avatar_id):
    return await fetch_sleeper(f"avatars/{avatar_id}")
async def get_avatar_thumb(avatar_id):
    return await fetch_sleeper(f"avatars/thumbs/{avatar_id}")

# Leagues
async def get_leagues(user_id, season):
    return await fetch_sleeper(f"user/{user_id}/leagues/nfl/{season}")
async def get_league(league_id):
    return await fetch_sleeper(f"league/{league_id}")
async def get_rosters(league_id):
    return await fetch_sleeper(f"league/{league_id}/rosters")
async def get_users(league_id):
    return await fetch_sleeper(f"league/{league_id}/users")
async def get_matchups(league_id, week):
    return await fetch_sleeper(f"league/{league_id}/matchups/{week}")
async def get_winners_bracket(league_id):
    return await fetch_sleeper(f"league/{league_id}/winners_bracket")
async def get_losers_bracket(league_id):
    return await fetch_sleeper(f"league/{league_id}/losers_bracket")
async def get_transactions(league_id, week):
    return await fetch_sleeper(f"league/{league_id}/transactions/{week}")
async def get_traded_picks(league_id):
    return await fetch_sleeper(f"league/{league_id}/traded_picks")

# Drafts
async def get_drafts_user(user_id, season):
    return await fetch_sleeper(f"user/{user_id}/drafts/nfl/{season}")
async def get_drafts_league(league_id):
    return await fetch_sleeper(f"league/{league_id}/drafts")
async def get_draft(draft_id):
    return await fetch_sleeper(f"draft/{draft_id}")
async def get_draft_picks(draft_id):
    return await fetch_sleeper(f"draft/{draft_id}/picks")
async def get_traded_picks(draft_id):
    return await fetch_sleeper(f"draft/{draft_id}/traded_picks")

# Players
async def get_all_players():
    return await fetch_sleeper(f"players/nfl")
async def get_trending_players(type, lookback = 24, limit = 25):
    return await fetch_sleeper(f"players/nfl/trending/{type}?lookback_hours={lookback}&limit={limit}")