# 桌面电子宠物 🐱

一个可爱的桌面电子宠物应用，支持接入Ollama AI进行智能对话。

## 功能特点

- 🎨 **卡通可爱风格** - 圆润可爱的卡通宠物形象
- 🤖 **AI智能对话** - 接入Ollama API，支持多种大语言模型
- 💾 **记忆系统** - 宠物能记住你的偏好和历史对话
- 🐾 **多宠物互动** - 可以同时养多个宠物
- 🎭 **丰富表情** - 宠物会根据心情显示不同表情
- 🚶 **桌面游走** - 宠物会在桌面上自由移动

## 安装要求

- Python 3.8+
- Ollama (需要本地运行)

## 安装步骤

1. 安装依赖:
```bash
pip install -r requirements.txt
```

2. 确保Ollama正在运行:
```bash
ollama serve
```

3. 下载模型 (可选，默认使用llama3):
```bash
ollama pull llama3
```

4. 运行程序:
```bash
python main.py
```

## 使用方法

- **双击宠物** - 打开聊天窗口
- **右键宠物** - 显示菜单（添加宠物、切换外观等）
- **系统托盘** - 管理应用和退出

## 项目结构

```
desktop_pet/
├── main.py           # 主程序入口
├── ollama_client.py  # Ollama API客户端
├── memory.py         # 记忆系统
├── requirements.txt  # 依赖列表
└── memory/           # 记忆数据存储目录
    ├── conversations.json
    ├── preferences.json
    └── facts.json
```

## 自定义配置

在 `ollama_client.py` 中可以修改:
- `base_url`: Ollama服务地址 (默认: http://localhost:11434)
- `model`: 使用的模型 (默认: llama3)
- `system_prompt`: 宠物的性格设定

## 注意事项

- 首次运行会在当前目录创建 `memory` 文件夹存储数据
- 确保Ollama服务已启动，否则无法进行AI对话
- 支持的模型取决于本地Ollama安装的模型
