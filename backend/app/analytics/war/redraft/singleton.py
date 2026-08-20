from concurrent.futures import ThreadPoolExecutor

from app.analytics.war.redraft.service import WARService

war_service = WARService()

war_thread_pool = ThreadPoolExecutor(
    max_workers=20,
    thread_name_prefix="war-calc",
)