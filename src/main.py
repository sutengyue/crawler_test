import argparse
import asyncio
import signal
import sys
from src.crawler.async_crawler import AsyncCrawler
from src.indexer.whoosh_indexer import WhooshIndexer
from src.searcher.search_engine import SearchEngine
from src.api.fastapi_app import run as run_api
from src.cli.command_line import run_cli
from src.scheduler.task_scheduler import TaskScheduler
from src.utils.config import load_config
from src.utils.logger import setup_logger

def signal_handler(signal, frame):
    print("\nShutting down gracefully...")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

def main():
    parser = argparse.ArgumentParser(description="Local Search Engine")
    parser.add_argument("-c", "--config", default="./config.yaml", help="Config file path")
    parser.add_argument("command", choices=["crawl", "search", "api", "scheduler", "cli"], help="Command to run")
    args = parser.parse_args()
    
    config = load_config(args.config)
    logger = setup_logger(config)
    
    if args.command == "crawl":
        logger.info("Starting crawl command")
        target_websites = config.get("crawler", {}).get("target_websites", [])
        if not target_websites:
            logger.error("No target websites configured")
            return
        
        start_urls = []
        for site in target_websites:
            start_urls.extend(site.get("start_urls", []))
        
        crawler = AsyncCrawler(config)
        results = asyncio.run(crawler.crawl(start_urls))
        
        logger.info(f"Crawled {len(results)} pages")
        
        indexer = WhooshIndexer(config)
        for result in results:
            indexer.add_document(
                url=result["url"],
                title=result["title"],
                content=result["content"],
                meta_description=result["meta_description"],
                word_count=result["word_count"],
                depth=result["depth"],
                snapshot_path=result.get("snapshot_path"),
                created_at=result.get("created_at", 0)
            )
        
        indexer.optimize()
        logger.info("Indexing completed")
    
    elif args.command == "search":
        logger.info("Starting interactive search")
        search_engine = SearchEngine(config)
        while True:
            query = input("Search: ").strip()
            if not query:
                continue
            if query.lower() == "exit":
                break
            
            result = search_engine.search(query)
            print(f"\n找到 {result['total_hits']} 条结果")
            for i, item in enumerate(result["results"], start=1):
                print(f"\n{i}. {item['title']}")
                print(f"   URL: {item['url']}")
                if item.get("highlight"):
                    print(f"   摘要: {item['highlight'][:150]}...")
            print()
    
    elif args.command == "api":
        logger.info("Starting API server")
        run_api(host="0.0.0.0", port=8000)
    
    elif args.command == "scheduler":
        logger.info("Starting scheduler")
        scheduler = TaskScheduler(config)
        scheduler.start()
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            scheduler.stop()
    
    elif args.command == "cli":
        run_cli()
    
    else:
        parser.print_help()

import time

if __name__ == "__main__":
    main()