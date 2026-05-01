import httpx, logging, asyncio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MAX_CONCURRENT_REQUESTS = 20
limit = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)

client: httpx.AsyncClient = None
error_count = 0

async def fetch_sleeper(endpoint: str, retries: int = 3):
    global error_count, client
    
    if client is None:
        raise RuntimeError("Sleeper client not initialized!")

    url = f"https://api.sleeper.app/v1/{endpoint}"

    async with limit:
        if error_count > 50:
            raise RuntimeError("Error count exceeded!")

        for attempt in range(retries):
            try:
                response = await client.get(url)

                if response.status_code == 429:
                    error_count += 5 
                    await asyncio.sleep(10)
                    continue 

                result = handle_sleeper_error(response)
  
                if response.status_code in [400, 404]:
                    return None

                response.raise_for_status()
                
                if error_count > 0:
                    error_count -= 1 
                return result

            except (httpx.HTTPStatusError, httpx.RequestError) as e:
                error_count += 1
                
                status_code = getattr(e.response, "status_code", None)
                if status_code == 429:
                    logger.warning(f"Rate limited by Sleeper. Cooling down...")
                    await asyncio.sleep(10)

                if attempt < retries - 1:
                    wait_time = (2 ** attempt) + 1
                    logger.warning(f"Sleeper error for {endpoint}. Retry {attempt+1} in {wait_time}s.")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"Final failure for {endpoint}: {e}")
                    raise e

def handle_sleeper_error(response: httpx.Response):
    status = response.status_code
    if status == 200:
        return response.json()
    if status == 400:
        logger.error("400 Bad Request: Check your league/user IDs.")
    elif status == 404:
        logger.warning("404 Not Found: That resource (kitten/league) doesn't exist.")
    elif status == 429:
        logger.warning("429 Too Many Requests: Sleeper is throttling us!")
    elif status >= 500:
        logger.error(f"{status} Server Error: Sleeper is having a bad day.")
        return None
 
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
async def get_NFL_state():
    return await fetch_sleeper(f"state/nfl")

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