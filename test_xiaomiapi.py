"""
测试脚本：测试 MiMo 客户端
"""
import sys
import json
from pathlib import Path
from mimo_client import MiMoClient

sys.stdout.reconfigure(encoding='utf-8')

def load_config():
    config_path = Path("config.json")
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def test_mimo():
    config = load_config()
    ollama_config = config.get("ollama", {})
    
    client = MiMoClient(
        base_url=ollama_config.get("base_url", "https://api.xiaomimimo.com/v1"),
        model=ollama_config.get("model", "mimo-v2-flash"),
        api_key=ollama_config.get("api_key", "")
    )
    
    print("=" * 60)
    print("测试 MiMo 客户端 (支持 tool calling)")
    print("=" * 60)
    
    tests = [
        ("你好", False),
        ("今天有什么新闻", True),
        ("什么是人工智能", False),
        ("昨天发生了什么大事", True),
    ]
    
    for message, should_search in tests:
        print(f"\n用户: {message}")
        print("-" * 40)
        response = client.chat(message)
        print(f"回复: {response}")

if __name__ == "__main__":
    test_mimo()
