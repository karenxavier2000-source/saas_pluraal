import os

file_path = r'c:\Users\karen.xavier\Desktop\pluraal saas\Frontend\index.html'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Locate footer start
footer_index = content.find('      <footer class="app-footer">')
if footer_index == -1:
    footer_index = content.find('<footer>')

# Locate enem view
enem_start = content.find('      <!-- View: ENEM -->')
enem_end = content.find('      <!-- Report Viewer Modal -->')

if enem_start != -1 and enem_end != -1 and footer_index != -1:
    enem_block = content[enem_start:enem_end]
    # Remove enem_block from current position
    content = content[:enem_start] + content[enem_end:]
    
    # Insert before footer
    new_footer_index = content.find('      <footer class="app-footer">')
    content = content[:new_footer_index] + enem_block + content[new_footer_index:]
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Moved viewEnem before footer.")
else:
    print("Could not find blocks.")
