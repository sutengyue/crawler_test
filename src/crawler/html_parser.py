from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re

class HTMLParser:
    @staticmethod
    def parse(html_content: str, base_url: str) -> dict:
        soup = BeautifulSoup(html_content, "html.parser")
        
        title = HTMLParser._extract_title(soup)
        meta_description = HTMLParser._extract_meta_description(soup)
        content = HTMLParser._extract_content(soup)
        links = HTMLParser._extract_links(soup, base_url)
        
        return {
            "title": title,
            "meta_description": meta_description,
            "content": content,
            "links": links,
            "word_count": len(content.split())
        }
    
    @staticmethod
    def _extract_title(soup) -> str:
        title_tag = soup.find("title")
        if title_tag:
            return title_tag.get_text(strip=True)
        return ""
    
    @staticmethod
    def _extract_meta_description(soup) -> str:
        meta_tag = soup.find("meta", attrs={"name": "description"})
        if meta_tag:
            return meta_tag.get("content", "").strip()
        return ""
    
    @staticmethod
    def _extract_content(soup) -> str:
        content_tags = soup.find_all(["p", "h1", "h2", "h3", "h4", "h5", "h6", "article", "main"])
        texts = []
        for tag in content_tags:
            text = tag.get_text(strip=True)
            if text:
                texts.append(text)
        return "\n".join(texts)
    
    @staticmethod
    def _extract_links(soup, base_url: str) -> list[str]:
        links = set()
        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"]
            full_url = urljoin(base_url, href)
            parsed = urlparse(full_url)
            if parsed.scheme in ("http", "https"):
                links.add(full_url)
        return list(links)
    
    @staticmethod
    def clean_text(text: str) -> str:
        text = re.sub(r"\s+", " ", text)
        text = text.strip()
        return text