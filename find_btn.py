with open(r'C:\Users\karen.xavier\Desktop\pluraal saas\Frontend\index.html', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

idx = text.find('id="barrierSubmitBtn"')
if idx != -1:
    print(text[idx-500:idx+500])
else:
    print('Not found')
