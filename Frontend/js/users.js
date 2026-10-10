// User Management and Delegation UI Logic
const Users = {
  allUsers: [],
  capabilities: null,
  currentEditingId: null,
  selectedAccesses: [],

  init() {
    this.bindEvents();
  },

  bindEvents() {
    // Search input
    const searchInput = document.getElementById('userSearchInput');
    if (searchInput) {
      searchInput.addEventListener('input', () => this.filterUsersTable());
    }

    // Hierarchy filter dropdown
    const filterHierarchy = document.getElementById('filterUserHierarchy');
    if (filterHierarchy) {
      filterHierarchy.addEventListener('change', () => this.filterUsersTable());
    }

    // New user button
    const newBtn = document.getElementById('btnNewUser');
    if (newBtn) {
      newBtn.addEventListener('click', () => this.openCreateUserModal());
    }

    // Modal close buttons
    document.querySelectorAll('[data-close-modal]').forEach(btn => {
      btn.addEventListener('click', () => {
        const modalId = btn.getAttribute('data-close-modal');
        this.closeModal(modalId);
      });
    });

    // Form submission
    const userForm = document.getElementById('userForm');
    if (userForm) {
      userForm.addEventListener('submit', (e) => this.handleSaveUser(e));
    }
    document.getElementById('formUserUnlimited')?.addEventListener('change', () => this.updateExpirationControl());

    // Target hierarchy change in form
    const formHierarchy = document.getElementById('formUserHierarchy');
    if (formHierarchy) {
      formHierarchy.addEventListener('change', () => this.handleHierarchyChangeInForm());
    }

    // Cascading dropdowns for adding accesses
    const selUniao = document.getElementById('accessSelectUniao');
    const selAssoc = document.getElementById('accessSelectAssoc');
    const btnAddAccess = document.getElementById('btnAddAccessTag');

    if (selUniao) {
      selUniao.addEventListener('change', () => this.populateCascadingAssocsAndSchools());
    }
    if (selAssoc) {
      selAssoc.addEventListener('change', () => this.populateCascadingSchools());
    }
    if (btnAddAccess) {
      btnAddAccess.addEventListener('click', () => this.handleAddAccessTag());
    }

    // Copy temporary password button
    const copyBtn = document.getElementById('btnCopyTempPassword');
    if (copyBtn) {
      copyBtn.addEventListener('click', () => {
        const pwText = document.getElementById('displayTempPassword').textContent;
        navigator.clipboard.writeText(pwText).then(() => {
          App.showToast('Senha copiada para a área de transferência!', 'success');
        });
      });
    }
  },

  async loadUsers() {
    const tableBody = document.getElementById('usersTableBody');
    tableBody.innerHTML = `<tr><td colspan="7" class="text-center py-4 text-muted">Carregando usuários...</td></tr>`;

    try {
      // Load capabilities first or concurrently
      if (!this.capabilities) {
        this.capabilities = await API.getHierarchyCapabilities();
      }

      // Check if user has button to create users
      const newBtn = document.getElementById('btnNewUser');
      if (newBtn) {
        if (this.capabilities.pode_criar_usuario || this.capabilities.usuario_hierarquia === 'Master') {
          newBtn.classList.remove('hidden');
        } else {
          newBtn.classList.add('hidden');
        }
      }

      this.allUsers = await API.getUsers();
      this.renderUsersTable(this.allUsers);
    } catch (err) {
      tableBody.innerHTML = `<tr><td colspan="7" class="text-center py-4 text-danger">Erro ao carregar usuários: ${err.message}</td></tr>`;
      App.showToast('Erro ao carregar lista de usuários: ' + err.message, 'danger');
    }
  },

  filterUsersTable() {
    const term = (document.getElementById('userSearchInput').value || '').toLowerCase();
    const hier = document.getElementById('filterUserHierarchy').value;

    const filtered = this.allUsers.filter(u => {
      const matchTerm = u.nome_completo_usuario.toLowerCase().includes(term) || u.email.toLowerCase().includes(term);
      const matchHier = !hier || u.hierarquia === hier;
      return matchTerm && matchHier;
    });

    this.renderUsersTable(filtered);
  },

  renderUsersTable(users) {
    const tableBody = document.getElementById('usersTableBody');
    if (!users || users.length === 0) {
      tableBody.innerHTML = `<tr><td colspan="7" class="text-center py-4 text-muted">Nenhum usuário encontrado.</td></tr>`;
      return;
    }

    const currentLoggedUser = API.getStoredUser() || {};
    const isMaster = (currentLoggedUser.hierarquia === 'Master');

    tableBody.innerHTML = users.map(u => {
      const hierBadgeClass = {
        'Master': 'badge-master',
        'Administrador': 'badge-master',
        'uniao': 'badge-uniao',
        'associacao': 'badge-associacao',
        'escola': 'badge-escola'
      }[u.hierarquia] || 'badge-inactive';

      const today = new Date();
      const localToday = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`;
      const expired = u.data_expiracao_login && String(u.data_expiracao_login).slice(0, 10) < localToday;
      const statusBadge = expired
        ? `<span class="badge badge-inactive">Prazo expirado</span>`
        : u.ativo
        ? `<span class="badge badge-active">Ativo</span>`
        : `<span class="badge badge-inactive">Inativo</span>`;

      const permBadge = u.pode_criar_usuario
        ? `<span class="badge badge-success">Sim</span>`
        : `<span class="badge badge-inactive">Não</span>`;

      // Format accesses summary
      let accessesSummary = '—';
      if (u.hierarquia === 'Master' || u.hierarquia === 'Administrador') {
        accessesSummary = '<strong style="color: var(--color-primary)">Acesso Global Total</strong>';
      } else if (u.acessos && u.acessos.length > 0) {
        accessesSummary = u.acessos.map(a => {
          if (a.tipo === 'uniao') return `<span class="badge badge-uniao">${a.sigla_uniao}</span>`;
          if (a.tipo === 'associacao') return `<span class="badge badge-associacao">${a.sigla_associacao}</span>`;
          if (a.tipo === 'escola') return `<span class="badge badge-escola">${a.nome_escola || ('Escola ID ' + a.id_escolas)}</span>`;
          return '';
        }).join(' ');
      }

      // Can reset password? Master or creator of target user
      const canReset = isMaster || (u.criado_por_usuario_id === currentLoggedUser.id_usuario);
      // Can edit? Master or creator or self (with restricted fields)
      const canEdit = isMaster || (u.criado_por_usuario_id === currentLoggedUser.id_usuario); // Restringido: não-master não pode editar a si mesmo

      let displayRole = u.hierarquia;
      if (u.hierarquia !== 'Master' && u.acessos && u.acessos.length > 0) {
          const acc = u.acessos[0];
          if (u.hierarquia === 'uniao' && acc.sigla_uniao) displayRole = acc.sigla_uniao;
          else if (u.hierarquia === 'associacao' && acc.sigla_associacao) displayRole = acc.sigla_associacao;
          else if (u.hierarquia === 'escola' && acc.nome_escola) displayRole = acc.nome_escola;
      }

      return `
        <tr>
          <td>
            <div class="font-semibold text-main">${this.escapeHtml(u.nome_completo_usuario)}</div>
            <div class="text-xs text-muted">Criado em: ${new Date(u.criado_em).toLocaleDateString('pt-BR')}</div>
            ${u.data_expiracao_login ? `<div class="text-xs text-muted">Acesso até: ${new Date(String(u.data_expiracao_login).slice(0, 10) + 'T12:00:00').toLocaleDateString('pt-BR')}</div>` : ''}
          </td>
          <td>${this.escapeHtml(u.email)}</td>
          <td><span class="badge ${hierBadgeClass}">${this.escapeHtml(displayRole)}</span></td>
          <td>${accessesSummary}</td>
          <td>${permBadge}</td>
          <td>${statusBadge}</td>
          <td class="text-right">
            <div class="flex items-center justify-center gap-2">
              ${canEdit ? `
                <button class="btn btn-outline btn-sm" onclick="Users.openEditUserModal(${u.id_usuario})" title="Editar Usuário">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path></svg>
                  Editar
                </button>
              ` : ''}
              ${canReset ? `
                <button class="btn btn-outline btn-sm" onclick="Users.handleResetPassword(${u.id_usuario}, '${this.escapeHtml(u.nome_completo_usuario)}')" title="Redefinir Senha">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 2l-2 2m-7.61 7.61a5.5 5.5 0 1 1-7.778 7.778 5.5 5.5 0 0 1 7.777-7.777zm0 0L15.5 7.5m0 0l3 3L22 7l-3-3m-3.5 3.5L19 4"></path></svg>
                  Reset Senha
                </button>
              ` : ''}
            </div>
          </td>
        </tr>
      `;
    }).join('');
  },

  async openCreateUserModal() {
    this.currentEditingId = null;
    this.selectedAccesses = [];

    document.getElementById('userModalTitle').textContent = 'Cadastrar Novo Usuário';
    document.getElementById('userModalAlert').classList.add('hidden');
    document.getElementById('conflictAlertBox').classList.add('hidden');
    document.getElementById('userForm').reset();
    this.updateExpirationControl();

    await this.setupHierarchyAndAccessSelectors();
    this.handleHierarchyChangeInForm();
    this.renderAccessTags();
    this.openModal('userModal');
  },

  async openEditUserModal(userId) {
    if (!userId || isNaN(userId)) {
      App.showToast('ID de usuário inválido.', 'warning');
      return;
    }
    this.currentEditingId = userId;
    this.selectedAccesses = [];

    document.getElementById('userModalTitle').textContent = 'Editar Usuário';
    document.getElementById('userModalAlert').classList.add('hidden');
    document.getElementById('conflictAlertBox').classList.add('hidden');

    try {
      const user = await API.getUser(userId);
      await this.setupHierarchyAndAccessSelectors(user);

      document.getElementById('formUserName').value = user.nome_completo_usuario;
      document.getElementById('formUserEmail').value = user.email;
      document.getElementById('formUserActive').checked = user.ativo;
      document.getElementById('formUserHierarchy').value = user.hierarquia;
      const expiration = user.data_expiracao_login ? String(user.data_expiracao_login).slice(0, 10) : '';
      document.getElementById('formUserUnlimited').checked = !expiration;
      document.getElementById('formUserExpirationDate').value = expiration;
      this.updateExpirationControl();

      if (document.getElementById('formUserPodeCriar')) {
        document.getElementById('formUserPodeCriar').checked = user.pode_criar_usuario;
      }
      document.getElementById('formUserLimiteCriacao').value = user.limite_criacao_usuarios ?? '';
      if (document.getElementById('formUserPodeSimular')) {
        document.getElementById('formUserPodeSimular').checked = user.pode_simular_visao;
      }
      document.getElementById('limiteCriacaoContainer').style.display = user.pode_criar_usuario ? 'block' : 'none';
      if (document.getElementById('formUserPodeCadastrarEscola')) {
        document.getElementById('formUserPodeCadastrarEscola').checked = user.pode_cadastrar_escola || false;
      }

      // Populate accesses
      if (user.acessos) {
        this.selectedAccesses = user.acessos.map(a => ({
          tipo: a.tipo,
          sigla_uniao: a.sigla_uniao,
          sigla_associacao: a.sigla_associacao,
          id_escolas: a.id_escolas,
          label: a.tipo === 'uniao' ? `União: ${a.sigla_uniao}`
               : a.tipo === 'associacao' ? `Assoc: ${a.sigla_associacao} (${a.sigla_uniao})`
               : `${a.nome_escola || 'Escola'} (${a.sigla_associacao || ''})`
        }));
      }

      // Populate pages
      const paginas = user.paginas_permitidas || [];
      document.querySelectorAll('input[name="userPages"]').forEach(cb => {
        cb.checked = paginas.includes(cb.value);
      });

      this.handleHierarchyChangeInForm();
      this.renderAccessTags();
      this.openModal('userModal');
    } catch (err) {
      App.showToast('Erro ao carregar dados do usuário: ' + err.message, 'danger');
    }
  },

  async setupHierarchyAndAccessSelectors(editingUser = null) {
    if (!this.capabilities) {
      this.capabilities = await API.getHierarchyCapabilities();
    }

    const currentLoggedUser = API.getStoredUser() || {};
    const isMaster = (currentLoggedUser.hierarquia === 'Master');
    const isEditingSelf = editingUser && (editingUser.id_usuario === currentLoggedUser.id_usuario);

    // Hierarchy dropdown options (restricted strictly to allowed target hierarchies)
    const chkCriar = document.getElementById('formUserPodeCriar');
    chkCriar.onchange = (e) => {
      document.getElementById('limiteCriacaoContainer').style.display = e.target.checked ? 'block' : 'none';
    };
    document.getElementById('limiteCriacaoContainer').style.display = chkCriar.checked ? 'block' : 'none';
      const hierSelect = document.getElementById('formUserHierarchy');
    hierSelect.innerHTML = this.capabilities.allowed_target_hierarchies.map(h => {
      const names = { 'Master': 'Master (Acesso Total)', 'Administrador': 'Administrador', 'uniao': 'União', 'associacao': 'Associação', 'escola': 'Escola' };
      return `<option value="${h}">${names[h] || h}</option>`;
    }).join('');

    // If editing self and non-master, freeze hierarchy & accesses
    if (isEditingSelf && !isMaster) {
      hierSelect.disabled = true;
      document.getElementById('accessAssignmentContainer').classList.add('hidden');
    } else {
      hierSelect.disabled = false;
      document.getElementById('accessAssignmentContainer').classList.remove('hidden');
    }

    // Toggle pode_criar_usuario permission visibility: Only Master can grant this!
    const podeCriarContainer = document.getElementById('podeCriarContainer');
    if (this.capabilities.can_grant_pode_criar_usuario && (!isEditingSelf || isMaster)) {
      podeCriarContainer.classList.remove('hidden');
    } else {
      podeCriarContainer.classList.add('hidden');
    }
    document.getElementById('podeSimularContainer').classList.toggle('hidden', !this.capabilities.can_grant_pode_simular);

    // Populate União selector
    const selUniao = document.getElementById('accessSelectUniao');
    selUniao.innerHTML = `<option value="">-- Selecione a União --</option>` +
      this.capabilities.unioes.map(u => `<option value="${u.sigla_uniao}">${u.sigla_uniao} - ${u.nome_uniao || ''}</option>`).join('');

    this.populateCascadingAssocsAndSchools();
    
    // Filter available pages
    const availablePages = this.capabilities.paginas_permitidas || ['reports', 'paaeb', 'data']; // Default for Master or if not set
    document.querySelectorAll('input[name="userPages"]').forEach(cb => {
        const label = cb.closest('label');
        if (!availablePages.includes(cb.value)) {
            label.style.display = 'none';
            cb.checked = false;
        } else {
            label.style.display = 'flex';
        }
    });
  },

  handleHierarchyChangeInForm() {
    const hier = document.getElementById('formUserHierarchy').value;
    const accessContainer = document.getElementById('accessAssignmentContainer');
    const assocGroup = document.getElementById('assocSelectGroup');
    const escolaGroup = document.getElementById('escolaSelectGroup');

    if (hier === 'Master' || hier === 'Administrador') {
      accessContainer.classList.add('hidden');
    } else {
      accessContainer.classList.remove('hidden');
      if (hier === 'uniao') {
        assocGroup.classList.add('hidden');
        escolaGroup.classList.add('hidden');
      } else if (hier === 'associacao') {
        assocGroup.classList.remove('hidden');
        escolaGroup.classList.add('hidden');
      } else if (hier === 'escola') {
        assocGroup.classList.remove('hidden');
        escolaGroup.classList.remove('hidden');
      }
    }
  },

  updateExpirationControl() {
    const unlimited = document.getElementById('formUserUnlimited').checked;
    const group = document.getElementById('userExpirationDateGroup');
    const input = document.getElementById('formUserExpirationDate');
    group.classList.toggle('hidden', unlimited);
    input.required = !unlimited;
    input.disabled = unlimited;
    const today = new Date();
    input.min = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`;
    if (unlimited) input.value = '';
  },

  populateCascadingAssocsAndSchools() {
    const u = document.getElementById('accessSelectUniao').value;
    const selAssoc = document.getElementById('accessSelectAssoc');

    if (!u) {
      selAssoc.innerHTML = `<option value="">-- Selecione a Associação --</option>`;
      this.populateCascadingSchools();
      return;
    }

    // Filter associations by chosen union
    const assocs = this.capabilities.associacoes.filter(a => a.sigla_uniao === u);
    selAssoc.innerHTML = `<option value="">-- Selecione a Associação --</option>` +
      assocs.map(a => `<option value="${a.sigla_associacao}">${a.sigla_associacao} - ${a.nome_associacao || ''}</option>`).join('');

    this.populateCascadingSchools();
  },

  populateCascadingSchools() {
    const u = document.getElementById('accessSelectUniao').value;
    const a = document.getElementById('accessSelectAssoc').value;
    const selEscola = document.getElementById('accessSelectEscola');

    let escolas = this.capabilities.escolas;
    if (u) {
      escolas = escolas.filter(e => e.sigla_uniao === u);
    }
    if (a) {
      escolas = escolas.filter(e => e.sigla_associacao === a);
    }

    selEscola.innerHTML = `<option value="">-- Selecione a Escola --</option>` +
      escolas.map(e => `<option value="${e.id_escolas}">${e.escola}</option>`).join('');
  },

  handleAddAccessTag() {
    const hier = document.getElementById('formUserHierarchy').value;
    const u = document.getElementById('accessSelectUniao').value;
    const a = document.getElementById('accessSelectAssoc').value;
    const selEscola = document.getElementById('accessSelectEscola');
    const eid = selEscola.value ? parseInt(selEscola.value) : null;
    const eNome = selEscola.options[selEscola.selectedIndex]?.text || '';

    if (hier === 'uniao') {
      if (!u) {
        App.showToast('Por favor, selecione uma União.', 'warning');
        return;
      }
      if (this.selectedAccesses.some(item => item.tipo === 'uniao' && item.sigla_uniao === u)) {
        App.showToast('Esta união já foi adicionada.', 'info');
        return;
      }
      this.selectedAccesses.push({ tipo: 'uniao', sigla_uniao: u, label: `União: ${u}` });
    } else if (hier === 'associacao') {
      if (!u || !a) {
        App.showToast('Por favor, selecione a União e a Associação.', 'warning');
        return;
      }
      if (this.selectedAccesses.some(item => item.tipo === 'associacao' && item.sigla_uniao === u && item.sigla_associacao === a)) {
        App.showToast('Esta associação já foi adicionada.', 'info');
        return;
      }
      this.selectedAccesses.push({ tipo: 'associacao', sigla_uniao: u, sigla_associacao: a, label: `Assoc: ${a} (${u})` });
    } else if (hier === 'escola') {
      if (!eid) {
        App.showToast('Por favor, selecione uma Escola.', 'warning');
        return;
      }
      if (this.selectedAccesses.some(item => item.tipo === 'escola' && item.id_escolas === eid)) {
        App.showToast('Esta escola já foi adicionada.', 'info');
        return;
      }
      this.selectedAccesses.push({ tipo: 'escola', id_escolas: eid, sigla_uniao: u, sigla_associacao: a, label: `${eNome}` });
    }

    this.renderAccessTags();
  },

  renderAccessTags() {
    const list = document.getElementById('assignedAccessTagsList');
    if (!this.selectedAccesses || this.selectedAccesses.length === 0) {
      list.innerHTML = `<span class="text-xs text-muted">Nenhum acesso específico adicionado ainda.</span>`;
      return;
    }

    list.innerHTML = this.selectedAccesses.map((acc, idx) => `
      <div class="access-tag">
        <span>${this.escapeHtml(acc.label || `${acc.tipo}: ${acc.sigla_uniao || acc.id_escolas}`)}</span>
        <span class="access-tag-remove" onclick="Users.removeAccessTag(${idx})" title="Remover">&times;</span>
      </div>
    `).join('');
  },

  removeAccessTag(idx) {
    this.selectedAccesses.splice(idx, 1);
    this.renderAccessTags();
  },

  async handleSaveUser(e) {
    e.preventDefault();
    const alertBox = document.getElementById('userModalAlert');
    const conflictBox = document.getElementById('conflictAlertBox');
    const saveBtn = document.getElementById('btnSaveUser');

    alertBox.classList.add('hidden');
    conflictBox.classList.add('hidden');

    const nome = document.getElementById('formUserName').value.trim();
    const email = document.getElementById('formUserEmail').value.trim();
    const hierarquia = document.getElementById('formUserHierarchy').value;
    const ativo = document.getElementById('formUserActive').checked;
    const pode_criar_usuario = document.getElementById('formUserPodeCriar') ? document.getElementById('formUserPodeCriar').checked : false;

    if (!nome || !email) {
      alertBox.textContent = 'Nome completo e e-mail são obrigatórios.';
      alertBox.classList.remove('hidden');
      return;
    }

    if (!['Master', 'Administrador'].includes(hierarquia) && this.selectedAccesses.length === 0) {
      alertBox.textContent = 'Selecione e adicione pelo menos uma instituição para este nível de acesso.';
      alertBox.classList.remove('hidden');
      return;
    }

    const payload = {
      nome_completo_usuario: nome,
      email: email,
      hierarquia: hierarquia,
      ativo: ativo,
      pode_criar_usuario: pode_criar_usuario,
      pode_simular_visao: document.getElementById('formUserPodeSimular') ? document.getElementById('formUserPodeSimular').checked : false,
      ...(document.getElementById('formUserPodeCadastrarEscola') ? {pode_cadastrar_escola: document.getElementById('formUserPodeCadastrarEscola').checked} : {}),
      limite_criacao_usuarios: document.getElementById('formUserLimiteCriacao') ? document.getElementById('formUserLimiteCriacao').value : '',
      data_expiracao_login: document.getElementById('formUserUnlimited').checked ? null : document.getElementById('formUserExpirationDate').value,
      acessos: this.selectedAccesses,
      paginas_permitidas: Array.from(document.querySelectorAll('input[name="userPages"]:checked')).map(cb => cb.value)
    };

    saveBtn.disabled = true;
    saveBtn.innerHTML = '<span>Salvando...</span>';

    try {
      if (this.currentEditingId) {
        // Edit User
        const res = await API.updateUser(this.currentEditingId, payload);
        App.showToast('Usuário atualizado com sucesso!', 'success');
        this.closeModal('userModal');
        this.loadUsers();
      } else {
        // Create User
        const res = await API.createUser(payload);
        this.closeModal('userModal');
        this.loadUsers();
        // Show temporary password modal
        this.showTemporaryPasswordModal(res.user.nome_completo_usuario, res.user.senha_temporaria);
      }
    } catch (err) {
      if (err.data && err.data.error === 'DELEGATION_REDUCTION_CONFLICT') {
        this.showReductionConflicts(err.data);
      } else {
        alertBox.textContent = err.message || 'Erro ao salvar usuário.';
        alertBox.classList.remove('hidden');
      }
    } finally {
      saveBtn.disabled = false;
      saveBtn.innerHTML = '<span>Salvar Usuário</span>';
    }
  },

  showReductionConflicts(data) {
    const conflictBox = document.getElementById('conflictAlertBox');
    const conflictMsg = document.getElementById('conflictAlertMsg');
    const conflictList = document.getElementById('conflictSubordinatesList');

    conflictMsg.textContent = data.message;
    conflictList.innerHTML = (data.conflitos || []).map(c => `
      <li style="margin-bottom: 0.5rem;">
        <strong>${this.escapeHtml(c.nome_completo_usuario)}</strong> (${c.hierarquia}) - 
        <span class="text-danger">${c.total_escolas_excedentes} escola(s) ficariam inacessíveis.</span>
      </li>
    `).join('');

    conflictBox.classList.remove('hidden');
  },

  async handleResetPassword(userId, userName) {
    if (!confirm(`Deseja realmente gerar uma nova senha temporária para o usuário "${userName}"?\n\nTodas as sessões ativas deste usuário serão encerradas imediatamente e ele será obrigado a cadastrar uma nova senha no próximo login.`)) {
      return;
    }

    try {
      const res = await API.resetPassword(userId);
      this.showTemporaryPasswordModal(userName, res.senha_temporaria);
      this.loadUsers();
    } catch (err) {
      App.showToast('Erro ao redefinir senha: ' + err.message, 'danger');
    }
  },

  showTemporaryPasswordModal(userName, tempPassword) {
    document.getElementById('tempPasswordUserName').textContent = userName;
    document.getElementById('displayTempPassword').textContent = tempPassword;
    this.openModal('tempPasswordModal');
  },

  openModal(modalId) {
    document.getElementById(modalId).classList.add('active');
  },

  closeModal(modalId) {
    document.getElementById(modalId).classList.remove('active');
  },

  escapeHtml(str) {
    if (!str) return '';
    return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#039;");
  }
};
