"""
测试脚本：验证联网搜索功能（含新闻RSS）
"""
import sys
import json
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')


def test_news_sources():
    print("=" * 60)
    print("【测试】news_sources 模块")
    print("=" * 60)
    try:
        from news_sources import get_news, format_news
        print("✓ 模块导入成功\n")
        
        # 测试综合新闻
        print("获取综合新闻...")
        news = get_news('综合', 3)
        if news:
            print(f"✓ 获取成功 ({len(news)} 条)\n")
            print(format_news(news[:2]))
        else:
            print("✗ 获取失败\n")
        
        # 测试分类新闻
        print("\n测试分类新闻:")
        categories = ['科技', '财经', '体育', '娱乐']
        for cat in categories:
            news = get_news(cat, 1)
            status = "✓" if news else "✗"
            title = news[0]['title'][:35] if news else "无数据"
            print(f"  {status} {cat}: {title}...")
        
    except Exception as e:
        print(f"✗ 测试失败: {e}")
    print()


def test_rss_tool():
    print("=" * 60)
    print("【测试】RssNewsTool")
    print("=" * 60)
    try:
        from tools import RssNewsTool
        tool = RssNewsTool()
        
        test_queries = [
            '今天有什么新闻',
            '科技新闻',
            '财经最新消息'
        ]
        
        for query in test_queries:
            print(f"\n查询: {query}")
            result = tool.execute(query)
            if result.success:
                print("✓ 成功")
                print("预览: " + result.content[:200].replace("\n", " ") + "...")
            else:
                print(f"✗ 失败: {result.error}")
        
    except Exception as e:
        print(f"✗ 测试失败: {e}")
    print()


def test_llm_client():
    print("=" * 60)
    print("【测试】LLM 客户端")
    print("=" * 60)
    
    config_path = Path("config.json")
    if not config_path.exists():
        print("✗ 配置文件不存在，跳过LLM测试")
        return
    
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)
    
    ollama_config = config.get("ollama", {})
    base_url = ollama_config.get("base_url", "")
    
    if "xiaomimimo.com" in base_url or "api.mimo" in base_url:
        from mimo_client import MiMoClient
        client = MiMoClient(
            base_url=base_url,
            model=ollama_config.get("model", "mimo-v2-flash"),
            api_key=ollama_config.get("api_key", "")
        )
        print("使用 MiMo 客户端")
    else:
        from ollama_client import OllamaClient
        client = OllamaClient(
            base_url=base_url,
            model=ollama_config.get("model", "llama3")
        )
        print("使用 Ollama 客户端")
    
    if hasattr(client, 'check_connection'):
        if not client.check_connection():
            print("✗ 无法连接到 LLM 服务")
            return
    
    print("✓ LLM 服务连接成功\n")
    
    # 测试普通对话
    print("测试普通对话:")
    response = client.chat("你好")
    print(f"  回复: {response}\n")
    
    # 测试新闻（会调用RSS）
    print("测试新闻查询:")
    response = client.chat("今天有什么新闻")
    print(f"  回复: {response[:300]}..." if len(response) > 300 else f"  回复: {response}")


def test_dependencies():
    print("=" * 60)
    print("【检查】依赖项")
    print("=" * 60)
    
    deps = {
        'requests': 'HTTP请求',
        'feedparser': 'RSS解析',
        'PyQt5': 'GUI界面'
    }
    
    for dep, desc in deps.items():
        try:
            __import__(dep)
            print(f"✓ {dep} ({desc})")
        except ImportError:
            print(f"✗ {dep} ({desc}) - 请运行: pip install {dep}")
    print()


if __name__ == "__main__":
    test_dependencies()
    print()
    test_news_sources()
    print()
    test_rss_tool()
    print()
    test_llm_client()
    print()
    print("=" * 60)
    print("测试完成！")
    print("=" * 60)
    print()
    print("下一步:")
    print("1. 运行 python main.py 启动宠物")
    print("2. 对宠物说: '今天有什么新闻' 或 '科技新闻'")
    print("3. 宠物会联网获取最新新闻并播报给你")

