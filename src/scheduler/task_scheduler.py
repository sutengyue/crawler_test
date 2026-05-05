from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from src.crawler.async_crawler import AsyncCrawler
from src.indexer.whoosh_indexer import WhooshIndexer
from src.utils.config import load_config
from src.utils.logger import setup_logger
import asyncio
import time

class TaskScheduler:
    def __init__(self, config):
        self.config = config
        self.logger = setup_logger(config)
        self.scheduler = BackgroundScheduler()
        self.interval_hours = config.get("scheduler", {}).get("interval_hours", 24)
    
    def _crawl_and_index(self):
        self.logger.info("Starting scheduled crawl task")
        
        target_websites = self.config.get("crawler", {}).get("target_websites", [])
        if not target_websites:
            self.logger.error("No target websites configured")
            return
        
        start_urls = []
        for site in target_websites:
            start_urls.extend(site.get("start_urls", []))
        
        if not start_urls:
            self.logger.error("No start URLs configured")
            return
        
        crawler = AsyncCrawler(self.config)
        results = asyncio.run(crawler.crawl(start_urls))
        
        self.logger.info(f"Scheduled crawl completed: {len(results)} pages")
        
        indexer = WhooshIndexer(self.config)
        for result in results:
            try:
                existing_doc = indexer.get_document(result["url"])
                if existing_doc:
                    indexer.update_document(
                        url=result["url"],
                        title=result["title"],
                        content=result["content"],
                        meta_description=result["meta_description"],
                        word_count=result["word_count"],
                        depth=result["depth"],
                        snapshot_path=result.get("snapshot_path"),
                        created_at=int(time.time())
                    )
                else:
                    indexer.add_document(
                        url=result["url"],
                        title=result["title"],
                        content=result["content"],
                        meta_description=result["meta_description"],
                        word_count=result["word_count"],
                        depth=result["depth"],
                        snapshot_path=result.get("snapshot_path"),
                        created_at=int(time.time())
                    )
            except Exception as e:
                self.logger.error(f"Failed to index {result['url']}: {e}")
        
        indexer.optimize()
        self.logger.info("Scheduled indexing completed")
    
    def start(self):
        if not self.config.get("scheduler", {}).get("enabled", True):
            self.logger.info("Scheduler is disabled")
            return
        
        self.scheduler.add_job(
            self._crawl_and_index,
            trigger=IntervalTrigger(hours=self.interval_hours),
            id="crawl_and_index",
            name="定期爬取和索引更新任务",
            replace_existing=True
        )
        
        self.logger.info(f"Scheduler started with interval: {self.interval_hours} hours")
        self.scheduler.start()
    
    def stop(self):
        if self.scheduler.running:
            self.scheduler.shutdown()
            self.logger.info("Scheduler stopped")
    
    def run_once(self):
        self._crawl_and_index()