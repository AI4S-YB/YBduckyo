from ddgs import DDGS
import sys

print('测试联网搜索...')
print('='*50)

try:
    with DDGS() as ddgs:
        print('DDGS连接成功，正在搜索...')
        results = list(ddgs.text('今天是几月几号', max_results=3))
        print(f'找到 {len(results)} 条结果:')
        print('-'*50)
        for i, r in enumerate(results, 1):
            print(f'{i}. {r["title"]}')
            print(f'   {r["body"][:200]}')
            print()
except Exception as e:
    print(f'错误: {type(e).__name__}: {e}')

input('\n按回车退出...')
