import re

with open('Frontend/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

modal_code = """
  <!-- ================= USER CREATE/EDIT MODAL ================= -->
  <div class="modal" id="userModal">
    <div class="modal-content" style="max-width: 600px;">
      <div class="modal-header">
        <h2 id="userModalTitle" class="modal-title">Cadastrar Novo Usuário</h2>
        <button class="modal-close" data-close-modal="userModal">&times;</button>
      </div>

      <div class="modal-body">
        <div id="userModalAlert" class="alert alert-danger hidden" style="margin-bottom: 1rem;"></div>
        
        <div id="conflictAlertBox" class="alert alert-warning hidden" style="margin-bottom: 1rem; border-left: 4px solid var(--color-accent-orange);">
          <div style="font-weight: 700; color: #b45309; margin-bottom: 0.5rem;">
            Conflito de Restrição de Escopo
          </div>
          <div id="conflictAlertMsg" style="font-size: 0.85rem; margin-bottom: 0.5rem;"></div>
          <ul id="conflictSubordinatesList" style="font-size: 0.8rem; padding-left: 1.5rem; max-height: 150px; overflow-y: auto;"></ul>
        </div>

        <form id="userForm">
          <div class="grid" style="grid-template-columns: 1fr 1fr; gap: 1rem;">
            <div class="form-group">
              <label class="form-label" for="formUserName">Nome Completo <span class="required">*</span></label>
              <input type="text" id="formUserName" class="form-control" required>
            </div>
            <div class="form-group">
              <label class="form-label" for="formUserEmail">E-mail <span class="required">*</span></label>
              <input type="email" id="formUserEmail" class="form-control" required>
            </div>
          </div>

          <div class="grid" style="grid-template-columns: 1fr 1fr; gap: 1rem; margin-top: 1rem;">
            <div class="form-group">
              <label class="form-label" for="formUserHierarchy">Hierarquia do Usuário <span class="required">*</span></label>
              <select id="formUserHierarchy" class="form-select" required></select>
            </div>
            <div class="form-group" style="display: flex; align-items: center; padding-top: 1.5rem; gap: 1rem;">
              <label style="display:flex; align-items:center; gap:0.5rem; cursor:pointer;">
                <input type="checkbox" id="formUserActive" checked style="width:16px; height:16px;">
                <span class="text-sm font-semibold text-main">Usuário Ativo</span>
              </label>
            </div>
          </div>

          <div id="podeCriarContainer" class="form-group hidden" style="margin-top: 0.5rem; padding: 0.75rem; background: var(--bg-card); border: 1px solid var(--border-color); border-radius: 8px;">
            <label style="display:flex; align-items:center; gap:0.5rem; cursor:pointer;">
              <input type="checkbox" id="formUserPodeCriar" style="width:16px; height:16px;">
              <div style="display:flex; flex-direction:column;">
                <span class="text-sm font-semibold text-main">Permitir criar e gerenciar usuários</span>
              </div>
            </label>
          </div>
          
          <div class="form-group" style="margin-top: 1.5rem;">
             <label class="form-label">Páginas Permitidas <span class="required">*</span></label>
             <div style="display: flex; gap: 1rem; flex-wrap: wrap; margin-top: 0.5rem;" id="paginasPermitidasCheckboxes">
                <label style="display:flex; align-items:center; gap:0.25rem;"><input type="checkbox" name="userPages" value="reports" checked> Visão Geral</label>
                <label style="display:flex; align-items:center; gap:0.25rem;"><input type="checkbox" name="userPages" value="paaeb" checked> PAAEB</label>
                <label style="display:flex; align-items:center; gap:0.25rem;"><input type="checkbox" name="userPages" value="data" checked> Dados</label>
             </div>
          </div>

          <div id="accessAssignmentContainer" style="margin-top: 1.5rem; padding-top: 1.5rem; border-top: 1px solid var(--border-color);">
            <h4 style="font-size: 0.95rem; font-weight: 700; margin-bottom: 0.5rem;">Escopo de Acesso</h4>
            
            <div class="grid" style="grid-template-columns: 1fr 1fr; gap: 1rem;">
              <div class="form-group">
                <label class="form-label">União</label>
                <select id="accessSelectUniao" class="form-select"><option value="">-- Selecione --</option></select>
              </div>
              <div class="form-group" id="assocSelectGroup">
                <label class="form-label">Associação</label>
                <select id="accessSelectAssoc" class="form-select"><option value="">-- Selecione --</option></select>
              </div>
            </div>

            <div class="form-group" id="escolaSelectGroup" style="margin-top: 1rem;">
              <label class="form-label">Escola</label>
              <select id="accessSelectEscola" class="form-select"><option value="">-- Selecione --</option></select>
            </div>

            <button type="button" id="btnAddAccessTag" class="btn btn-outline w-full" style="margin-top: 1rem; justify-content: center;">Adicionar Unidade</button>

            <div style="margin-top: 1.5rem;">
              <div class="text-sm font-semibold mb-2">Unidades Atribuídas:</div>
              <div id="assignedAccessTagsList" class="flex flex-wrap gap-2" style="background: var(--bg-card); padding: 1rem; border: 1px dashed var(--border-color); border-radius: 8px; min-height: 60px;"></div>
            </div>
          </div>
        </form>
      </div>

      <div class="modal-footer">
        <button type="button" class="btn btn-outline" data-close-modal="userModal">Cancelar</button>
        <button type="submit" form="userForm" id="btnSaveUser" class="btn btn-primary">Salvar Usuário</button>
      </div>
    </div>
  </div>

  <!-- ================= TEMP PASSWORD MODAL ================= -->
  <div class="modal" id="tempPasswordModal">
    <div class="modal-content" style="max-width: 400px; text-align: center;">
      <div class="modal-header" style="border-bottom: none; padding-bottom: 0;">
        <h2 class="modal-title" style="width: 100%;">Senha Temporária</h2>
      </div>
      <div class="modal-body">
        <p style="margin-bottom: 1rem; color: var(--text-muted);">
          A senha temporária para <strong><span id="tempPasswordUserName"></span></strong> foi gerada.
        </p>
        <div style="background: var(--bg-card); padding: 1rem; border: 2px dashed var(--border-color); border-radius: 8px; margin-bottom: 1.5rem;">
          <span id="displayTempPassword" style="font-size: 1.5rem; font-family: monospace; font-weight: 700; color: var(--color-primary);"></span>
        </div>
        <button id="btnCopyTempPassword" class="btn btn-primary w-full" style="justify-content: center; margin-bottom: 0.5rem;">Copiar Senha</button>
        <button type="button" class="btn btn-outline w-full" data-close-modal="tempPasswordModal" style="justify-content: center;">Fechar</button>
      </div>
    </div>
  </div>
"""

if 'id="userModal"' not in html:
    idx = html.rfind('</body>')
    if idx != -1:
        html = html[:idx] + modal_code + '\n' + html[idx:]
        with open('Frontend/index.html', 'w', encoding='utf-8') as f:
            f.write(html)
        print('Modals added.')
    else:
        print('</body> not found!')
else:
    print('Modals already exist.')
