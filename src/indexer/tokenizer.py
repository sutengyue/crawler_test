import jieba
import jieba.analyse
from whoosh.analysis import Tokenizer, Token

class ChineseTokenizer(Tokenizer):
    def __init__(self, stopwords=None):
        self.stopwords = stopwords or set()
    
    def __call__(self, text, **kwargs):
        words = jieba.cut(text, cut_all=False)
        for word in words:
            word = word.strip()
            if word and word not in self.stopwords and len(word) > 1:
                yield Token(text=word, pos=0, startchar=0, endchar=len(word))

def load_stopwords(filepath: str = "./data/stopwords.txt") -> set:
    stopwords = set()
    if filepath and os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                stopwords.add(line.strip())
    return stopwords

def extract_keywords(text: str, top_n: int = 10) -> list:
    keywords = jieba.analyse.extract_tags(text, topK=top_n, withWeight=False)
    return keywords

import os