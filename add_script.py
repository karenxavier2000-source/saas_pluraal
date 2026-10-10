path = r'c:\Users\karen.xavier\Desktop\pluraal saas\Frontend\index.html'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace('<script src="js/enem.js"></script>', '<script src="js/enem.js"></script>\n    <script src="js/schools.js"></script>')
with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print('Added schools.js')
