import requests
import sys

print('测试开始', flush=True)

try:
    print('发送请求到: http://192.168.87.153:11434/api/chat', flush=True)
    response = requests.post('http://192.168.87.153:11434/api/chat', 
        json={
            'model': 'qwen3-vl:8b',
            'messages': [{'role': 'user', 'content': '你好，用一句话回复'}],
            'stream': False
        },
        timeout=90
    )
    print(f'状态码: {response.status_code}', flush=True)
    if response.status_code == 200:
        data = response.json()
        content = data.get('message', {}).get('content', '')
        print(f'回复: {content[:500]}', flush=True)
    else:
        print(f'错误响应: {response.text[:500]}', flush=True)
except Exception as e:
    print(f'发生错误: {type(e).__name__}: {e}', flush=True)
