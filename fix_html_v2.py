import os

file_path = r'c:\Users\karen.xavier\Desktop\pluraal saas\Frontend\index.html'
with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

start_enem = -1
end_enem = -1
for i, line in enumerate(lines):
    if '<!-- View: ENEM -->' in line:
        start_enem = i
    if start_enem != -1 and '</section>' in line and i > start_enem:
        end_enem = i
        break

footer_start = -1
for i, line in enumerate(lines):
    if '<footer class="app-footer">' in line:
        footer_start = i
        break

if start_enem != -1 and end_enem != -1 and footer_start != -1:
    enem_lines = lines[start_enem:end_enem+1]
    
    new_lines = []
    for i, line in enumerate(lines):
        if i == footer_start:
            new_lines.extend(enem_lines)
            new_lines.append(line)
        elif start_enem <= i <= end_enem:
            continue
        else:
            new_lines.append(line)

    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    print("Mover realizado com sucesso!")
else:
    print(f"Falha: start_enem={start_enem}, end_enem={end_enem}, footer={footer_start}")
