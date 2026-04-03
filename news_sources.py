"""
新闻源模块 - 实时获取中文新闻
支持新浪、网易等主流媒体的 RSS/JSON 接口
"""
import requests
import json
import re
from datetime import datetime
from typing import List, Dict, Optional

try:
    import feedparser
    HAS_FEEDPARSER = True
except ImportError:
    HAS_FEEDPARSER = False


class NewsSource:
    def __init__(self, name: str, url: str, source_type: str = "rss"):
        self.name = name
        self.url = url
        self.source_type = source_type

    def fetch(self, limit: int = 10) -> List[Dict]:
        try:
            if self.source_type == "json":
                return self._fetch_json(limit)
            else:
                return self._fetch_rss(limit)
        except Exception as e:
            print(f"[NewsSource] 获取失败 {self.name}: {e}")
            return []

    def _fetch_rss(self, limit: int) -> List[Dict]:
        if not HAS_FEEDPARSER:
            return self._fetch_rss_fallback(limit)
        
        feed = feedparser.parse(self.url)
        news_list = []
        
        for entry in feed.entries[:limit]:
            news = {
                "title": self._clean_html(entry.get("title", "")),
                "source": self.name,
                "url": entry.get("link", ""),
                "pubdate": self._parse_date(entry),
                "summary": self._clean_html(entry.get("summary", entry.get("description", "")))[:200]
            }
            news_list.append(news)
        
        return news_list

    def _fetch_rss_fallback(self, limit: int) -> List[Dict]:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/rss+xml, application/xml, text/xml, */*'
        }
        try:
            response = requests.get(self.url, headers=headers, timeout=10)
            response.encoding = response.apparent_encoding
            
            titles = re.findall(r'<title><!\[CDATA\[(.*?)\]\]></title>', response.text)
            links = re.findall(r'<link>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</link>', response.text)
            pubdates = re.findall(r'<pubDate>(.*?)</pubDate>', response.text)
            descriptions = re.findall(r'<description><!\[CDATA\[(.*?)\]\]></description>', response.text)
            
            news_list = []
            for i in range(min(limit, len(titles))):
                news = {
                    "title": titles[i] if i < len(titles) else "",
                    "source": self.name,
                    "url": links[i] if i < len(links) else "",
                    "pubdate": pubdates[i] if i < len(pubdates) else "",
                    "summary": self._clean_html(descriptions[i] if i < len(descriptions) else "")[:200]
                }
                news_list.append(news)
            
            return news_list
        except Exception as e:
            print(f"[NewsSource] Fallback RSS 获取失败: {e}")
            return []

    def _fetch_json(self, limit: int) -> List[Dict]:
        try:
            response = requests.get(self.url, timeout=10)
            data = response.json()
            
            news_list = []
            items = data.get("result", {}).get("data", []) or data.get("data", [])
            
            for item in items[:limit]:
                ctime = item.get("ctime", item.get("pubdate", ""))
                if ctime and str(ctime).isdigit() and len(str(ctime)) == 10:
                    from datetime import datetime as dt
                    pubdate = dt.fromtimestamp(int(ctime)).strftime("%m-%d %H:%M")
                else:
                    pubdate = str(ctime)
                
                news = {
                    "title": item.get("title", ""),
                    "source": item.get("media_name", self.name),
                    "url": item.get("url", item.get("link", "")),
                    "pubdate": pubdate,
                    "summary": item.get("intro", item.get("desc", ""))[:200]
                }
                news_list.append(news)
            
            return news_list
        except Exception as e:
            print(f"[NewsSource] JSON 获取失败: {e}")
            return []

    def _parse_date(self, entry) -> str:
        if hasattr(entry, 'published_parsed') and entry.published_parsed:
            try:
                dt = datetime(*entry.published_parsed[:6])
                return dt.strftime("%Y-%m-%d %H:%M")
            except:
                pass
        return entry.get("published", "")

    def _clean_html(self, text: str) -> str:
        text = re.sub(r'<[^>]+>', '', text)
        text = re.sub(r'&nbsp;', ' ', text)
        text = re.sub(r'&amp;', '&', text)
        text = re.sub(r'&lt;', '<', text)
        text = re.sub(r'&gt;', '>', text)
        text = re.sub(r'&quot;', '"', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text


SOURCES = {
    "综合": NewsSource("新浪热点", "https://feed.mix.sina.com.cn/api/roll/get?pageid=153&lid=2516&num=10&page=1", "json"),
    "科技": NewsSource("新浪科技", "https://feed.mix.sina.com.cn/api/roll/get?pageid=153&lid=216&num=10&page=1", "json"),
    "财经": NewsSource("新浪财经", "https://feed.mix.sina.com.cn/api/roll/get?pageid=153&lid=1686&num=10&page=1", "json"),
    "体育": NewsSource("新浪体育", "https://feed.mix.sina.com.cn/api/roll/get?pageid=153&lid=475&num=10&page=1", "json"),
    "娱乐": NewsSource("新浪娱乐", "https://feed.mix.sina.com.cn/api/roll/get?pageid=153&lid=217&num=10&page=1", "json"),
    "军事": NewsSource("新浪军事", "https://feed.mix.sina.com.cn/api/roll/get?pageid=153&lid=190&num=10&page=1", "json"),
    "社会": NewsSource("新浪社会", "https://feed.mix.sina.com.cn/api/roll/get?pageid=153&lid=2517&num=10&page=1", "json"),
}

BACKUP_SOURCES = {
    "网易科技": NewsSource("网易科技", "https://news.163.com/special/rss/tech.xml"),
    "网易体育": NewsSource("网易体育", "https://sports.163.com/special/rss/sports.xml"),
    "网易财经": NewsSource("网易财经", "https://money.163.com/special/rss/finance.xml"),
}


def get_news(category: str = "综合", limit: int = 10, keyword: str = "") -> List[Dict]:
    results = []
    
    if category in SOURCES:
        results = SOURCES[category].fetch(limit)
    
    if not results:
        for source in SOURCES.values():
            results = source.fetch(limit)
            if results:
                break
    
    if keyword and results:
        keyword_lower = keyword.lower()
        results = [r for r in results if keyword_lower in r["title"].lower() or keyword_lower in r["summary"].lower()]
    
    return results[:limit]


def format_news(News_list: List[Dict], show_url: bool = False) -> str:
    if not News_list:
        return "暂无新闻内容"
    
    lines = ["📰 最新新闻\n"]
    
    for i, news in enumerate(News_list, 1):
        lines.append(f"{i}. {news['title']}")
        if news.get('pubdate'):
            lines.append(f"   ⏰ {news['pubdate']}")
        if news.get('source'):
            lines.append(f"   📢 {news['source']}")
        if news.get('summary') and news['summary'] != news['title']:
            lines.append(f"   📝 {news['summary']}")
        if show_url and news.get('url'):
            lines.append(f"   🔗 {news['url']}")
        lines.append("")
    
    return "\n".join(lines)


def search_news(keyword: str, category: str = "综合", limit: int = 10) -> str:
    news_list = get_news(category, limit, keyword)
    return format_news(news_list, show_url=True)


if __name__ == "__main__":
    print("=== 测试新闻获取 ===\n")
    
    news = get_news("综合", 5)
    print(format_news(news, show_url=True))
