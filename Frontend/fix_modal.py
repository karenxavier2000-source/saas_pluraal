import os
path = r'c:\Users\karen.xavier\Desktop\pluraal saas\Frontend\index.html'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

old_str = '''  <!-- ================= EXPANDED SCHOOL LIST MODAL ================= -->
  <div class="modal" id="schoolListModal">
    <div class="modal-content" style="max-width: 800px; height: 80vh; display: flex; flex-direction: column;">'''

new_str = '''  <!-- ================= EXPANDED SCHOOL LIST MODAL ================= -->
  <div class="modal-backdrop" id="schoolListModal">
    <div class="modal" style="max-width: 800px; height: 80vh; display: flex; flex-direction: column;">'''

content = content.replace(old_str, new_str)
with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated index.html modal class")
