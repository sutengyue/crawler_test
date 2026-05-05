# 高性能本地搜索引擎系统

基于 Python 开发的高性能本地搜索引擎，包含爬虫、索引和搜索全链路。

## 功能特性

- **异步爬虫**: 使用 asyncio + httpx 实现异步多线程爬虫
- **中文分词**: 使用 jieba 进行中文分词处理
- **全文索引**: 使用 Whoosh 建立全文索引
- **混合排序**: TF-IDF + BM25 混合相关性排序
- **网页快照**: 保存原始 HTML 和提取文本
- **定时任务**: 使用 APScheduler 实现定时增量爬取
- **Web 界面**: FastAPI 搭建的可视化搜索页面
- **命令行接口**: 提供命令行搜索功能

## 技术栈

- Python 3.10+
- asyncio + httpx (异步爬虫)
- BeautifulSoup (HTML解析)
- jieba (中文分词)
- Whoosh (全文索引)
- FastAPI + Uvicorn (Web服务)
- APScheduler (定时任务)
- loguru (日志系统)
- Docker + docker-compose (容器部署)

## 项目结构

```
├── src/
│   ├── crawler/           # 爬虫模块
│   │   ├── __init__.py
│   │   ├── async_crawler.py   # 异步爬虫实现
│   │   └── html_parser.py     # HTML解析器
│   ├── indexer/           # 索引模块
│   │   ├── __init__.py
│   │   ├── tokenizer.py       # 中文分词器
│   │   └── whoosh_indexer.py  # Whoosh索引管理
│   ├── searcher/          # 搜索模块
│   │   ├── __init__.py
│   │   └── search_engine.py   # 搜索引擎核心
│   ├── api/               # API模块
│   │   ├── __init__.py
│   │   └── fastapi_app.py     # FastAPI应用
│   ├── cli/               # 命令行接口
│   │   ├── __init__.py
│   │   └── command_line.py    # CLI命令
│   ├── scheduler/         # 任务调度
│   │   ├── __init__.py
│   │   └── task_scheduler.py  # APScheduler任务
│   ├── utils/             # 工具模块
│   │   ├── __init__.py
│   │   ├── logger.py          # 日志配置
│   │   ├── config.py          # 配置管理
│   │   └── bloom_filter.py    # 布隆过滤器/MD5去重
│   ├── __init__.py
│   └── main.py            # 主入口
├── data/
│   ├── index/             # Whoosh索引目录
│   ├── snapshots/         # 网页快照目录
│   └── stopwords.txt      # 中文停用词表
├── logs/                  # 日志目录
├── config.yaml            # 配置文件
├── requirements.txt       # 依赖列表
├── Dockerfile             # Docker镜像构建
├── docker-compose.yml     # Docker Compose配置
└── README.md              # 项目说明
```

## 安装与运行

### 环境要求

- Python 3.10+
- pip (Python包管理工具)

### 安装依赖

```bash
pip install -r requirements.txt
```

### 配置文件

编辑 `config.yaml` 配置目标网站和各项参数：

```yaml
crawler:
  max_depth: 3                    # 爬取深度
  delay: 1.0                      # 请求间隔(秒)
  timeout: 30                     # 请求超时(秒)
  max_concurrent_requests: 10     # 最大并发请求数
  user_agents:                    # User-Agent列表
    - "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"
  target_websites:                # 目标网站配置
    - name: "example"
      url: "https://example.com"
      allowed_domains:
        - "example.com"
      start_urls:
        - "https://example.com"
      max_pages: 100

indexer:
  index_dir: "./data/index"
  snapshot_dir: "./data/snapshots"

search:
  default_limit: 10
  max_limit: 100

logging:
  level: "INFO"
  file: "./logs/search_engine.log"

scheduler:
  enabled: true
  interval_hours: 24              # 定时任务间隔(小时)
```

### 运行方式

#### 1. 命令行爬取

```bash
python -m src.main crawl
```

#### 2. 命令行搜索

```bash
python -m src.main search
```

#### 3. Web 服务

```bash
python -m src.main api
```

访问 http://localhost:8000 查看 Web 搜索界面。

#### 4. 定时任务调度

```bash
python -m src.main scheduler
```

#### 5. CLI 命令

```bash
python -m src.cli.command_line crawl
python -m src.cli.command_line search "关键词"
python -m src.cli.command_line stats
```

## Docker 部署

### 构建并运行

```bash
docker-compose up -d
```

### 访问服务

- Web 界面: http://localhost:8000
- Redis: localhost:6379

### 停止服务

```bash
docker-compose down
```

## API 接口

### 搜索接口

```
GET /api/search?query=关键词&page=1&limit=10
```

响应示例:
```json
{
  "query": "关键词",
  "total_hits": 100,
  "total_pages": 10,
  "current_page": 1,
  "results": [
    {
      "url": "https://example.com/page",
      "title": "页面标题",
      "score": 0.85,
      "highlight": "包含<mark>关键词</mark>的摘要",
      "word_count": 1000,
      "depth": 1
    }
  ]
}
```

### 搜索建议

```
GET /api/suggest?query=关键词
```

响应示例:
```json
{
  "suggestions": ["关键词1", "关键词2"]
}
```

### 统计信息

```
GET /api/stats
```

响应示例:
```json
{
  "document_count": 1000
}
```

## 扩展说明

### 添加新的目标网站

在 `config.yaml` 的 `target_websites` 列表中添加新网站配置：

```yaml
target_websites:
  - name: "my_site"
    url: "https://mysite.com"
    allowed_domains:
      - "mysite.com"
    start_urls:
      - "https://mysite.com"
      - "https://mysite.com/blog"
    max_pages: 500
```

### 自定义分词器

修改 `src/indexer/tokenizer.py` 中的 `ChineseTokenizer` 类，添加自定义分词逻辑。

### 修改排序算法

在 `src/searcher/search_engine.py` 中调整 `_calculate_hybrid_score` 方法的权重参数。

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！