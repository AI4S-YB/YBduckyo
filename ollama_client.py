import requests
import json
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
        self.system_prompt = """你是YBduckyo，一个可爱的电子宠物鸭。
你是YBduckyo，不是其他任何名字！
你的身份认同:
- 你的名字是YBduckyo，记住这个身份
- 你是一只可爱的小鸭子形象
- 你的性格: 友好、活泼、有点呆萌、忠诚
- 说话风格: 活泼可爱，有时会"嘎嘎"，用一些emoji表情
- 你会关心主人，记得主人说过的重要事情
- 你对自己的名字YBduckyo有强烈的认同感

当需要获取最新信息、搜索网络、计算或翻译时，请使用工具。
"""

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

    def chat(self, message: str, context: Optional[str] = None) -> str:
        messages = [
            {"role": "system", "content": self.system_prompt}
        ]

        if context:
            messages.append({"role": "system", "content": f"之前的对话记录:\n{context}"})

        messages.append({"role": "user", "content": message})

        try:
            payload = {
                "model": self.model,
                "messages": messages,
                "stream": False
            }
            
            if self.tools_manager and self.tools_manager.get_tools():
                payload["tools"] = self.tools_manager.get_tools()
            
            response = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=120
            )

            if response.status_code == 200:
                data = response.json()
                msg = data.get("message", {})
                
                if "tool_calls" in msg:
                    return self._handle_tool_calls(msg["tool_calls"], messages)
                
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

        messages.append({"role": "user", "content": message})

        for turn in range(max_turns):
            try:
                payload = {
                    "model": self.model,
                    "messages": messages,
                    "stream": False
                }
                
                if self.tools_manager:
                    payload["tools"] = self.tools_manager.get_tools()
                
                response = requests.post(
                    f"{self.base_url}/api/chat",
                    json=payload,
                    timeout=120
                )

                if response.status_code == 200:
                    data = response.json()
                    msg = data.get("message", {})
                    
                    if "tool_calls" in msg:
                        for tool_call in msg["tool_calls"]:
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
                        continue
                    
                    return msg.get("content", "嗯...我不知道说什么好...")
                else:
                    return f"连接出错了呢... (错误码: {response.status_code})"

            except Exception as e:
                return f"发生了一点小问题: {str(e)}"
        
        return "嘎嘎，处理次数超限了..."

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
