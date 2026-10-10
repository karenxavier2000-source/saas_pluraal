// Main Pluraal App Controller and Shell
const App = {
  currentView: 'reports',

  permittedPages() {
    const pages = API.getStoredUser()?.paginas_permitidas;
    return Array.isArray(pages) ? pages : [];
  },

  canOpen(view) {
    return view === 'profile' || this.permittedPages().includes(view === 'pdfReports' ? 'reports' : view);
  },

  firstAllowedView() {
    return ['reports', 'paaeb', 'enem', 'data'].find(view => this.canOpen(view)) || 'profile';
  },

  init() {
    const hash = window.location.hash.replace('#', '');
    if (['reports', 'profile', 'data', 'enem', 'paaeb'].includes(hash)) {
      this.currentView = hash;
    }
    this.bindEvents();
    Auth.init();
    Users.init();
    Schools.init();
    Reports.init();
    Profile.init();
    ReportModal.init();

    window.addEventListener('hashchange', () => {
        const h = window.location.hash.replace('#', '');
        if (['reports', 'profile', 'data', 'enem', 'paaeb'].includes(h) && h !== this.currentView) {
            this.navigateTo(h);
        }
    });
  },

  bindEvents() {
    // Navigation links in sidebar
    document.querySelectorAll('.nav-link[data-view]').forEach(link => {
      link.addEventListener('click', (e) => {
        e.preventDefault();
        const view = link.getAttribute('data-view');
        
        if (!this.canOpen(view)) return;
        
        if (view === 'pdfReports') {
          ReportModal.open();
          this.closeMobileSidebar();
          return;
        }
        this.navigateTo(view);
        this.closeMobileSidebar();
      });
    });

    const userCard = document.getElementById('userCardPremium');
    const userContainer = document.getElementById('sidebarUserContainer');
    userCard?.addEventListener('click', () => {
      const open = userContainer.classList.toggle('active');
      userCard.setAttribute('aria-expanded', String(open));
    });
    document.addEventListener('click', event => {
      if (userContainer && !userContainer.contains(event.target)) {
        userContainer.classList.remove('active');
        userCard?.setAttribute('aria-expanded', 'false');
      }
    });
    document.getElementById('openProfileBtn')?.addEventListener('click', () => {
      userContainer.classList.remove('active');
      userCard.setAttribute('aria-expanded', 'false');
      this.navigateTo('profile');
      this.closeMobileSidebar();
    });

    // Photo change entry points (sidebar dropdown + profile card)
    document.getElementById('changePhotoDropdownBtn')?.addEventListener('click', () => {
      userContainer.classList.remove('active');
      userCard.setAttribute('aria-expanded', 'false');
      this.triggerPhotoUpload();
    });
    ['profileChangePhoto', 'profileChangePhotoBtn', 'profileAvatar'].forEach(id => {
      document.getElementById(id)?.addEventListener('click', () => this.triggerPhotoUpload());
    });

    // Sidebar collapse toggle button (« / »)
    const collapseBtn = document.getElementById('sidebarToggleCollapse');
    collapseBtn?.addEventListener('click', (e) => {
      e.stopPropagation();
      this.toggleSidebar();
    });

    // Mobile / topbar menu toggle button
    const mobileBtn = document.getElementById('mobileMenuBtn');
    const backdrop = document.getElementById('sidebarBackdrop');

    if (mobileBtn) {
      mobileBtn.addEventListener('click', () => {
        if (window.innerWidth <= 1024) {
          this.toggleMobileSidebar();
        } else {
          this.toggleSidebar();
        }
      });
    }
    if (backdrop) {
      backdrop.addEventListener('click', () => this.closeMobileSidebar());
    }

    // Logout buttons
    document.querySelectorAll('[data-logout-btn]').forEach(btn => {
      btn.addEventListener('click', () => Auth.logout());
    });

    // PDF Reports Tabs
    document.querySelectorAll('.profile-tab[data-pdf-tab]').forEach(tab => {
      tab.addEventListener('click', () => {
        document.querySelectorAll('.profile-tab[data-pdf-tab]').forEach(t => {
          t.classList.remove('active');
          t.setAttribute('aria-selected', 'false');
          t.style.borderBottom = 'none';
          t.style.color = 'var(--text-muted)';
        });
        tab.classList.add('active');
        tab.setAttribute('aria-selected', 'true');
        tab.style.borderBottom = '3px solid var(--brand-green)';
        tab.style.color = 'var(--color-primary)';
        
        const target = tab.dataset.pdfTab;
        document.getElementById('tabPdfSimulado').style.display = target === 'simulado' ? 'block' : 'none';
        document.getElementById('tabPdfPaaeb').style.display = target === 'paaeb' ? 'block' : 'none';
      });
    });
  },

  showDashboard() {
    document.getElementById('authView').classList.add('hidden');
    document.getElementById('appView').classList.remove('hidden');

    // Restore saved sidebar collapsed state on desktop
    const savedCollapsed = localStorage.getItem('pluraal_sidebar_collapsed') === 'true';
    if (savedCollapsed && window.innerWidth > 1024) {
      this.toggleSidebar(true);
    }

    this.updateUserInterfaceDetails();
    if (!this.canOpen(this.currentView)) this.currentView = this.firstAllowedView();
    this.navigateTo(this.currentView);
  },

  toggleSidebar(forceState) {
    const sidebar = document.getElementById('appSidebar');
    const container = document.getElementById('appView');
    const toggleBtn = document.getElementById('sidebarToggleCollapse');
    if (!sidebar) return;

    if (window.innerWidth <= 1024) {
      this.toggleMobileSidebar();
      return;
    }

    const isCollapsed = typeof forceState === 'boolean'
      ? (forceState ? sidebar.classList.add('collapsed') || true : sidebar.classList.remove('collapsed') || false)
      : sidebar.classList.toggle('collapsed');

    container?.classList.toggle('sidebar-collapsed', isCollapsed);
    if (toggleBtn) {
      toggleBtn.setAttribute('aria-expanded', String(!isCollapsed));
      toggleBtn.setAttribute('title', isCollapsed ? 'Expandir menu' : 'Recolher menu');
    }
    localStorage.setItem('pluraal_sidebar_collapsed', String(isCollapsed));
  },

  updateUserInterfaceDetails() {
    const user = API.getStoredUser();
    if (!user) return;
    const nameParts = (user.nome_completo_usuario || '').trim().split(/\s+/).filter(Boolean);
    const displayName = nameParts.length > 1
      ? `${nameParts[0]} ${nameParts[nameParts.length - 1]}`
      : (nameParts[0] || 'Usuário');

    // Sidebar user details
    const nameEl = document.getElementById('sidebarUserName');
    const titleEl = document.getElementById('sidebarUserTitle');
    const roleEl = document.getElementById('sidebarUserRole');
    const avatarEl = document.getElementById('sidebarUserAvatar');
    const scopeTag = document.getElementById('topbarScopeTag');

    if (nameEl) nameEl.textContent = displayName;
    if (titleEl) {
      const titleMap = {
        'Master': 'Master',
        'Administrador': 'Administrador',
        'uniao': 'Gestor de União',
        'associacao': 'Gestor de Associação',
        'escola': 'Gestor Escolar'
      };
      titleEl.textContent = titleMap[user.hierarquia] || (user.pode_criar_usuarios ? 'Administrador' : 'Usuário');
    }
    const isMaster = user.hierarquia === 'Master';
    let displayRole = user.hierarquia;
    if (!isMaster && user.acessos?.length) {
      const acc = user.acessos[0];
      if (user.hierarquia === 'uniao') displayRole = acc.sigla_uniao || displayRole;
      else if (user.hierarquia === 'associacao') displayRole = acc.sigla_associacao || displayRole;
      else if (user.hierarquia === 'escola') displayRole = acc.nome_escola || displayRole;
    }
    if (roleEl) {
      const hierBadgeClass = {
        'Master': 'badge-master',
        'Administrador': 'badge-master',
        'uniao': 'badge-uniao',
        'associacao': 'badge-associacao',
        'escola': 'badge-escola'
      }[user.hierarquia] || 'badge-inactive';
      
      const crownSvg = isMaster 
        ? `<svg class="crown-icon" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M11.562 3.266a.5.5 0 0 1 .876 0L15.39 8.87a1 1 0 0 0 1.516.294L21.183 5.5a.5.5 0 0 1 .798.519l-2.834 10.269a1 1 0 0 1-.96.712H5.813a1 1 0 0 1-.96-.712L2.019 6.019a.5.5 0 0 1 .798-.519l4.277 3.664a1 1 0 0 0 1.516-.294z"/><path d="M5 21h14"/></svg>` 
        : '';

      roleEl.innerHTML = `<span class="badge ${hierBadgeClass}">${crownSvg}<span>${displayRole}</span></span>`;
    }

    if (avatarEl) {
      if (user.foto_perfil) {
        avatarEl.innerHTML = `<img src="${user.foto_perfil}" alt="Avatar" style="width:100%; height:100%; border-radius:50%; object-fit:cover; cursor:pointer;" id="avatarImgEl">`;
      } else {
        const initials = `${nameParts[0]?.[0] || ''}${nameParts.length > 1 ? nameParts[nameParts.length - 1][0] : ''}`.toUpperCase();
        avatarEl.innerHTML = `<span style="cursor:pointer;" id="avatarTextEl">${initials || 'PL'}</span>`;
      }
      
      const clickableEl = document.getElementById('avatarImgEl') || document.getElementById('avatarTextEl');
      if (clickableEl && !avatarEl.hasAttribute('data-has-listener')) {
        avatarEl.setAttribute('data-has-listener', 'true');
        avatarEl.addEventListener('click', (event) => {
          event.stopPropagation();
          this.triggerPhotoUpload();
        });
      }
    }

    if (scopeTag) {
      scopeTag.textContent = user.hierarquia === 'Master' ? 'Escopo: Master (Total)' : `Escopo: ${displayRole}`;
    }

    // Filter Navigation Pages
    document.querySelectorAll('.nav-link[data-view], .nav-link[data-permission-page]').forEach(link => {
      const page = link.dataset.permissionPage || link.dataset.view;
      link.hidden = !this.canOpen(page);
      link.style.display = '';
    });
  },

  navigateTo(viewName, tab = 'overview') {
    if (!this.canOpen(viewName)) viewName = this.firstAllowedView();
    this.currentView = viewName;
    window.location.hash = viewName;

    // Update nav links
    document.querySelectorAll('.nav-link[data-view]').forEach(link => {
      const active = link.getAttribute('data-view') === viewName;
      link.classList.toggle('active', active);
      if (active) link.setAttribute('aria-current', 'page');
      else link.removeAttribute('aria-current');
    });

    // Toggle view containers
    const reportsView = document.getElementById('viewReports');
    const profileView = document.getElementById('viewProfile');
    const pdfReportsView = document.getElementById('viewPdfReports');
    const dataView = document.getElementById('viewData');
    const enemView = document.getElementById('viewEnem');
    const paaebView = document.getElementById('viewPaaeb');
    const topbarTitle = document.getElementById('topbarPageTitle');

    reportsView?.classList.toggle('hidden', viewName !== 'reports');
    profileView?.classList.toggle('hidden', viewName !== 'profile');
    pdfReportsView?.classList.toggle('hidden', viewName !== 'pdfReports');
    dataView?.classList.toggle('hidden', viewName !== 'data');
    enemView?.classList.toggle('hidden', viewName !== 'enem');
    paaebView?.classList.toggle('hidden', viewName !== 'paaeb');

    if (viewName === 'reports') {
      topbarTitle.textContent = 'Relatórios de Desempenho';
      Reports.loadReports();
    } else if (viewName === 'profile') {
      topbarTitle.textContent = 'Meu perfil';
      Profile.showTab(tab);
      Profile.load();
    } else if (viewName === 'data') {
      topbarTitle.textContent = 'Exportação de Dados';
      Profile.load();
    } else if (viewName === 'pdfReports') {
      topbarTitle.textContent = 'Relatórios PDF';
    } else if (viewName === 'paaeb') {
      topbarTitle.textContent = 'PAAEB';
    } else if (viewName === 'enem') {
      topbarTitle.textContent = 'ENEM';
    }
  },

  toggleMobileSidebar() {
    const sidebar = document.getElementById('appSidebar');
    const backdrop = document.getElementById('sidebarBackdrop');
    sidebar.classList.toggle('mobile-open');
    backdrop.classList.toggle('active');
  },

  closeMobileSidebar() {
    const sidebar = document.getElementById('appSidebar');
    const backdrop = document.getElementById('sidebarBackdrop');
    sidebar.classList.remove('mobile-open');
    backdrop.classList.remove('active');
  },

  showToast(message, type = 'info') {
    let container = document.getElementById('toastContainer');
    if (!container) {
      container = document.createElement('div');
      container.id = 'toastContainer';
      container.style.cssText = `
        position: fixed;
        bottom: 1.5rem;
        right: 1.5rem;
        z-index: 10000;
        display: flex;
        flex-direction: column;
        gap: 0.75rem;
        max-width: 380px;
        width: 100%;
        pointer-events: none;
      `;
      document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    const bgColors = {
      success: 'var(--color-accent-green-dark)',
      danger: 'var(--color-accent-red)',
      warning: 'var(--color-accent-orange)',
      info: 'var(--color-primary)'
    };

    toast.style.cssText = `
      background-color: ${bgColors[type] || 'var(--color-primary)'};
      color: #fff;
      padding: 0.875rem 1.25rem;
      border-radius: var(--radius-md);
      box-shadow: var(--shadow-lg);
      font-size: var(--font-size-sm);
      font-weight: 500;
      line-height: 1.4;
      pointer-events: auto;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 0.75rem;
      animation: slideInRight 0.3s ease-out;
      transition: opacity 0.3s ease, transform 0.3s ease;
    `;

    toast.innerHTML = `
      <span>${message}</span>
      <button style="background:none; border:none; color:#fff; cursor:pointer; font-size:1.2rem; line-height:1;">&times;</button>
    `;

    toast.querySelector('button').addEventListener('click', () => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateY(10px)';
      setTimeout(() => toast.remove(), 300);
    });

    container.appendChild(toast);

    setTimeout(() => {
      if (toast.parentElement) {
        toast.style.opacity = '0';
        toast.style.transform = 'translateY(10px)';
        setTimeout(() => toast.remove(), 300);
      }
    }, 4500);
  },

  triggerPhotoUpload() {
    const user = API.getStoredUser();
    if (!user) return;
    
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = 'image/png, image/jpeg, image/webp';
    input.onchange = async (e) => {
      const file = e.target.files[0];
      if (!file) return;
      
      if (file.size > 10 * 1024 * 1024) {
        App.showToast('A imagem deve ter no máximo 10MB.', 'warning');
        return;
      }
      
      const reader = new FileReader();
      reader.onload = async (ev) => {
        const base64 = ev.target.result;
        try {
          const res = await API.request(`/api/users/${user.id_usuario}/photo`, {
            method: 'POST',
            body: { foto_perfil: base64 }
          });
          
          if (res.foto_perfil !== undefined) {
            user.foto_perfil = res.foto_perfil;
            API.setUser(user);
            this.updateUserInterfaceDetails();
            if (typeof Profile !== 'undefined') Profile.load();
            App.showToast('Foto atualizada com sucesso!', 'success');
          } else {
            throw new Error(res.message || 'Erro ao atualizar foto');
          }
        } catch (err) {
          console.error(err);
          App.showToast('Erro ao enviar foto: ' + err.message, 'danger');
        }
      };
      reader.readAsDataURL(file);
    };
    input.click();
  }
};

