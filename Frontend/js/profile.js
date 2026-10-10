const Profile = {
  options: null,
  init() {
    document.querySelectorAll('[data-profile-tab]').forEach(button => {
      button.addEventListener('click', () => this.showTab(button.dataset.profileTab));
    });
    for (const id of ['dataFilterUniao', 'dataFilterAssoc']) {
      document.getElementById(id)?.addEventListener('change', () => this.updateInstitutionFilters(id));
    }
    document.getElementById('clearDataFilters')?.addEventListener('click', () => {
      for (const id of ['dataFilterUniao','dataFilterAssoc','dataFilterEscola','dataFilterAno','dataFilterBimestre']) {
        document.getElementById(id).value = '';
      }
      this.updateInstitutionFilters('dataFilterUniao');
    });
    document.querySelectorAll('[data-export-table]').forEach(button => {
      button.addEventListener('click', () => this.export(button));
    });

    document.querySelectorAll('[data-data-tab]').forEach(tab => {
      tab.addEventListener('click', () => {
        const target = tab.dataset.dataTab;
        document.querySelectorAll('[data-data-tab]').forEach(t => t.classList.remove('active'));
        tab.classList.add('active');
        document.getElementById('dataSimuladosContent')?.classList.toggle('hidden', target !== 'simulados');
        document.getElementById('dataPaaebContent')?.classList.toggle('hidden', target !== 'paaeb');
        document.getElementById('dataEscolasContent')?.classList.toggle('hidden', target !== 'escolas');
      });
    });
  },
  showTab(tab) {
    if (tab === 'data') {
      App.navigateTo('data');
      return;
    }
    
    const user = API.getStoredUser() || {};
    if (tab === 'users' && user.hierarquia !== 'Master' && !user.pode_criar_usuario) {
      return; // Do not allow access
    }
    if (tab === 'schools' && user.hierarquia !== 'Master') return;

    document.getElementById('profileOverview').classList.toggle('hidden', tab !== 'overview');
    document.getElementById('profileUsers')?.classList.toggle('hidden', tab !== 'users');
    document.getElementById('profileSchools')?.classList.toggle('hidden', tab !== 'schools');
    if (tab === 'users') Users.loadUsers();
    if (tab === 'schools') Schools.loadSchools();
    document.querySelectorAll('[data-profile-tab]').forEach(button => {
      const active = button.dataset.profileTab === tab;
      button.classList.toggle('active', active);
      button.setAttribute('aria-selected', String(active));
    });
  },
  async load() {
    const user = API.getStoredUser() || {};
    document.getElementById('profileName').textContent = user.nome_completo_usuario || 'Usuário';
    document.getElementById('profileEmail').textContent = user.email || '';
    let displayRole = ({Master:'Master',Administrador:'Administrador',uniao:'União',associacao:'Associação',escola:'Escola'})[user.hierarquia] || '—';
    if (user.hierarquia !== 'Master' && user.acessos && user.acessos.length > 0) {
        const acc = user.acessos[0];
        if (user.hierarquia === 'uniao' && acc.sigla_uniao) {
            displayRole = acc.sigla_uniao;
        } else if (user.hierarquia === 'associacao' && acc.sigla_associacao) {
            displayRole = acc.sigla_associacao;
        } else if (user.hierarquia === 'escola' && acc.nome_escola) {
            displayRole = acc.nome_escola;
        }
    }
    document.getElementById('profileRole').textContent = displayRole;
    const rolePill = document.getElementById('profileRoleBadge');
    if (rolePill) rolePill.textContent = document.getElementById('profileRole').textContent;
    const parts = (user.nome_completo_usuario || '').trim().split(/\s+/).filter(Boolean);
    const avatar = document.getElementById('profileAvatar');
    avatar.textContent = `${parts[0]?.[0] || 'P'}${parts.length > 1 ? parts.at(-1)[0] : ''}`.toUpperCase();
    if (user.foto_perfil) {
      avatar.textContent = '';
      const img = document.createElement('img'); img.src = user.foto_perfil; img.alt = '';
      avatar.appendChild(img);
    }
    
    // Hide 'Usuários e acessos' tab if user cannot create users
    const tabUsers = document.getElementById('profileTabUsers');
    if (tabUsers) {
      tabUsers.style.display = user.hierarquia === 'Master' || user.pode_criar_usuario ? 'inline-block' : 'none';
    }
    Schools.updatePermission();
    
    if (this.options) return;
    const status = document.getElementById('dataExportStatus');
    status.textContent = 'Carregando instituições e períodos disponíveis…';
    status.className = 'report-status';
    try {
      this.options = await API.getExportOptions();
      this.fillSelect('dataFilterUniao', [...new Set(this.options.entidades.map(x => x.uniao).filter(Boolean))].sort(), 'Todas as uniões');
      this.fillSelect('dataFilterAno', this.options.anos, 'Todos os anos');
      this.fillSelect('dataFilterBimestre', this.options.bimestres, 'Todos os bimestres');
      this.updateInstitutionFilters('init');
            document.getElementById('profileSchoolCount').textContent = this.options.entidades.length.toLocaleString('pt-BR');
      
      const schoolList = document.getElementById('profileSchoolList');
      if (schoolList && this.options.entidades.length > 0) {
        schoolList.style.display = 'block';
        
        // Agrupar por Uniao -> Associacao -> Escola
        const tree = {};
        this.options.entidades.forEach(e => {
            const u = e.uniao || 'Sem União';
            const a = e.associacao || 'Sem Associação';
            const s = e.escola;
            
            if (!tree[u]) tree[u] = {};
            if (!tree[u][a]) tree[u][a] = [];
            if (s) tree[u][a].push(s);
        });
        
        let listHtml = '<ul style="list-style:none; padding:0; margin:0;">';
        for (const uniao of Object.keys(tree).sort()) {
            listHtml += `<li style="font-weight:bold; margin-top:0.5rem; color:var(--color-primary);">${uniao}</li>`;
            listHtml += '<ul style="list-style:none; padding-left:1rem; margin:0;">';
            for (const assoc of Object.keys(tree[uniao]).sort()) {
                listHtml += `<li style="font-weight:600; margin-top:0.25rem; color:var(--text-main);">${assoc}</li>`;
                const escolas = tree[uniao][assoc].sort();
                if (escolas.length > 0) {
                    listHtml += '<ul style="list-style:disc; padding-left:1.5rem; margin:0; color:var(--text-muted);">';
                    escolas.forEach(esc => {
                        listHtml += `<li>${esc}</li>`;
                    });
                    listHtml += '</ul>';
                }
            }
            listHtml += '</ul>';
        }
        listHtml += '</ul>';
        
        let headerHtml = `
          <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--border-color); padding-bottom: 0.5rem; margin-bottom: 0.5rem;">
            <span style="font-weight: 600; color: var(--text-main);">Lista de Instituições</span>
            <button type="button" class="btn btn-outline" style="padding: 0.25rem 0.5rem; font-size: 0.75rem;" onclick="document.getElementById('schoolListModal').classList.add('active')">
              Expandir
            </button>
          </div>
        `;
        
        schoolList.innerHTML = headerHtml + listHtml;
        const modalBody = document.getElementById('schoolListModalBody');
        if (modalBody) {
          modalBody.innerHTML = listHtml;
        }
      } else if (schoolList) {
        schoolList.style.display = 'none';
      }

      const unique = key => [...new Set(this.options.entidades.map(x => x[key]).filter(Boolean))];
      document.getElementById('detailUniaoDropdown').textContent = unique('uniao').length === 1 ? unique('uniao')[0] : `${unique('uniao').length} uniões`;
      document.getElementById('detailAssociacaoDropdown').textContent = unique('associacao').length === 1 ? unique('associacao')[0] : `${unique('associacao').length} associações`;
      document.getElementById('detailEscolaDropdown').textContent = this.options.entidades.length === 1 ? this.options.entidades[0].escola : `${this.options.entidades.length} escolas`;
      status.className = 'report-status hidden';
    } catch (error) {
      status.textContent = 'Não foi possível carregar os filtros: ' + error.message;
      status.className = 'report-status error';
    }
  },
  fillSelect(id, values, placeholder, keep = '') {
    const select = document.getElementById(id);
    select.replaceChildren(new Option(placeholder, ''), ...values.map(value => new Option(value, value)));
    select.value = keep;
  },
  updateInstitutionFilters(changed) {
    if (!this.options) return;
    const entities = this.options.entidades;
    const union = document.getElementById('dataFilterUniao').value;
    const assoc = document.getElementById('dataFilterAssoc');
    const oldAssoc = assoc.value;
    const oldSchool = document.getElementById('dataFilterEscola').value;
    this.fillSelect('dataFilterAssoc', [...new Set(entities.filter(x => !union || x.uniao === union).map(x => x.associacao).filter(Boolean))].sort(), 'Todas as associações', changed === 'dataFilterUniao' ? '' : oldAssoc);
    const schools = entities.filter(x => (!union || x.uniao === union) && (!assoc.value || x.associacao === assoc.value));
    const schoolSelect = document.getElementById('dataFilterEscola');
    schoolSelect.replaceChildren(new Option('Todas as escolas', ''), ...schools.map(x => new Option(x.escola, x.id_escolas)));
    schoolSelect.value = ['dataFilterUniao','dataFilterAssoc'].includes(changed) ? '' : oldSchool;
  },
  filters() {
    return {
      uniao: document.getElementById('dataFilterUniao').value,
      associacao: document.getElementById('dataFilterAssoc').value,
      escola: document.getElementById('dataFilterEscola').value,
      ano: document.getElementById('dataFilterAno').value,
      bimestre: document.getElementById('dataFilterBimestre').value,
    };
  },
  async export(button) {
    const table = button.dataset.exportTable;
    if (table && table.startsWith('paaeb_')) {
      if (typeof App !== 'undefined') {
        return App.showToast('Em breve', 'info');
      }
      return;
    }
    if (!this.options) return App.showToast('Aguarde o carregamento dos filtros.', 'warning');
    button.disabled = true;
    const label = button.innerHTML;
    button.textContent = 'Preparando arquivo…';
    try {
      await API.exportTable(button.dataset.exportTable, this.filters());
      App.showToast('Arquivo CSV preparado com sucesso.', 'success');
    } catch (error) {
      App.showToast(error.message, 'danger');
    } finally {
      button.disabled = false;
      button.innerHTML = label;
    }
  }
};
