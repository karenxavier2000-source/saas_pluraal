import re

file_path = r'c:\Users\karen.xavier\Desktop\pluraal saas\Frontend\index.html'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace the entire viewPaaeb block
pattern = r'<!-- View: PAAEB -->.*?<section id="viewPaaeb".*?</section>'
replacement = '''<!-- View: PAAEB -->
      <section id="viewPaaeb" class="view-content hidden" style="background: transparent;">
        <div class="paaeb-grid" style="width: 100%; max-width: 1400px; margin: 0 auto;">
            <!-- Renderizado via JS -->
        </div>
      </section>'''

new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(new_content)
