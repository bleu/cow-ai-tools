from typing import List, Dict, Union
import datetime as dt
import asyncio
import os

from op_brains.config import SUMMARIZER_MODEL, USE_SUMMARY_MOCK_DATA
from op_brains.documents.optimism import ForumPostsProcessingStrategy
from op_brains.summarizer.summarizer import summarize_thread
from op_brains.exceptions import OpChatBrainsException

from op_data.db.models import RawTopic, RawTopicSummary

from tortoise.exceptions import OperationalError, DBConnectionError

# Configuration for concurrent processing
# Lower default to avoid rate limits and reduce database pressure (users can increase via env var)
MAX_CONCURRENT_SUMMARIES = int(os.getenv("MAX_CONCURRENT_SUMMARIES", "5"))
# Batch size for incremental saving (save every N summaries)
BATCH_SIZE = int(os.getenv("SUMMARY_BATCH_SIZE", "10"))
# Retry configuration for database operations
MAX_DB_RETRIES = int(os.getenv("MAX_DB_RETRIES", "3"))
DB_RETRY_DELAY = float(os.getenv("DB_RETRY_DELAY", "1.0"))
# Delay between batch saves to reduce database connection pressure (in seconds)
BATCH_SAVE_DELAY = float(os.getenv("BATCH_SAVE_DELAY", "0.5"))


async def retry_on_db_error(func, *args, max_retries=MAX_DB_RETRIES, delay=DB_RETRY_DELAY, **kwargs):
    """
    Retry a database operation on connection errors.
    This handles transient connection issues with serverless databases like Neon.
    """
    last_error = None
    for attempt in range(max_retries):
        try:
            return await func(*args, **kwargs)
        except (OperationalError, DBConnectionError, ConnectionError) as e:
            last_error = e
            if attempt < max_retries - 1:
                wait_time = delay * (2 ** attempt)  # Exponential backoff
                print(f"⚠️  Database connection error (attempt {attempt + 1}/{max_retries}): {str(e)}")
                print(f"Retrying in {wait_time:.1f}s...")
                await asyncio.sleep(wait_time)
            else:
                print(f"❌ Failed after {max_retries} attempts: {str(e)}")

    raise last_error


