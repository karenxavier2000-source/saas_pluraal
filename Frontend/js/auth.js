// Authentication Logic and First-Access Password Management
const Auth = {
  init() {
    this.bindEvents();
    this.checkInitialState();
  },

  async checkInitialState() {
    const token = API.getToken();
    const user = API.getStoredUser();

    if (!token || !user) {
      this.showLoginView();
      return;
    }

    try {
      const current = await API.getCurrentUser();
      API.setUser(current);
      if (current.trocar_senha_no_primeiro_acesso) this.showPasswordChangeBarrier();
      else App.showDashboard();
    } catch (error) {
      if (error.status === 401 || error.status === 403) this.showLoginView();
      else if (user.trocar_senha_no_primeiro_acesso) this.showPasswordChangeBarrier();
      else App.showDashboard();
    }
  },

  bindEvents() {
    // Login form submission
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
      loginForm.addEventListener('submit', (e) => this.handleLogin(e));
    }

    // Password change barrier form
    const pwChangeForm = document.getElementById('mandatoryPasswordChangeForm');
    if (pwChangeForm) {
      pwChangeForm.addEventListener('submit', (e) => this.handlePasswordChange(e));
      
      // Live validation on new password typing
      const newPwInput = document.getElementById('barrierNewPassword');
      if (newPwInput) {
        newPwInput.addEventListener('input', () => this.validatePasswordStrengthLive(newPwInput.value));
      }
    }

    // Global session events
    window.addEventListener('auth:session_expired', (e) => {
      App.showToast(e.detail || 'Sessão encerrada. Faça login novamente.', 'warning');
      this.showLoginView();
    });

    window.addEventListener('auth:force_password_change', () => {
      this.showPasswordChangeBarrier();
    });

    // Password toggle buttons
    document.querySelectorAll('.password-toggle-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const targetId = btn.getAttribute('data-target');
        const input = document.getElementById(targetId);
        if (input) {
          const isPassword = input.type === 'password';
          input.type = isPassword ? 'text' : 'password';
          btn.innerHTML = isPassword ? `
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path>
              <line x1="1" y1="1" x2="23" y2="23"></line>
            </svg>` : `
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
              <circle cx="12" cy="12" r="3"></circle>
            </svg>`;
        }
      });
    });
  },

  async handleLogin(e) {
    e.preventDefault();
    const email = document.getElementById('loginEmail').value.trim();
    const senha = document.getElementById('loginPassword').value;
    const alertBox = document.getElementById('loginAlert');
    const submitBtn = document.getElementById('loginSubmitBtn');

    alertBox.classList.add('hidden');
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<span>Verificando...</span>';

    try {
      const res = await API.login(email, senha);
      API.setToken(res.token);
      API.setUser(res.usuario);
      this.resetSimulation();

      if (res.usuario.trocar_senha_no_primeiro_acesso) {
        this.showPasswordChangeBarrier();
      } else {
        App.currentView = 'reports';
        App.showToast('Login realizado com sucesso!', 'success');
        this.hideLoginView();
        App.showDashboard();
      }
    } catch (err) {
      alertBox.textContent = err.message || 'Erro ao realizar login.';
      alertBox.classList.remove('hidden');
    } finally {
      submitBtn.disabled = false;
      submitBtn.innerHTML = '<span>Entrar no Sistema</span>';
    }
  },

  validatePasswordStrengthLive(pw) {
    const lengthCheck = document.getElementById('pwReqLength');
    const letterCheck = document.getElementById('pwReqLetter');
    const numberCheck = document.getElementById('pwReqNumber');

    if (!lengthCheck || !letterCheck || !numberCheck) return;

    // Check 8+ chars
    if (pw.length >= 8) {
      lengthCheck.classList.add('text-success');
    } else {
      lengthCheck.classList.remove('text-success');
    }

    // Check letter
    if (/[A-Za-z]/.test(pw)) {
      letterCheck.classList.add('text-success');
    } else {
      letterCheck.classList.remove('text-success');
    }

    // Check number
    if (/[0-9]/.test(pw)) {
      numberCheck.classList.add('text-success');
    } else {
      numberCheck.classList.remove('text-success');
    }
  },

  async handlePasswordChange(e) {
    e.preventDefault();
    const senhaAtual = document.getElementById('barrierCurrentPassword').value;
    const novaSenha = document.getElementById('barrierNewPassword').value;
    const confirmacao = document.getElementById('barrierConfirmPassword').value;
    const alertBox = document.getElementById('barrierAlert');
    const submitBtn = document.getElementById('barrierSubmitBtn');

    alertBox.classList.add('hidden');

    if (novaSenha !== confirmacao) {
      alertBox.textContent = 'A nova senha e a confirmação de senha não coincidem.';
      alertBox.classList.remove('hidden');
      return;
    }

    if (novaSenha === senhaAtual) {
      alertBox.textContent = 'A nova senha deve ser diferente da senha temporária atual.';
      alertBox.classList.remove('hidden');
      return;
    }

    if (novaSenha.length < 8) {
      alertBox.textContent = 'A nova senha deve conter pelo menos 8 caracteres.';
      alertBox.classList.remove('hidden');
      return;
    }

    submitBtn.disabled = true;
    submitBtn.innerHTML = '<span>Salvando nova senha...</span>';

    try {
      const res = await API.changePassword(senhaAtual, novaSenha, confirmacao);
      API.setToken(res.token);
      API.setUser(res.usuario);

      App.currentView = 'reports';
      App.showToast('Nova senha definida com sucesso! Acesso completo liberado.', 'success');
      this.hidePasswordChangeBarrier();
      this.hideLoginView();
      App.showDashboard();
    } catch (err) {
      alertBox.textContent = err.message || 'Erro ao alterar senha.';
      alertBox.classList.remove('hidden');
    } finally {
      submitBtn.disabled = false;
      submitBtn.innerHTML = '<span>Confirmar Nova Senha</span>';
    }
  },

  showLoginView() {
    this.resetSimulation();
    document.getElementById('authView').classList.remove('hidden');
    document.getElementById('appView').classList.add('hidden');
    this.hidePasswordChangeBarrier();
  },

  hideLoginView() {
    document.getElementById('authView').classList.add('hidden');
  },

  resetSimulation() {
    for (const id of ['previewNivel', 'previewUniao', 'previewAssociacao', 'previewEscola',
                      'reportFilterUniao', 'reportFilterAssoc', 'reportFilterEscola']) {
      const control = document.getElementById(id);
      if (control) control.value = '';
    }
    if (typeof Reports !== 'undefined') Reports.catalog = [];
  },

  showPasswordChangeBarrier() {
    const barrier = document.getElementById('passwordChangeBarrier');
    if (barrier) {
      barrier.classList.remove('hidden');
    }
  },

  hidePasswordChangeBarrier() {
    const barrier = document.getElementById('passwordChangeBarrier');
    if (barrier) {
      barrier.classList.add('hidden');
    }
  },

  logout() {
    API.clearAuth();
    App.currentView = 'reports';
    history.replaceState(null, '', window.location.pathname + window.location.search);
    App.showToast('Você saiu do sistema.', 'info');
    this.showLoginView();
  }
};
