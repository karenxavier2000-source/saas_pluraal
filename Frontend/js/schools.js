const Schools = {
  rows: [],
  loaded: false,

  init() {
    document.getElementById('btnNewSchool')?.addEventListener('click', () => this.openForm());
    document.getElementById('schoolSearch')?.addEventListener('input', () => this.render());
    document.getElementById('schoolTableBody')?.addEventListener('click', event => {
      const button = event.target.closest('button[data-school-action]');
      if (!button) return;
      const row = this.rows.find(item => String(item.id_escolas) === button.dataset.id);
      if (!row) return;
      if (button.dataset.schoolAction === 'edit') this.openForm(row);
      if (button.dataset.schoolAction === 'delete') this.remove(row);
    });
    this.updatePermission();
  },

  updatePermission() {
    const master = API.getStoredUser()?.hierarquia === 'Master';
    const tab = document.getElementById('profileTabSchools');
    if (tab) tab.style.display = master ? 'inline-block' : 'none';
    if (!master) {
      this.rows = [];
      this.loaded = false;
    }
  },

  esc(value) {
    return String(value ?? '').replace(/[&<>"']/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
  },

  async loadSchools() {
    if (API.getStoredUser()?.hierarquia !== 'Master') return;
    const status = document.getElementById('schoolStatus');
    status.textContent = 'Carregando escolas…';
    status.className = 'report-status';
    try {
      this.rows = await API.request('/api/schools', {cache: 'no-store'});
      this.loaded = true;
      this.render();
      status.className = 'report-status hidden';
    } catch (error) {
      status.textContent = 'Não foi possível carregar escolas: ' + error.message;
      status.className = 'report-status error';
    }
  },

  render() {
    const term = (document.getElementById('schoolSearch')?.value || '').toLocaleLowerCase('pt-BR');
    const rows = this.rows.filter(row => ['UNIAO','SIGLA_UNIAO','ASSOCIACAO','SIGLA_ASSOCIACAO','ESCOLA']
      .some(field => String(row[field] || '').toLocaleLowerCase('pt-BR').includes(term)));
    const body = document.getElementById('schoolTableBody');
    body.innerHTML = rows.length ? rows.map(row => `<tr>
      <td>${this.esc(row.id_escolas)}</td><td>${this.esc(row.UNIAO || '—')}</td>
      <td>${this.esc(row.SIGLA_UNIAO || '—')}</td><td>${this.esc(row.ASSOCIACAO || '—')}</td>
      <td>${this.esc(row.SIGLA_ASSOCIACAO || '—')}</td><td>${this.esc(row.ESCOLA || '—')}</td>
      <td class="flex gap-2"><button type="button" class="btn btn-outline btn-sm" data-school-action="edit" data-id="${row.id_escolas}">Editar</button>
      <button type="button" class="btn btn-outline btn-sm" data-school-action="delete" data-id="${row.id_escolas}">Excluir</button></td>
    </tr>`).join('') : '<tr><td colspan="7" class="empty-state">Nenhuma escola encontrada.</td></tr>';
  },

  options(field, selected = {}) {
    return [...new Set(this.rows.filter(row => Object.entries(selected).every(([key, value]) => row[key] === value))
      .map(row => row[field]).filter(Boolean))].sort((a, b) => a.localeCompare(b, 'pt-BR'));
  },

  fillSelect(id, field, selected, value = '') {
    const element = document.getElementById(id);
    const values = this.options(field, selected);
    element.replaceChildren(new Option('Selecione', ''), ...values.map(item => new Option(item, item)));
    element.value = value;
  },

  updateFormOptions(changed, saved = {}) {
    const values = {
      UNIAO: document.getElementById('schoolFormUniao').value,
      SIGLA_UNIAO: document.getElementById('schoolFormSiglaUniao').value,
      ASSOCIACAO: document.getElementById('schoolFormAssociacao').value,
      SIGLA_ASSOCIACAO: document.getElementById('schoolFormSiglaAssociacao').value,
      ...saved
    };
    if (changed === 'UNIAO') Object.assign(values, {SIGLA_UNIAO:'', ASSOCIACAO:'', SIGLA_ASSOCIACAO:''});
    if (changed === 'SIGLA_UNIAO') Object.assign(values, {ASSOCIACAO:'', SIGLA_ASSOCIACAO:''});
    if (changed === 'ASSOCIACAO') values.SIGLA_ASSOCIACAO = '';
    this.fillSelect('schoolFormUniao', 'UNIAO', {}, values.UNIAO);
    this.fillSelect('schoolFormSiglaUniao', 'SIGLA_UNIAO', {UNIAO:values.UNIAO}, values.SIGLA_UNIAO);
    this.fillSelect('schoolFormAssociacao', 'ASSOCIACAO', {UNIAO:values.UNIAO, SIGLA_UNIAO:values.SIGLA_UNIAO}, values.ASSOCIACAO);
    this.fillSelect('schoolFormSiglaAssociacao', 'SIGLA_ASSOCIACAO', {UNIAO:values.UNIAO, SIGLA_UNIAO:values.SIGLA_UNIAO, ASSOCIACAO:values.ASSOCIACAO}, values.SIGLA_ASSOCIACAO);
  },

  openForm(row = null) {
    if (API.getStoredUser()?.hierarquia !== 'Master') return;
    if (!this.loaded) return App.showToast('Aguarde o carregamento das escolas.', 'warning');
    let modal = document.getElementById('schoolFormModal');
    if (!modal) {
      document.body.insertAdjacentHTML('beforeend', `<div id="schoolFormModal" class="modal-backdrop" role="dialog" aria-modal="true" aria-labelledby="schoolFormTitle">
        <div class="modal school-form-dialog" style="max-width: 560px;"><div class="modal-header"><h2 id="schoolFormTitle" class="modal-title"></h2><button id="schoolFormClose" type="button" class="modal-close" aria-label="Fechar">&times;</button></div>
        <form id="schoolForm"><div class="modal-body"><input id="schoolFormId" type="hidden">
          <div class="form-group"><label for="schoolFormUniao" class="form-label">União</label><select id="schoolFormUniao" class="form-select" required></select></div>
          <div class="form-group"><label for="schoolFormSiglaUniao" class="form-label">Sigla união</label><select id="schoolFormSiglaUniao" class="form-select" required></select></div>
          <div class="form-group"><label for="schoolFormAssociacao" class="form-label">Associação</label><select id="schoolFormAssociacao" class="form-select" required></select></div>
          <div class="form-group"><label for="schoolFormSiglaAssociacao" class="form-label">Sigla associação</label><select id="schoolFormSiglaAssociacao" class="form-select" required></select></div>
          <div class="form-group"><label for="schoolFormNome" class="form-label">Escola</label><input id="schoolFormNome" class="form-control" type="text" required maxlength="255"></div>
          <p id="schoolFormError" class="report-status error hidden" role="alert"></p></div>
          <div class="modal-footer"><button id="schoolFormCancel" type="button" class="btn btn-outline">Cancelar</button><button id="schoolFormSave" type="submit" class="btn btn-primary">Salvar</button></div>
        </form></div></div>`);
      modal = document.getElementById('schoolFormModal');
      for (const id of ['schoolFormClose','schoolFormCancel']) document.getElementById(id).addEventListener('click', () => modal.classList.remove('active'));
      modal.addEventListener('click', event => { if (event.target === modal) modal.classList.remove('active'); });
      for (const [id, field] of [['schoolFormUniao','UNIAO'],['schoolFormSiglaUniao','SIGLA_UNIAO'],['schoolFormAssociacao','ASSOCIACAO']]) {
        document.getElementById(id).addEventListener('change', () => this.updateFormOptions(field));
      }
      document.getElementById('schoolForm').addEventListener('submit', event => { event.preventDefault(); this.save(); });
    }
    document.getElementById('schoolForm').reset();
    document.getElementById('schoolFormTitle').textContent = row ? 'Editar escola' : 'Adicionar escola';
    document.getElementById('schoolFormId').value = row?.id_escolas || '';
    document.getElementById('schoolFormNome').value = row?.ESCOLA || '';
    document.getElementById('schoolFormError').classList.add('hidden');
    this.updateFormOptions('', row || {});
    modal.classList.add('active');
  },

  async save() {
    const id = document.getElementById('schoolFormId').value;
    const data = {
      UNIAO: document.getElementById('schoolFormUniao').value,
      SIGLA_UNIAO: document.getElementById('schoolFormSiglaUniao').value,
      ASSOCIACAO: document.getElementById('schoolFormAssociacao').value,
      SIGLA_ASSOCIACAO: document.getElementById('schoolFormSiglaAssociacao').value,
      ESCOLA: document.getElementById('schoolFormNome').value.trim()
    };
    const button = document.getElementById('schoolFormSave');
    const error = document.getElementById('schoolFormError');
    button.disabled = true;
    try {
      await API.request(id ? `/api/schools/${id}` : '/api/schools', {method:id ? 'PUT' : 'POST', body:data});
      document.getElementById('schoolFormModal').classList.remove('active');
      Profile.options = null;
      Reports.catalog = [];
      await this.loadSchools();
      App.showToast(id ? 'Escola atualizada.' : 'Escola adicionada.', 'success');
    } catch (cause) {
      error.textContent = cause.message;
      error.classList.remove('hidden');
    } finally {
      button.disabled = false;
    }
  },

  async remove(row) {
    if (!confirm(`Excluir a escola "${row.ESCOLA}"?`)) return;
    try {
      await API.request(`/api/schools/${row.id_escolas}`, {method:'DELETE'});
      Profile.options = null;
      Reports.catalog = [];
      await this.loadSchools();
      App.showToast('Escola excluída.', 'success');
    } catch (error) {
      App.showToast('Não foi possível excluir: ' + error.message, 'danger');
    }
  }
};
