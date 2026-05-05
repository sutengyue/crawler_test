from fastapi import FastAPI, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from src.searcher.search_engine import SearchEngine
from src.utils.config import load_config
from src.utils.logger import setup_logger
import uvicorn
import os

app = FastAPI(title="Local Search Engine", version="1.0")

config = load_config()
logger = setup_logger(config)
search_engine = SearchEngine(config)

class SearchRequest(BaseModel):
    query: str
    page: int = 1
    limit: int = 10

class SearchResponse(BaseModel):
    query: str
    total_hits: int
    total_pages: int
    current_page: int
    results: list

@app.get("/api/search", response_model=SearchResponse)
def search(query: str = Query(..., min_length=1), page: int = Query(1, ge=1), limit: int = Query(10, ge=1, le=100)):
    result = search_engine.search(query, page=page, limit=limit)
    return result

@app.get("/api/suggest")
def suggest(query: str = Query(..., min_length=1)):
    suggestions = search_engine.suggest(query)
    return {"suggestions": suggestions}

@app.get("/api/snapshot")
def get_snapshot(snapshot_path: str = Query(...)):
    content = search_engine.get_snapshot(snapshot_path)
    return {"content": content}

@app.get("/api/stats")
def stats():
    count = search_engine.index_count()
    return {"document_count": count}

@app.get("/", response_class=HTMLResponse)
def home():
    html_content = """
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>本地搜索引擎</title>
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
            .container { max-width: 800px; margin: 0 auto; }
            .search-box { width: 100%; padding: 12px 20px; font-size: 18px; border: 2px solid #ddd; border-radius: 24px; outline: none; }
            .search-box:focus { border-color: #4285f4; }
            .search-btn { padding: 12px 30px; font-size: 18px; background: #4285f4; color: white; border: none; border-radius: 24px; cursor: pointer; margin-left: 10px; }
            .search-btn:hover { background: #3367d6; }
            .result-item { background: white; padding: 20px; margin: 10px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            .result-title { font-size: 18px; color: #1a0dab; text-decoration: none; }
            .result-title:hover { text-decoration: underline; }
            .result-url { color: #006621; font-size: 14px; }
            .result-snippet { color: #545454; font-size: 14px; margin-top: 8px; }
            .highlight { background: #ffff00; }
            .pagination { margin-top: 20px; text-align: center; }
            .page-link { padding: 8px 16px; margin: 0 4px; border: 1px solid #ddd; border-radius: 4px; text-decoration: none; color: #1a0dab; }
            .page-link:hover { background: #eee; }
            .page-link.active { background: #4285f4; color: white; border-color: #4285f4; }
            .stats { text-align: center; color: #666; margin-bottom: 20px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1 style="text-align: center; color: #4285f4; margin-bottom: 30px;">🔍 本地搜索引擎</h1>
            <div style="text-align: center; margin-bottom: 20px;">
                <input type="text" id="query" class="search-box" placeholder="输入搜索关键词..." onkeyup="handleKeyup(event)">
                <button class="search-btn" onclick="doSearch()">搜索</button>
            </div>
            <div id="suggestions" style="text-align: center; margin-bottom: 10px;"></div>
            <div class="stats" id="stats"></div>
            <div id="results"></div>
            <div class="pagination" id="pagination"></div>
        </div>
        <script>
            let currentPage = 1;
            
            async function loadStats() {
                const res = await fetch('/api/stats');
                const data = await res.json();
                document.getElementById('stats').textContent = `已索引 ${data.document_count} 个文档`;
            }
            
            async function doSearch(page = 1) {
                const query = document.getElementById('query').value;
                if (!query.trim()) return;
                
                currentPage = page;
                const res = await fetch(`/api/search?query=${encodeURIComponent(query)}&page=${page}&limit=10`);
                const data = await res.json();
                displayResults(data);
            }
            
            function displayResults(data) {
                const resultsDiv = document.getElementById('results');
                const paginationDiv = document.getElementById('pagination');
                
                if (data.total_hits === 0) {
                    resultsDiv.innerHTML = '<p style="text-align: center; color: #666;">未找到相关结果</p>';
                    paginationDiv.innerHTML = '';
                    return;
                }
                
                let html = '';
                data.results.forEach(result => {
                    html += `
                        <div class="result-item">
                            <h3><a href="${result.url}" target="_blank" class="result-title">${result.title}</a></h3>
                            <div class="result-url">${result.url}</div>
                            <div class="result-snippet">${result.highlight || '暂无摘要'}</div>
                        </div>
                    `;
                });
                resultsDiv.innerHTML = html;
                
                let pagination = '';
                for (let i = 1; i <= data.total_pages; i++) {
                    pagination += `<a href="#" class="page-link ${i === currentPage ? 'active' : ''}" onclick="doSearch(${i})">${i}</a>`;
                }
                paginationDiv.innerHTML = pagination;
            }
            
            async function handleKeyup(event) {
                if (event.key === 'Enter') {
                    doSearch(1);
                    return;
                }
                
                const query = event.target.value;
                if (query.length > 2) {
                    const res = await fetch(`/api/suggest?query=${encodeURIComponent(query)}`);
                    const data = await res.json();
                    const suggestionsDiv = document.getElementById('suggestions');
                    if (data.suggestions.length > 0) {
                        suggestionsDiv.innerHTML = '建议: ' + data.suggestions.map(s => `<a href="#" onclick="document.getElementById('query').value='${s}'; doSearch(1);">${s}</a>`).join(' | ');
                    } else {
                        suggestionsDiv.innerHTML = '';
                    }
                }
            }
            
            loadStats();
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

def run(host: str = "0.0.0.0", port: int = 8000):
    logger.info(f"Starting FastAPI server on {host}:{port}")
    uvicorn.run(app, host=host, port=port)