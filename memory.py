import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional


class MemorySystem:
    def __init__(self, memory_dir: str = "memory"):
        self.memory_dir = Path(memory_dir)
        self.memory_dir.mkdir(exist_ok=True)
        
        self.conversation_file = self.memory_dir / "conversations.json"
        self.preferences_file = self.memory_dir / "preferences.json"
        self.facts_file = self.memory_dir / "facts.json"
        
        self.conversations = self.load_json(self.conversation_file, [])
        self.preferences = self.load_json(self.preferences_file, {})
        self.facts = self.load_json(self.facts_file, {})
        
        self.max_conversations = 50

    def load_json(self, file_path: Path, default):
        if file_path.exists():
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                return default
        return default

    def save_json(self, file_path: Path, data):
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def add_conversation(self, user_message: str, pet_response: str):
        conversation = {
            "timestamp": datetime.now().isoformat(),
            "user": user_message,
            "pet": pet_response
        }
        self.conversations.append(conversation)
        
        if len(self.conversations) > self.max_conversations:
            self.conversations = self.conversations[-self.max_conversations:]
        
        self.save_json(self.conversation_file, self.conversations)
        
        self.extract_preferences(user_message)
        self.extract_facts(user_message)

    def extract_preferences(self, message: str):
        preference_keywords = {
            "喜欢": "likes",
            "讨厌": "dislikes",
            "爱": "likes",
            "不喜欢": "dislikes",
            "最爱": "likes",
            "最讨厌": "dislikes"
        }
        
        for keyword, pref_type in preference_keywords.items():
            if keyword in message:
                parts = message.split(keyword)
                if len(parts) > 1:
                    preference = parts[1].strip()[:50]
                    if preference:
                        if pref_type not in self.preferences:
                            self.preferences[pref_type] = []
                        if preference not in self.preferences[pref_type]:
                            self.preferences[pref_type].append(preference)
                            self.save_json(self.preferences_file, self.preferences)

    def extract_facts(self, message: str):
        fact_keywords = ["我叫", "我的名字", "我是", "我今年", "我住在"]
        
        for keyword in fact_keywords:
            if keyword in message:
                fact = message[message.index(keyword):].strip()[:100]
                if fact:
                    fact_key = f"fact_{len(self.facts)}"
                    self.facts[fact_key] = {
                        "content": fact,
                        "timestamp": datetime.now().isoformat()
                    }
                    self.save_json(self.facts_file, self.facts)
                    break

    def get_context(self, max_items: int = 10) -> str:
        recent_conversations = self.conversations[-max_items:]
        
        context_parts = []
        
        context_parts.append("重要提醒: 你是YBduckyo！不要忘记你的名字和身份！\n")
        
        if self.facts:
            facts_text = "关于主人的信息:\n"
            for key, fact in list(self.facts.items())[-5:]:
                facts_text += f"- {fact['content']}\n"
            context_parts.append(facts_text)
        
        if self.preferences:
            pref_text = "主人的偏好:\n"
            if "likes" in self.preferences:
                pref_text += f"喜欢: {', '.join(self.preferences['likes'][-3:])}\n"
            if "dislikes" in self.preferences:
                pref_text += f"讨厌: {', '.join(self.preferences['dislikes'][-3:])}\n"
            context_parts.append(pref_text)
        
        if recent_conversations:
            conv_text = "最近的对话:\n"
            for conv in recent_conversations:
                conv_text += f"主人: {conv['user']}\nYBduckyo: {conv['pet']}\n"
            context_parts.append(conv_text)
        
        return "\n".join(context_parts)

    def get_pet_personality(self) -> str:
        return """你是YBduckyo，一个可爱的电子宠物鸭。
你是YBduckyo，不是其他任何名字。
你的身份认同:
- 你的名字是YBduckyo，记住这个身份
- 你是一只可爱的小鸭子形象
- 你的性格: 友好、活泼、有点呆萌、忠诚
- 说话风格: 活泼可爱，有时会"嘎嘎"，用一些emoji表情
- 你会关心主人，记得主人说过的重要事情
- 你对自己的名字YBduckyo有强烈的认同感

记住: 你就是YBduckyo！"""

    def clear_memory(self):
        self.conversations = []
        self.preferences = {}
        self.facts = {}
        self.save_json(self.conversation_file, [])
        self.save_json(self.preferences_file, {})
        self.save_json(self.facts_file, {})

    def get_memory_stats(self) -> Dict:
        return {
            "conversations_count": len(self.conversations),
            "preferences_count": len(self.preferences.get("likes", [])) + len(self.preferences.get("dislikes", [])),
            "facts_count": len(self.facts)
        }
