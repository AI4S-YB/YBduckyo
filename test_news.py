"""
测试脚本：验证联网搜索功能
"""
import sys
import json
from pathlib import Path
from ollama_client import OllamaClient

sys.stdout.reconfigure(encoding='utf-8')

def load_config():
    config_path = Path("config.json")
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def test_search():
    config = load_config()
    ollama_config = config.get("ollama", {})
    
    client = OllamaClient(
        base_url=ollama_config.get("base_url", "http://localhost:11434"),
        model=ollama_config.get("model", "llama3")
    )
    
    if not client.check_connection():
        print("错误: 无法连接到 Ollama 服务")
        return
    
    print("Ollama 连接成功!")
    print()
    
    tests = [
        ("今天有什么新闻", True, "新闻搜索"),
        ("今天天气怎么样", True, "天气查询"),
        ("什么是Python", False, "知识问答"),
        ("你好", False, "普通对话"),
        ("昨天的热搜", True, "新闻搜索"),
    ]
    
    for message, should_search, desc in tests:
        print("="*50)
        print(f"[{desc}] 用户: {message}")
        print("-"*50)
        need, _ = client._need_search(message)
        print(f"需要搜索: {'是' if need else '否'}")
        response = client.chat(message)
        print(f"回复: {response}")
        print()

if __name__ == "__main__":
    test_search()
