"""APScheduler placeholder for reminders."""

from apscheduler.schedulers.asyncio import AsyncIOScheduler


def create_scheduler() -> AsyncIOScheduler:
    """Create a scheduler instance without jobs."""
    return AsyncIOScheduler()
