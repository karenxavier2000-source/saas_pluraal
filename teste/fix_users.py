import os

path = r'C:\Users\karen.xavier\Desktop\pluraal saas\Frontend\js\users.js'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

# Fix copy to clipboard
copy_old = '''        copyBtn.addEventListener('click', () => {
          const pwText = document.getElementById('displayTempPassword').textContent;
          navigator.clipboard.writeText(pwText).then(() => {
            App.showToast('Senha copiada para a área de transferência!', 'success');
          });
        });'''

copy_new = '''        copyBtn.addEventListener('click', () => {
          const pwText = document.getElementById('displayTempPassword').textContent;
          if (navigator.clipboard && window.isSecureContext) {
            navigator.clipboard.writeText(pwText).then(() => {
              App.showToast('Senha copiada!', 'success');
            }).catch(() => fallbackCopy(pwText));
          } else {
            fallbackCopy(pwText);
          }
          
          function fallbackCopy(text) {
            const textArea = document.createElement("textarea");
            textArea.value = text;
            textArea.style.position = "fixed";
            textArea.style.left = "-999999px";
            document.body.appendChild(textArea);
            textArea.focus();
            textArea.select();
            try {
              document.execCommand('copy');
              App.showToast('Senha copiada!', 'success');
            } catch (err) {
              App.showToast('Erro ao copiar senha.', 'danger');
            }
            document.body.removeChild(textArea);
          }
        });'''

if 'navigator.clipboard.writeText' in text:
    text = text.replace(copy_old, copy_new)
    print('Clipboard fixed.')

# Fix native confirm
confirm_old = '''  async handleResetPassword(userId, userName) {
    if (!confirm(Deseja realmente gerar uma nova senha temporária para o usuário ""?\\n\\nTodas as sessões ativas deste usuário serão encerradas imediatamente e ele será obrigado a cadastrar uma nova senha no próximo login.)) {
      return;
    }

    try {'''

confirm_new = '''  async handleResetPassword(userId, userName) {
    const msg = Deseja realmente gerar uma nova senha temporária para o usuário "<strong></strong>"?<br><br>Todas as sessões ativas deste usuário serão encerradas imediatamente e ele será obrigado a cadastrar uma nova senha no próximo login.;
    
    document.getElementById('customConfirmMessage').innerHTML = msg;
    document.getElementById('customConfirmModal').classList.add('active');
    
    // Cleanup previous event listeners
    const okBtn = document.getElementById('customConfirmOk');
    const cancelBtn = document.getElementById('customConfirmCancel');
    
    const newOkBtn = okBtn.cloneNode(true);
    const newCancelBtn = cancelBtn.cloneNode(true);
    okBtn.parentNode.replaceChild(newOkBtn, okBtn);
    cancelBtn.parentNode.replaceChild(newCancelBtn, cancelBtn);
    
    newCancelBtn.addEventListener('click', () => {
      document.getElementById('customConfirmModal').classList.remove('active');
    });
    
    newOkBtn.addEventListener('click', async () => {
      document.getElementById('customConfirmModal').classList.remove('active');
      try {'''

if 'if (!confirm' in text:
    text = text.replace(confirm_old, confirm_new)
    # Also need to add a closing bracket for the try block in handleResetPassword
    # The original was:
    # try { ... } catch { ... }
    # Now it is inside an async event listener, so we need to close the listener!
    
    # Let's replace the end of handleResetPassword
    end_old = '''      } catch (err) {
        App.showToast('Erro ao redefinir senha: ' + err.message, 'danger');
      }
    },'''
    
    end_new = '''      } catch (err) {
        App.showToast('Erro ao redefinir senha: ' + err.message, 'danger');
      }
    });
  },'''
    text = text.replace(end_old, end_new)
    print('Confirm replaced.')

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)

