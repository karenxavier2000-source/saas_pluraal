// Pluraal API Client
const API = {
  TOKEN_KEY: 'pluraal_auth_token',
  USER_KEY: 'pluraal_user_data',

  getToken() {
    return localStorage.getItem(this.TOKEN_KEY);
  },

  setToken(token) {
    localStorage.setItem(this.TOKEN_KEY, token);
  },

  getStoredUser() {
    const raw = localStorage.getItem(this.USER_KEY);
    return raw ? JSON.parse(raw) : null;
  },

  setUser(user) {
    localStorage.setItem(this.USER_KEY, JSON.stringify(user));
  },

  clearAuth() {
    localStorage.removeItem(this.TOKEN_KEY);
    localStorage.removeItem(this.USER_KEY);
  },

  async request(endpoint, options = {}) {
    const headers = options.headers || {};
    const token = this.getToken();

    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const simNivel = document.getElementById('previewNivel')?.value;
    if (simNivel) {
      headers['X-Simulate-Nivel'] = simNivel;
      headers['X-Simulate-Uniao'] = document.getElementById('previewUniao')?.value || '';
      headers['X-Simulate-Associacao'] = document.getElementById('previewAssociacao')?.value || '';
      headers['X-Simulate-Escola'] = document.getElementById('previewEscola')?.value || '';
    }

    if (options.body && typeof options.body === 'object' && !(options.body instanceof FormData)) {
      headers['Content-Type'] = 'application/json';
      options.body = JSON.stringify(options.body);
    }

    options.headers = headers;

    try {
      const response = await fetch(endpoint, options);
      const data = await response.json().catch(() => ({}));

      if (!response.ok) {
        // Intercept session revocation
        if (response.status === 401) {
          if (data.error === 'SESSION_REVOKED' || data.error === 'UNAUTHORIZED' || data.error === 'LOGIN_EXPIRED') {
            this.clearAuth();
            window.dispatchEvent(new CustomEvent('auth:session_expired', { detail: data.message }));
          }
        }

        // Intercept mandatory password change
        if (response.status === 403 && data.error === 'FORCE_PASSWORD_CHANGE') {
          window.dispatchEvent(new CustomEvent('auth:force_password_change', { detail: data.message }));
        }

        const error = new Error(data.message || 'Erro na requisição');
        error.status = response.status;
        error.data = data;
        throw error;
      }

      return data;
    } catch (err) {
      throw err;
    }
  },

  // Auth endpoints
  login(email, senha) {
    return this.request('/api/auth/login', {
      method: 'POST',
      body: { email, senha }
    });
  },

  changePassword(senha_atual, nova_senha, confirmacao_senha) {
    return this.request('/api/auth/change-password', {
      method: 'POST',
      body: { senha_atual, nova_senha, confirmacao_senha }
    });
  },

  getCurrentUser() {
    return this.request('/api/auth/me');
  },

  // Users endpoints
  getUsers() {
    return this.request('/api/users');
  },

  getUser(id) {
    return this.request(`/api/users/${id}`);
  },

  createUser(userData) {
    return this.request('/api/users', {
      method: 'POST',
      body: userData
    });
  },

  updateUser(id, userData) {
    return this.request(`/api/users/${id}`, {
      method: 'PUT',
      body: userData
    });
  },

  resetPassword(id) {
    return this.request(`/api/users/${id}/reset-password`, {
      method: 'POST'
    });
  },

  // Hierarchy capabilities
  getHierarchyCapabilities() {
    return this.request('/api/hierarchy/capabilities');
  },

  // Reports
  getReports(filters = {}) {
    const params = new URLSearchParams();
    Object.entries(filters).forEach(([key,value]) => { if (value) params.append(key,value); });
    return this.request(`/api/reports?${params.toString()}`, {cache: 'no-store'});
  },

  getStudentReport(filters = {}) {
    return this.request(`/api/reports/student?${new URLSearchParams(filters).toString()}`);
  },

  getSimuladoDetail(simuladoId, filters = {}) {
    return this.request(`/api/reports/simulado/${simuladoId}?${new URLSearchParams(filters).toString()}`);
  },

  getPendingStudents(filters = {}) {
    return this.request(`/api/reports/pending?${new URLSearchParams(filters).toString()}`);
  },

  getReportStudents(filters = {}) {
    return this.request(`/api/reports/students?${new URLSearchParams(filters).toString()}`);
  },

  getExportOptions() {
    return this.request('/api/reports/export-options');
  },

  async exportTable(table, filters = {}) {
    const params = new URLSearchParams(Object.entries(filters).filter(([, value]) => value));
    const response = await fetch(`/api/reports/export/${table}?${params}`, {
      headers: { Authorization: `Bearer ${this.getToken()}` }
    });
    if (!response.ok) {
      const data = await response.json().catch(() => ({}));
      if (response.status === 401) {
        this.clearAuth();
        window.dispatchEvent(new CustomEvent('auth:session_expired', { detail: data.message }));
      }
      throw new Error(data.message || 'Não foi possível exportar os dados.');
    }
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `pluraal_${table}.csv`;
    document.body.appendChild(link);
    link.click();
    link.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  },

  async downloadPdf(reportType, filters = {}) {
    const params = new URLSearchParams(Object.entries(filters).filter(([, value]) => value));
    const response = await fetch(`/api/reports/pdf/${reportType}?${params}`, {
      headers: { Authorization: `Bearer ${this.getToken()}` }
    });
    if (!response.ok) {
      const data = await response.json().catch(() => ({}));
      if (response.status === 401) {
        this.clearAuth();
        window.dispatchEvent(new CustomEvent('auth:session_expired', { detail: data.message }));
      }
      throw new Error(data.message || 'Não foi possível gerar o arquivo PDF.');
    }
    const blob = await response.blob();
    const disposition = response.headers.get('Content-Disposition') || '';
    const match = disposition.match(/filename="?([^";]+)"?/);
    const filename = match ? match[1] : `relatorio_${reportType}.pdf`;
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    link.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
};
