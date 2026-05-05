from src.indexer.whoosh_indexer import WhooshIndexer
from src.utils.logger import setup_logger
import math
from collections import Counter

class SearchEngine:
    def __init__(self, config: dict):
        self.config = config
        self.logger = setup_logger(config)
        self.indexer = WhooshIndexer(config)
        self.tfidf_cache = {}
        self.bm25_k1 = 1.2
        self.bm25_b = 0.75
    
    def _calculate_tf(self, text: str, term: str) -> float:
        words = text.lower().split()
        term_count = words.count(term.lower())
        return term_count / len(words) if words else 0
    
    def _calculate_idf(self, term: str, total_docs: int, doc_count_with_term: int) -> float:
        if doc_count_with_term == 0:
            return 0
        return math.log((total_docs - doc_count_with_term + 0.5) / (doc_count_with_term + 0.5) + 1)
    
    def _calculate_bm25(self, tf: float, idf: float, doc_length: int, avg_doc_length: float) -> float:
        numerator = idf * tf * (self.bm25_k1 + 1)
        denominator = tf + self.bm25_k1 * (1 - self.bm25_b + self.bm25_b * (doc_length / avg_doc_length))
        return numerator / denominator if denominator != 0 else 0
    
    def _calculate_hybrid_score(self, bm25_score: float, tfidf_score: float, alpha: float = 0.7) -> float:
        return alpha * bm25_score + (1 - alpha) * tfidf_score
    
    def search(self, query_str: str, page: int = 1, limit: int = 10) -> dict:
        offset = (page - 1) * limit
        raw_results = self.indexer.search(query_str, limit=limit, offset=offset)
        
        total_docs = self.indexer.count()
        total_hits = len(raw_results)
        
        results = []
        for hit in raw_results:
            content = hit.get("highlight", hit.get("content", ""))
            tf = self._calculate_tf(content, query_str)
            idf = self._calculate_idf(query_str, total_docs, total_hits)
            tfidf_score = tf * idf
            
            doc_length = hit.get("word_count", 0)
            avg_doc_length = self._get_avg_doc_length()
            bm25_score = self._calculate_bm25(tf, idf, doc_length, avg_doc_length)
            
            hybrid_score = self._calculate_hybrid_score(bm25_score, tfidf_score)
            
            results.append({
                "url": hit["url"],
                "title": hit["title"],
                "score": hybrid_score,
                "bm25_score": bm25_score,
                "tfidf_score": tfidf_score,
                "highlight": hit.get("highlight", ""),
                "word_count": hit["word_count"],
                "depth": hit["depth"],
                "snapshot_path": hit.get("snapshot_path")
            })
        
        results.sort(key=lambda x: x["score"], reverse=True)
        
        total_pages = (total_hits + limit - 1) // limit
        
        return {
            "query": query_str,
            "total_hits": total_hits,
            "total_pages": total_pages,
            "current_page": page,
            "results": results
        }
    
    def _get_avg_doc_length(self) -> float:
        try:
            with self.indexer.index.searcher() as searcher:
                total_length = 0
                count = 0
                for doc in searcher.all_stored_fields():
                    total_length += doc.get("word_count", 0)
                    count += 1
                return total_length / count if count > 0 else 1000
        except Exception:
            return 1000
    
    def suggest(self, query_str: str) -> list[str]:
        suggestions = []
        try:
            with self.indexer.index.searcher() as searcher:
                query_parser = self.indexer.index.schema.parse_query(query_str)
                corrected = searcher.correct_query(query_parser, query_str)
                if corrected.query != query_str:
                    suggestions.append(corrected.query)
        except Exception as e:
            self.logger.error(f"Suggest error: {e}")
        
        return suggestions
    
    def get_snapshot(self, snapshot_path: str) -> str:
        if snapshot_path and os.path.exists(snapshot_path):
            with open(snapshot_path, "r", encoding="utf-8") as f:
                return f.read()
        return ""
    
    def index_count(self) -> int:
        return self.indexer.count()

import os