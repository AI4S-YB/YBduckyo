"""
测试脚本：测试搜索工具（不依赖 Ollama）
"""
from tools import WebSearchTool, NewsSearchTool, ImageSearchTool, VideoSearchTool

def test_search_tools():
    print("="*60)
    print("DDGS 搜索工具测试")
    print("="*60)
    
    test_cases = [
        ("今天有什么新闻", NewsSearchTool()),
        ("什么是人工智能", WebSearchTool()),
        ("猫咪图片", ImageSearchTool()),
        ("Python 教程视频", VideoSearchTool()),
    ]
    
    for query, tool in test_cases:
        print(f"\n测试: {query}")
        print(f"工具: {tool.name}")
        print("-"*40)
        
        result = tool.execute(query)
        
        if result.success:
            lines = result.content.split('\n')
            for line in lines[:10]:  # 只显示前10行
                print(line)
            if len(lines) > 10:
                print(f"... (共 {len(lines)} 行)")
        else:
            print(f"失败: {result.error}")
        
        print()

if __name__ == "__main__":
    test_search_tools()
