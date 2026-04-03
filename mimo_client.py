"""
MiMo API 客户端 - 简化为两步流程
"""
import requests
import json
from datetime import datetime
from typing import Optional, List, Dict

try:
    from tools import ToolsManager, ToolResult
    HAS_TOOLS = True
except ImportError:
    HAS_TOOLS = False


class MiMoClient:
    def __init__(self, base_url: str = "https://api.xiaomimimo.com/v1", model: str = "mimo-v2-flash", api_key: str = ""):
        self.base_url = base_url
        self.model = model
        self.api_key = api_key
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
- 当用户询问新闻时，请用可爱的语气播报，可以适当展开描述

回复要求: 正常对话50字以内，新闻播报时可以根据内容适当展开（100-200字）！"""

    def _get_headers(self):
        return {
            "api-key": self.api_key,
            "Content-Type": "application/json"
        }

    def check_connection(self) -> bool:
        try:
            response = requests.get(
                f"{self.base_url}/models",
                headers=self._get_headers(),
                timeout=5
            )
            return response.status_code == 200
        except:
            return False

    def _need_search(self, message: str) -> tuple:
        always_search_keywords = [
            "今天", "昨天", "明天", "新闻", "天气", "最新", "现在", "当前",
            "热搜", "热搜榜", "几号", "星期几", "日期", "实时", "今日",
            "科技", "财经", "体育", "娱乐", "军事", "社会",
            "发生了什么", "有什么", "最近", "近期", "近期新闻"
        ]
        for kw in always_search_keywords:
            if kw in message:
                return True, "news"
        
        message_lower = message.lower()
        general_keywords = ["是什么", "怎么样", "如何", "为什么", "哪个", "哪里", "多少", "解释", "介绍", "查询", "上网", "怎么"]
        for kw in general_keywords:
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
        
        try:
            result = self.tools_manager.execute("rss_news", {"query": search_query})
            if result.success:
                return result.content
        except Exception:
            pass
        
        tool_map = {"news": "news_search", "web": "web_search", "image": "image_search", "video": "video_search"}
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

【重要】以下是刚刚联网搜索到的真实结果，你必须严格按照这些搜索结果来回答，不要编造任何信息：

{search_result}

请严格根据以上真实搜索结果回答用户问题，直接告诉用户搜索到的答案。新闻类问题可以适当展开描述（100-200字），普通问题回复50字以内。"""
                messages.append({"role": "user", "content": enhanced_message})
            else:
                messages.append({"role": "user", "content": message})
        else:
            messages.append({"role": "user", "content": message})

        try:
            payload = {
                "model": self.model,
                "messages": messages,
                "max_tokens": 500,
                "temperature": 0.8
            }
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self._get_headers(),
                json=payload,
                timeout=60
            )

            if response.status_code == 200:
                data = response.json()
                choices = data.get("choices", [])
                if choices:
                    msg = choices[0].get("message", {})
                    return msg.get("content", "嗯...我不知道说什么好...")
            else:
                return f"连接出错了呢... (错误码: {response.status_code})"

        except requests.exceptions.ConnectionError:
            return "呜呜，无法连接到MiMo服务..."
        except requests.exceptions.Timeout:
            return "思考时间太长了，让我再想想..."
        except Exception as e:
            return f"发生了一点小问题: {str(e)}"

        return "嘎嘎，处理出错了..."
