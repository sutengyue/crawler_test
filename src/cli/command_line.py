import argparse
import asyncio
from src.crawler.async_crawler import AsyncCrawler
from src.searcher.search_engine import SearchEngine
from src.indexer.whoosh_indexer import WhooshIndexer
from src.utils.config import load_config
from src.utils.logger import setup_logger
import sys

def crawl_command(args):
    config = load_config(args.config)
    logger = setup_logger(config)
    
    target_websites = config.get("crawler", {}).get("target_websites", [])
    if not target_websites:
        logger.error("No target websites configured")
        return
    
    start_urls = []
    for site in target_websites:
        start_urls.extend(site.get("start_urls", []))
    
    if not start_urls:
        logger.error("No start URLs configured")
        return
    
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

def search_command(args):
    config = load_config(args.config)
    search_engine = SearchEngine(config)
    
    result = search_engine.search(args.query, page=args.page, limit=args.limit)
    
    print(f"\n搜索结果: '{args.query}'")
    print(f"共找到 {result['total_hits']} 条结果")
    print("-" * 60)
    
    for i, item in enumerate(result["results"], start=1):
        print(f"\n{i}. {item['title']}")
        print(f"   URL: {item['url']}")
        print(f"   评分: {item['score']:.4f}")
        if item.get("highlight"):
            print(f"   摘要: {item['highlight'][:100]}...")
    
    print(f"\n第 {result['current_page']}/{result['total_pages']} 页")

def stats_command(args):
    config = load_config(args.config)
    search_engine = SearchEngine(config)
    count = search_engine.index_count()
    print(f"已索引文档数: {count}")

def run_cli():
    parser = argparse.ArgumentParser(description="Local Search Engine CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    crawl_parser = subparsers.add_parser("crawl", help="Start crawling")
    crawl_parser.add_argument("-c", "--config", default="./config.yaml", help="Config file path")
    
    search_parser = subparsers.add_parser("search", help="Search the index")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument("-p", "--page", type=int, default=1, help="Page number")
    search_parser.add_argument("-l", "--limit", type=int, default=10, help="Results per page")
    search_parser.add_argument("-c", "--config", default="./config.yaml", help="Config file path")
    
    stats_parser = subparsers.add_parser("stats", help="Show statistics")
    stats_parser.add_argument("-c", "--config", default="./config.yaml", help="Config file path")
    
    args = parser.parse_args()
    
    if args.command == "crawl":
        crawl_command(args)
    elif args.command == "search":
        search_command(args)
    elif args.command == "stats":
        stats_command(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    run_cli()