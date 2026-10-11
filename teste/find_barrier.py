with open(r'C:\Users\karen.xavier\Desktop\pluraal saas\Frontend\index.html', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

idx = text.find('id="passwordChangeBarrier"')
if idx != -1:
    print(text[idx:idx+2500])
else:
    print('Not found')
