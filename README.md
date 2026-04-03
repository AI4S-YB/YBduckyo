# YBducyo 优秀而忠臣的桌面捣乱大师 🐱

**QQ宠物文化传承案例**
<img width="301" height="359" alt="5a3e6094-ef47-4561-88c9-78a758f9ec77" src="https://github.com/user-attachments/assets/c9f900c4-2342-4a3d-af99-8c1e362bb3c8" />

## 功能特点

- 🎨 **卡通可爱风格** - Duckyo可爱无需多言
- 🤖 **AI智能对话** - 接入大模型，支持多种大语言模型，智能联网搜索，实时更新
- 💾 **记忆系统** - 宠物能记住你的偏好和历史对话
- 🐾 **多宠物互动** - 可以同时养多个宠物
- 🎭 **丰富表情** - 宠物会根据心情显示不同表情（会睡觉）
- 🚶 **桌面游走** - 宠物会在桌面上自由移动

## 安装要求

- Python 3.11+

## 安装步骤
```
点一下start.bat
```
**手动安装**
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

- **鼠标放到宠物上** - 打开聊天窗口
- **右键宠物** - 显示菜单（详细聊天记录，添加宠物、切换外观等）
- **关闭bat** - 退出

## 项目结构

```
desktop_pet/
├── main.py           # 主程序入口
├── xx_client.py  # API客户端
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
