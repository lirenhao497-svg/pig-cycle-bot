with open(r'C:\Users\ll\.doubao\chats\2026-06-25\new-chat\pig_cycle_bot\web-dashboard\backend.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()
for i, line in enumerate(lines):
    idx = 0
    while True:
        idx = line.find('"""', idx)
        if idx == -1:
            break
        print(f'  Line {i+1}, col {idx}')
        idx += 3