// Footer Helper
window.FooterHelper = {
  copyEmail(btn) {
    const email = 'sac@aextecnologia.com.br';
    const copyText = btn.querySelector('.copy-text');
    const origText = copyText ? copyText.textContent : 'Copiar';

    const showSuccess = () => {
      if (copyText) copyText.textContent = 'Copiado!';
      btn.style.background = '#22c55e';
      btn.style.color = '#ffffff';
      btn.style.borderColor = '#22c55e';
      if (typeof App !== 'undefined' && App.showToast) {
        App.showToast('E-mail de suporte copiado para a área de transferência!', 'success');
      }
      setTimeout(() => {
        if (copyText) copyText.textContent = origText;
        btn.style.background = '';
        btn.style.color = '';
        btn.style.borderColor = '';
      }, 2200);
    };

    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(email).then(showSuccess).catch(() => {
        this.fallbackCopy(email, showSuccess);
      });
    } else {
      this.fallbackCopy(email, showSuccess);
    }
  },

  fallbackCopy(text, callback) {
    const textarea = document.createElement('textarea');
    textarea.value = text;
    textarea.style.position = 'fixed';
    textarea.style.opacity = '0';
    document.body.appendChild(textarea);
    textarea.select();
    try {
      document.execCommand('copy');
      if (callback) callback();
    } catch (e) {
      window.location.href = `mailto:${text}`;
    }
    document.body.removeChild(textarea);
  }
};

document.addEventListener('DOMContentLoaded', () => {
  App.init();
});

