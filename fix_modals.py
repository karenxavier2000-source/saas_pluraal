import os

path = r'C:\Users\karen.xavier\Desktop\pluraal saas\Frontend\index.html'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace('<div class="modal" id="userModal">', '<div class="modal-backdrop" id="userModal">')
text = text.replace('<div class="modal-content" style="max-width: 600px;">', '<div class="modal" style="max-width: 600px;">')

text = text.replace('<div class="modal" id="tempPasswordModal">', '<div class="modal-backdrop" id="tempPasswordModal">')
text = text.replace('<div class="modal-content" style="max-width: 400px; text-align: center;">', '<div class="modal" style="max-width: 400px; text-align: center;">')

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)

print('Modals updated.')
