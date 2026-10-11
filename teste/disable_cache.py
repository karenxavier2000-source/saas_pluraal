import sys

path = r'C:\Users\karen.xavier\Desktop\pluraal saas\Backend\server.py'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

# Flask by default sets max-age. We can set SEND_FILE_MAX_AGE_DEFAULT = 0
if 'app = Flask(__name__, static_folder=None)' in text:
    text = text.replace('app = Flask(__name__, static_folder=None)', 'app = Flask(__name__, static_folder=None)\n    app.config[\'SEND_FILE_MAX_AGE_DEFAULT\'] = 0')
    
    with open(path, 'w', encoding='utf-8') as f:
        f.write(text)
    print('Cache disabled in Flask.')
