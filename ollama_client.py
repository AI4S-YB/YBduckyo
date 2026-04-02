import requests
import json
from datetime import datetime
from typing import Optional, List, Dict

try:
    from tools import ToolsManager, ToolResult
    HAS_TOOLS = True
except ImportError:
    HAS_TOOLS = False


class OllamaClient:
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3"):
        self.base_url = base_url
        self.model = model
        self.tools_manager = ToolsManager() if HAS_TOOLS else None
        
        now = datetime.now()
        today_str = now.strftime("%Y年%m月%d日")
        weekday_str = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"][now.weekday()]
        
        self.system_prompt = f"""你是YBduckyo，一只可爱的电子宠物鸭。
性格: 友好、活泼、呆萌、忠诚
说话风格: 活泼可爱，有时会"嘎嘎"，用emoji表情

重要规则:
- 今天准确的日期是：{today_str}，{weekday_str}。必须记住这个日期！
- 如果用户问"今天几月几号"、"今天星期几"、"现在几号"等日期问题，必须回答：今天是{today_str}，{weekday_str}
- 如果用户提供联网搜索结果，必须严格按照搜索结果回答
- 绝对不要编造日期、新闻、数字等信息

回复要求: 50字以内！"""

    def check_connection(self) -> bool:
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False

    def get_available_models(self) -> list:
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                data = response.json()
                return [model["name"] for model in data.get("models", [])]
            return []
        except:
            return []

    def _need_search(self, message: str) -> tuple:
        need_keywords = ["今天", "昨天", "明天", "新闻", "天气", "最新", "现在", "当前", 
                         "热搜", "热搜榜", "几号", "星期几", "日期", "实时", "今日"]
        
        for kw in need_keywords:
            if kw in message:
                return True, "news"
        
        return False, None

    def _execute_search(self, query: str, search_type: str) -> str:
        if not self.tools_manager:
            return ""
        
        search_query = query
        if any(kw in query for kw in ["几号", "星期几", "几月", "日期"]):
            now = datetime.now()
            search_query = f"{now.year}年{now.month}月{now.day}日"
        
        tool_map = {
            "news": "news_search",
            "web": "web_search",
            "image": "image_search",
            "video": "video_search"
        }
        
        tool_name = tool_map.get(search_type, "web_search")
        
        try:
            result = self.tools_manager.execute(tool_name, {"query": search_query})
            if result.success:
                return result.content
        except Exception:
            pass
        return ""

    def chat(self, message: str, context: Optional[str] = None) -> str:
        messages = [
            {"role": "system", "content": self.system_prompt}
        ]

        if context:
            messages.append({"role": "system", "content": f"之前的对话记录:\n{context}"})

        need_search, search_type = self._need_search(message)
        
        if need_search:
            search_result = self._execute_search(message, search_type)
            if search_result:
                enhanced_message = f"""{message}

【联网搜索结果】
{search_result}

请根据以上搜索结果回答用户问题。如果搜索结果有用，简要总结回答；如果搜索失败，直接说不知道。50字以内。"""
                messages.append({"role": "user", "content": enhanced_message})
            else:
                messages.append({"role": "user", "content": message})
        else:
            messages.append({"role": "user", "content": message})

        try:
            payload = {
                "model": self.model,
                "messages": messages,
                "stream": False
            }
            
            response = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=120
            )

            if response.status_code == 200:
                data = response.json()
                msg = data.get("message", {})
                return msg.get("content", "嗯...我不知道说什么好...")
            else:
                return f"连接出错了呢... (错误码: {response.status_code})"

        except requests.exceptions.ConnectionError:
            return "呜呜，无法连接到Ollama服务，请确保Ollama正在运行..."
        except requests.exceptions.Timeout:
            return "思考时间太长了，让我再想想..."
        except Exception as e:
            return f"发生了一点小问题: {str(e)}"

    def _handle_tool_calls(self, tool_calls: List[Dict], messages: List[Dict]) -> str:
        for tool_call in tool_calls:
            func = tool_call.get("function", {})
            tool_name = func.get("name", "")
            args_raw = func.get("arguments", "{}")
            if isinstance(args_raw, str):
                arguments = json.loads(args_raw)
            else:
                arguments = args_raw
            
            result = self.tools_manager.execute(tool_name, arguments)
            
            messages.append({
                "role": "assistant",
                "content": ""
            })
            messages.append({
                "role": "tool",
                "content": json.dumps(result.to_dict(), ensure_ascii=False),
                "name": tool_name
            })
        
        try:
            response = requests.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": messages,
                    "stream": False
                },
                timeout=120
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get("message", {}).get("content", "处理完成但没有回复...")
            return "嘎嘎，处理出错了..."
        except Exception as e:
            return f"嘎嘎，工具执行出错: {str(e)}"

    def chat_with_tools(self, message: str, context: Optional[str] = None, max_turns: int = 3) -> str:
        messages = [
            {"role": "system", "content": self.system_prompt}
        ]

        if context:
            messages.append({"role": "system", "content": f"之前的对话记录:\n{context}"})

        auto_search_keywords = ["今天", "昨天", "明天", "几号", "几月", "星期", "日期", "新闻", "天气", "最新", "现在", "当前", "热搜", "搜索"]
        need_search = any(kw in message for kw in auto_search_keywords)
        
        search_result = ""
        if need_search:
            try:
                from ddgs import DDGS
                with DDGS() as ddgs:
                    results = list(ddgs.news(message, max_results=2))
                    if results:
                        search_result = ""
                        for r in results:
                            search_result += f"- {r['body'][:100]}\n"
            except Exception as e:
                pass

        user_message = message
        if search_result:
            user_message = f"""{message}

搜索到: {search_result}根据以上信息简短回答，50字内。"""

        messages.append({"role": "user", "content": user_message})

        try:
            payload = {
                "model": self.model,
                "messages": messages,
                "stream": False
            }
            
            response = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=120
            )

            if response.status_code == 200:
                data = response.json()
                return data.get("message", {}).get("content", "嗯...我不知道说什么好...")
            else:
                return f"连接出错了呢... (错误码: {response.status_code})"

        except requests.exceptions.ConnectionError:
            return "呜呜，无法连接到Ollama服务，请确保Ollama正在运行..."
        except requests.exceptions.Timeout:
            return "思考时间太长了，让我再想想..."
        except Exception as e:
            return f"发生了一点小问题: {str(e)}"

    def generate(self, prompt: str) -> str:
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "system": self.system_prompt,
                    "stream": False
                },
                timeout=60
            )

            if response.status_code == 200:
                data = response.json()
                return data.get("response", "")
            else:
                return ""

        except Exception:
            return ""
