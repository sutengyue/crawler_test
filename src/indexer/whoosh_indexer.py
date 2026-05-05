import os
from whoosh.index import create_in, open_dir, Index
from whoosh.fields import Schema, TEXT, ID, STORED, NUMERIC
from whoosh.qparser import QueryParser
from whoosh import scoring
from src.indexer.tokenizer import ChineseTokenizer
from src.utils.logger import setup_logger

class WhooshIndexer:
    def __init__(self, config: dict):
        self.config = config
        self.logger = setup_logger(config)
        self.index_dir = config.get("indexer", {}).get("index_dir", "./data/index")
        self.schema = self._create_schema()
        self.index = None
        
        os.makedirs(self.index_dir, exist_ok=True)
        self._init_index()
    
    def _create_schema(self) -> Schema:
        return Schema(
            url=ID(unique=True, stored=True),
            title=TEXT(stored=True, analyzer=ChineseTokenizer()),
            content=TEXT(stored=True, analyzer=ChineseTokenizer()),
            meta_description=TEXT(stored=True),
            word_count=NUMERIC(stored=True),
            depth=NUMERIC(stored=True),
            snapshot_path=STORED,
            created_at=NUMERIC(stored=True)
        )
    
    def _init_index(self):
        if os.path.exists(self.index_dir) and len(os.listdir(self.index_dir)) > 0:
            try:
                self.index = open_dir(self.index_dir)
                self.logger.info(f"Opened existing index at {self.index_dir}")
            except Exception as e:
                self.logger.error(f"Failed to open index: {e}")
                self.index = create_in(self.index_dir, self.schema)
        else:
            self.index = create_in(self.index_dir, self.schema)
            self.logger.info(f"Created new index at {self.index_dir}")
    
    def add_document(self, **kwargs):
        if not self.index:
            self._init_index()
        
        with self.index.writer() as writer:
            writer.add_document(**kwargs)
        self.logger.debug(f"Added document: {kwargs.get('url', '')}")
    
    def update_document(self, **kwargs):
        if not self.index:
            self._init_index()
        
        url = kwargs.get("url")
        if not url:
            return
        
        with self.index.writer() as writer:
            writer.update_document(**kwargs)
        self.logger.debug(f"Updated document: {url}")
    
    def delete_document(self, url: str):
        if not self.index:
            return
        
        with self.index.writer() as writer:
            writer.delete_by_term("url", url)
        self.logger.debug(f"Deleted document: {url}")
    
    def optimize(self):
        if self.index:
            try:
                with self.index.writer() as writer:
                    if callable(writer.optimize):
                        writer.optimize()
                    else:
                        writer.optimize = True
                self.logger.info("Index optimized")
            except Exception as e:
                self.logger.warning(f"Failed to optimize index: {e}")
    
    def search(self, query_str: str, limit: int = 10, offset: int = 0) -> list:
        if not self.index:
            return []
        
        results = []
        try:
            with self.index.searcher(weighting=scoring.BM25F()) as searcher:
                query_parser = QueryParser("content", schema=self.index.schema)
                query = query_parser.parse(query_str)
                
                hits = searcher.search(query, limit=limit + offset)
                
                for hit in hits[offset:]:
                    results.append({
                        "url": hit["url"],
                        "title": hit["title"],
                        "score": hit.score,
                        "word_count": hit["word_count"],
                        "depth": hit["depth"],
                        "snapshot_path": hit.get("snapshot_path"),
                        "highlight": hit.highlights("content", text=query_str)
                    })
        except Exception as e:
            self.logger.error(f"Search error: {e}")
        
        return results
    
    def get_document(self, url: str) -> dict:
        if not self.index:
            return {}
        
        with self.index.searcher() as searcher:
            query = QueryParser("url", schema=self.index.schema).parse(url)
            hits = searcher.search(query)
            if hits:
                return dict(hits[0])
        return {}
    
    def count(self) -> int:
        if not self.index:
            return 0
        return self.index.doc_count()