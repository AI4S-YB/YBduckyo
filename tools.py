import requests
import json
import re
from typing import Dict, List, Optional, Callable

try:
    from duckduckgo_search import DDGS
    HAS_DDGS = True
except ImportError:
    HAS_DDGS = False


class ToolResult:
    def __init__(self, success: bool, content: str, error: str = ""):
        self.success = success
        self.content = content
        self.error = error
    
    def to_dict(self):
        return {
            "success": self.success,
            "content": self.content,
            "error": self.error
        }


class WebSearchTool:
    def __init__(self):
        self.name = "web_search"
        self.description = "搜索互联网获取最新信息。适用于回答需要最新资讯、新闻或实时数据的问题。输入搜索关键词，返回搜索结果摘要。"
    
    def execute(self, query: str) -> ToolResult:
        try:
            if HAS_DDGS:
                with DDGS() as ddgs:
                    results = list(ddgs.text(query, max_results=5))
                    if results:
                        content = "搜索结果:\n"
                        for i, r in enumerate(results, 1):
                            content += f"{i}. {r['title']}\n   {r['href']}\n   {r['body'][:200]}...\n"
                        return ToolResult(True, content)
                    return ToolResult(False, "", "未找到相关结果")
            else:
                return ToolResult(False, "", "搜索功能未安装，请运行: pip install duckduckgo-search")
        except Exception as e:
            return ToolResult(False, "", f"搜索出错: {str(e)}")


class WebFetchTool:
    def __init__(self):
        self.name = "web_fetch"
        self.description = "获取指定URL的网页内容。适用于需要查看特定网页详细内容的场景，如获取文章、文档或网页的具体信息。输入URL，返回网页的主要内容（去除HTML标签后的文本）。"
    
    def execute(self, url: str) -> ToolResult:
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.encoding = response.apparent_encoding
            
            text = response.text
            text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL)
            text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
            text = re.sub(r'<[^>]+>', '', text)
            text = re.sub(r'\s+', ' ', text).strip()
            
            return ToolResult(True, text[:3000])
        except Exception as e:
            return ToolResult(False, "", f"获取网页失败: {str(e)}")


class CalculatorTool:
    def __init__(self):
        self.name = "calculator"
        self.description = "执行数学计算。适用于需要计算数值、统计数据或进行数学运算的场景。输入数学表达式，返回计算结果。"
    
    def execute(self, expression: str) -> ToolResult:
        try:
            expression = re.sub(r'[^0-9+\-*/.()% ]', '', expression)
            result = eval(expression)
            return ToolResult(True, f"{expression} = {result}")
        except Exception as e:
            return ToolResult(False, "", f"计算错误: {str(e)}")


class TranslateTool:
    def __init__(self):
        self.name = "translate"
        self.description = "翻译文本。输入要翻译的文本和目标语言代码（如en, zh, ja），返回翻译结果。"
    
    def execute(self, text: str, target_lang: str = "en") -> ToolResult:
        try:
            url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl={target_lang}&dt=t&q={text}"
            response = requests.get(url, timeout=10)
            data = response.json()
            result = ''.join([item[0] for item in data[0]])
            return ToolResult(True, result)
        except Exception as e:
            return ToolResult(False, "", f"翻译失败: {str(e)}")


class WeatherTool:
    def __init__(self):
        self.name = "weather"
        self.description = "查询天气信息。输入城市名称，返回该城市的当前天气、温度等信息。"
    
    def execute(self, city: str) -> ToolResult:
        try:
            url = f"https://wttr.in/{city}?format=j1"
            response = requests.get(url, timeout=10)
            data = response.json()
            current = data['current_condition'][0]
            result = f"{city}天气:\n"
            result += f"温度: {current['temp_C']}°C\n"
            result += f"天气: {current['weatherDesc'][0]['value']}\n"
            result += f"湿度: {current['humidity']}%\n"
            result += f"风速: {current['windspeedKmph']} km/h"
            return ToolResult(True, result)
        except Exception as e:
            return ToolResult(False, "", f"获取天气失败: {str(e)}")


class ToolsManager:
    def __init__(self):
        self.tools: List[Dict] = []
        self.tool_instances: Dict[str, Callable] = {}
        self._register_tools()
    
    def _register_tools(self):
        self.register(WebSearchTool())
        self.register(WebFetchTool())
        self.register(CalculatorTool())
        self.register(TranslateTool())
        self.register(WeatherTool())
    
    def register(self, tool_instance):
        tool_dict = {
            "type": "function",
            "function": {
                "name": tool_instance.name,
                "description": tool_instance.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "搜索关键词或URL"}
                    },
                    "required": ["query"]
                }
            }
        }
        self.tools.append(tool_dict)
        self.tool_instances[tool_instance.name] = tool_instance
    
    def execute(self, tool_name: str, arguments: Dict) -> ToolResult:
        if tool_name in self.tool_instances:
            args = arguments.get('query', '')
            return self.tool_instances[tool_name].execute(args)
        return ToolResult(False, "", f"未知工具: {tool_name}")
    
    def get_tools(self) -> List[Dict]:
        return self.tools