class RawTopicSummaryService:
    @staticmethod
    async def get_topics_urls_to_summarize(out_of_date: bool = True) -> List[str]:
        async def _get_topics():
            if out_of_date:
                topics = await ForumPostsProcessingStrategy.get_threads_documents_not_summarized()
            else:
                topics = await ForumPostsProcessingStrategy.get_threads_documents()
            return [topic.metadata["url"] for topic in topics if topic.metadata["url"]]

        return await retry_on_db_error(_get_topics)

    @staticmethod
    async def summarize_single_topic(
        url: str, model_name: str
    ) -> Dict[str, Union[str, Dict[str, str]]]:
        try:
            summary = await summarize_thread(
                url, model_name, use_mock_data=USE_SUMMARY_MOCK_DATA
            )
            return {"url": url, "data": summary, "error": False}
        except OpChatBrainsException as e:
            return {"url": url, "data": {"error": str(e)}, "error": True}

    @classmethod
    async def summarize_topics(
        cls, out_of_date: bool = True, max_concurrent: int = None
    ) -> List[Dict[str, Union[str, Dict[str, str]]]]:
        if max_concurrent is None:
            max_concurrent = MAX_CONCURRENT_SUMMARIES

        topics_urls = await cls.get_topics_urls_to_summarize(out_of_date=out_of_date)
        print(f"we have #{len(topics_urls)} to summarize")
        print(f"Processing with max {max_concurrent} concurrent operations")
        summaries = []

        if not topics_urls:
            return summaries

        # Use semaphore to limit concurrent operations
        semaphore = asyncio.Semaphore(max_concurrent)
        completed_count = 0

        async def rate_limited_summarize(url: str, index: int):
            nonlocal completed_count
            async with semaphore:
                result = await cls.summarize_single_topic(url, SUMMARIZER_MODEL)
                completed_count += 1
                if completed_count % 10 == 0:
                    print(f"Progress: {completed_count}/{len(topics_urls)} summaries completed")
                return result

        tasks = [
            asyncio.create_task(rate_limited_summarize(url, i))
            for i, url in enumerate(topics_urls)
        ]

        summaries = await asyncio.gather(*tasks)

        return summaries

    @staticmethod
    async def bulk_save_summaries(summaries: List[Dict[str, str]]):
        raw_summaries = [
            RawTopicSummary(
                url=summary["url"],
                data=summary["data"],
                error=summary["error"],
            )
            for summary in summaries
        ]

        await RawTopicSummary.bulk_create(raw_summaries)

    @staticmethod
    async def update_raw_topics_as_summarized(urls: List[str]) -> bool:
        await RawTopic.filter(url__in=urls).update(
            lastSummarizedAt=dt.datetime.now(dt.UTC)
        )

    @staticmethod
    def get_summaries_urls(summaries: List[Dict[str, str]]) -> List[str]:
        return [summary["url"] for summary in summaries]

    @classmethod
    async def acquire_and_save_incremental(
        cls, batch_size: int = None, max_concurrent: int = None
    ):
        """
        Acquire and save summaries incrementally in batches.
        This prevents data loss if the process fails mid-execution.
        """
        if batch_size is None:
            batch_size = BATCH_SIZE
        if max_concurrent is None:
            max_concurrent = MAX_CONCURRENT_SUMMARIES

        print("Acquiring and saving summaries (incremental mode)")
        print(f"Batch size: {batch_size} (saves every {batch_size} summaries)")

        topics_urls = await cls.get_topics_urls_to_summarize(out_of_date=True)
        print(f"we have #{len(topics_urls)} to summarize")
        print(f"Processing with max {max_concurrent} concurrent operations")

        if not topics_urls:
            print("No topics to summarize")
            return

        # Use semaphore to limit concurrent operations
        semaphore = asyncio.Semaphore(max_concurrent)
        save_lock = asyncio.Lock()  # Lock for thread-safe batch operations
        completed_count = 0
        total_saved = 0
        batch_buffer = []

        async def save_batch(batch_to_save: List):
            """Helper function to save a batch of summaries with retry logic"""
            nonlocal total_saved
            try:
                urls_to_save = cls.get_summaries_urls(batch_to_save)

                # Use retry logic for database operations
                await retry_on_db_error(cls.bulk_save_summaries, batch_to_save)
                await retry_on_db_error(cls.update_raw_topics_as_summarized, urls_to_save)

                total_saved += len(batch_to_save)
                print(f"✅ Saved batch: {total_saved}/{len(topics_urls)} summaries saved to database")

                # Small delay to reduce connection pool pressure
                await asyncio.sleep(BATCH_SAVE_DELAY)
                return True
            except Exception as e:
                print(f"❌ Error saving batch: {str(e)}")
                return False

        async def rate_limited_summarize(url: str, index: int):
            nonlocal completed_count

            async with semaphore:
                result = await cls.summarize_single_topic(url, SUMMARIZER_MODEL)
                completed_count += 1

                # Add to batch buffer (thread-safe with lock)
                async with save_lock:
                    batch_buffer.append(result)

                    # Save batch when buffer is full
                    if len(batch_buffer) >= batch_size:
                        batch_to_save = batch_buffer[:]
                        batch_buffer.clear()

                        # Save this batch (outside the lock to allow concurrent processing)
                        await save_batch(batch_to_save)

                # Progress update
                if completed_count % 5 == 0:
                    print(f"Progress: {completed_count}/{len(topics_urls)} summaries completed (saved: {total_saved})")

                return result

        # Create all tasks
        tasks = [
            asyncio.create_task(rate_limited_summarize(url, i))
            for i, url in enumerate(topics_urls)
        ]

        # Wait for all to complete
        try:
            await asyncio.gather(*tasks)
        except Exception as e:
            print(f"⚠️  Error during processing: {str(e)}")
            print(e)
            print(f"Attempting to save remaining {len(batch_buffer)} summaries from buffer...")

        # Save any remaining summaries in buffer
        if batch_buffer:
            print(f"Saving final batch of {len(batch_buffer)} summaries...")
            await save_batch(batch_buffer)

        print(f"\n{'='*60}")
        print(f"Incremental save complete!")
        print(f"Total saved: {total_saved}/{len(topics_urls)} summaries")
        if total_saved < len(topics_urls):
            print(f"⚠️  Warning: {len(topics_urls) - total_saved} summaries failed to save")
        print(f"{'='*60}\n")

    @classmethod
    async def acquire_and_save(cls):
        """Legacy method - now uses incremental saving"""
        await cls.acquire_and_save_incremental()

    @staticmethod
    async def update_relationships():
        pass
