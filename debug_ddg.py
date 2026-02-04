with open('ddg_debug.html', 'r', encoding='utf-8') as f:
    text = f.read()
import re
start = text.find('result__a')
if start > 0:
    print(text[start-200:start+2000])
else:
    print('No result__a found')
    for p in ['result', 'web-result', 'links_main', 'snippet']:
        idx = text.find(p)
        if idx > 0:
            print(f'Found "{p}" at {idx}:')
            print(text[idx-100:idx+500])
            break
    else:
        mid = len(text) // 2
        print(text[mid:mid+2000])
