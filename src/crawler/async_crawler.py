import asyncio
import httpx
import random
from urllib.parse import urlparse
from src.crawler.html_parser import HTMLParser
from src.utils.bloom_filter import BloomFilter, MD5Deduplicator
from src.utils.logger import setup_logger
import os

class AsyncCrawler:
    def __init__(self, config: dict):
        self.config = config
        self.logger = setup_logger(config)
        self.delay = config.get("crawler", {}).get("delay", 1.0)
        self.timeout = config.get("crawler", {}).get("timeout", 30)
        self.max_depth = config.get("crawler", {}).get("max_depth", 3)
        self.max_concurrent = config.get("crawler", {}).get("max_concurrent_requests", 10)
        self.user_agents = config.get("crawler", {}).get("user_agents", [])
        self.semaphore = asyncio.Semaphore(self.max_concurrent)
        self.deduplicator = MD5Deduplicator()
        self.visited = set()
        self.results = []
        
        os.makedirs("./data/snapshots", exist_ok=True)
        self.snapshot_dir = config.get("indexer", {}).get("snapshot_dir", "./data/snapshots")
    
    async def fetch(self, url: str) -> tuple[str, int, dict]:
        headers = {
            "User-Agent": random.choice(self.user_agents) if self.user_agents else "Mozilla/5.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Referer": url
        }
        
        try:
            async with self.semaphore:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.get(url, headers=headers)
                    await asyncio.sleep(self.delay)
                    return (url, response.status_code, response.text)
        except httpx.HTTPError as e:
            self.logger.error(f"HTTP error fetching {url}: {e}")
            return (url, 500, "")
        except asyncio.TimeoutError:
            self.logger.error(f"Timeout fetching {url}")
            return (url, 408, "")
        except Exception as e:
            self.logger.error(f"Error fetching {url}: {e}")
            return (url, 500, "")
    
    async def crawl_page(self, url: str, depth: int = 0) -> list:
        if depth > self.max_depth:
            return []
        
        if url in self.visited:
            return []
        
        parsed_url = urlparse(url)
        allowed_domains = self.config.get("crawler", {}).get("target_websites", [{}])[0].get("allowed_domains", [])
        if allowed_domains:
            domain = parsed_url.netloc
            if domain.startswith('www.'):
                domain = domain[4:]
            if domain not in allowed_domains and parsed_url.netloc not in allowed_domains:
                return []
        
        self.visited.add(url)
        self.logger.info(f"Crawling [{depth}] {url}")
        
        url, status, html = await self.fetch(url)
        
        if status != 200:
            return []
        
        result = HTMLParser.parse(html, url)
        result["url"] = url
        result["depth"] = depth
        
        snapshot_path = os.path.join(self.snapshot_dir, f"{hash(url)}.html")
        with open(snapshot_path, "w", encoding="utf-8") as f:
            f.write(html)
        result["snapshot_path"] = snapshot_path
        
        self.results.append(result)
        
        tasks = []
        for link in result.get("links", []):
            if link not in self.visited:
                tasks.append(self.crawl_page(link, depth + 1))
        
        if tasks:
            await asyncio.gather(*tasks)
        
        return self.results
    
    async def crawl(self, start_urls: list[str]) -> list:
        self.results = []
        self.visited = set()
        
        tasks = [self.crawl_page(url) for url in start_urls]
        await asyncio.gather(*tasks)
        
        return self.results
    
    def get_results(self) -> list:
        return self.results