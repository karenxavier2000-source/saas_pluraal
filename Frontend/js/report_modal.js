/**
 * Módulo de Controle do Modal Unificado de Relatórios Executivos Pluraal
 * Suporta emissão para Simulado ou PAAEB em múltiplos escopos:
 * - Rede Geral
 * - União (todas as suas associações e escolas)
 * - Associação (suas escolas)
 * - Escola Individual ou Múltiplas Escolas
 * - Análises por Turma, Aluno, Bimestre, Ano, Séries e Habilidades
 */

const ReportModal = {
  tipoAvaliacao: 'simulado',

  init() {
    // Botões para abrir o modal
    const navPdf = document.getElementById('navLinkPdfReports');
    if (navPdf) {
      navPdf.addEventListener('click', (e) => {
        e.preventDefault();
        this.open();
      });
    }

    const openBtn = document.getElementById('btnOpenReportModal');
    if (openBtn) {
      openBtn.addEventListener('click', () => this.open());
    }

    const heroPdfBtn = document.getElementById('btnHeroOpenReportModal');
    if (heroPdfBtn) {
      heroPdfBtn.addEventListener('click', () => this.open());
    }

    // Botões de fechar modal
    document.getElementById('btnCloseModalReport')?.addEventListener('click', () => this.close());
    document.getElementById('btnCancelModalReport')?.addEventListener('click', () => this.close());
    document.getElementById('modalReportGenerator')?.addEventListener('click', (e) => {
      if (e.target.id === 'modalReportGenerator') this.close();
    });

    // Seletor Tipo: Simulado vs PAAEB
    document.getElementById('btnTipoSimulado')?.addEventListener('click', () => this.setTipo('simulado'));
    document.getElementById('btnTipoPaaeb')?.addEventListener('click', () => { if(typeof App !== 'undefined') App.showToast('Em breve', 'info'); });

    // Mudanças de filtros no modal
    ['modalFilterUniao', 'modalFilterAssoc', 'modalFilterEscola'].forEach(id => {
      document.getElementById(id)?.addEventListener('change', () => {
        this.handleInstitutionalFilterChange(id);
        this.updateScopeSummary();
      });
    });

    ['modalFilterAno', 'modalFilterBimestre', 'modalFilterSerie', 'modalFilterTurma'].forEach(id => {
      document.getElementById(id)?.addEventListener('change', () => this.updateScopeSummary());
    });

    // Botão de confirmação de geração
    document.getElementById('btnConfirmGenerateReport')?.addEventListener('click', () => this.generate());
  },

  setTipo(tipo) {
    this.tipoAvaliacao = tipo;
    const btnSim = document.getElementById('btnTipoSimulado');
    const btnPaa = document.getElementById('btnTipoPaaeb');

    if (btnSim && btnPaa) {
      if (tipo === 'simulado') {
        btnSim.style.border = '2px solid #4338ca';
        btnSim.style.background = '#eef2ff';
        btnSim.querySelector('.badge').style.background = '#4338ca';
        btnSim.querySelector('.badge').style.color = '#fff';
        btnSim.querySelector('.badge').textContent = 'Ativo';

        btnPaa.style.border = '2px solid #e2e8f0';
        btnPaa.style.background = '#fff';
        btnPaa.querySelector('.badge').style.background = '#e2e8f0';
        btnPaa.querySelector('.badge').style.color = '#64748b';
        btnPaa.querySelector('.badge').textContent = 'Selecionar';
      } else {
        btnPaa.style.border = '2px solid #0284c7';
        btnPaa.style.background = '#e0f2fe';
        btnPaa.querySelector('.badge').style.background = '#0284c7';
        btnPaa.querySelector('.badge').style.color = '#fff';
        btnPaa.querySelector('.badge').textContent = 'Ativo';

        btnSim.style.border = '2px solid #e2e8f0';
        btnSim.style.background = '#fff';
        btnSim.querySelector('.badge').style.background = '#e2e8f0';
        btnSim.querySelector('.badge').style.color = '#64748b';
        btnSim.querySelector('.badge').textContent = 'Selecionar';
      }
    }
    this.updateScopeSummary();
  },

  populateFilters() {
    const entities = Reports.entities || [];
    const catalog = Reports.catalog && Reports.catalog.length ? Reports.catalog : entities;

    // 1. Uniões
    const unions = [...new Set(entities.map(x => x.uniao).filter(Boolean))].sort();
    Reports.select('modalFilterUniao', unions.map(x => ({ value: x, label: x })), 'Todas as Uniões (Geral)');

    // 2. Anos
    const anos = Reports.data?.anos_disponiveis || ['2026', '2025'];
    Reports.select('modalFilterAno', anos.map(x => ({ value: x, label: x })), 'Todos os Anos');

    // 3. Bimestres
    const bimestres = Reports.data?.bimestres_disponiveis || ['1º BIMESTRE', '2º BIMESTRE', '3º BIMESTRE'];
    Reports.select('modalFilterBimestre', bimestres.map(x => ({ value: x, label: x })), 'Todos os Bimestres');

    // 4. Séries
    const series = (Reports.data?.por_serie || []).map(s => s.serie).filter(Boolean);
    Reports.select('modalFilterSerie', series.map(x => ({ value: x, label: x })), 'Todas as Séries');

    // 5. Turmas
    const turmas = [...new Set((Reports.data?.por_turma || []).map(t => t.turma).filter(Boolean))].sort();
    Reports.select('modalFilterTurma', turmas.map(x => ({ value: x, label: x })), 'Todas as Turmas');

    // Atualizar associações e escolas
    this.handleInstitutionalFilterChange('init');
  },

  handleInstitutionalFilterChange(changed) {
    const entities = Reports.entities || [];
    const u = document.getElementById('modalFilterUniao')?.value || '';
    const oldA = document.getElementById('modalFilterAssoc')?.value || '';
    const oldE = document.getElementById('modalFilterEscola')?.value || '';

    // Filtrar Associações
    const assocs = [...new Set(entities.filter(x => !u || x.uniao === u).map(x => x.associacao).filter(Boolean))].sort();
    Reports.select('modalFilterAssoc', assocs.map(x => ({ value: x, label: x })), 'Todas as Associações', changed === 'modalFilterUniao' ? '' : oldA);

    // Filtrar Escolas
    const a = document.getElementById('modalFilterAssoc')?.value || '';
    const schools = entities.filter(x => (!u || x.uniao === u) && (!a || x.associacao === a));
    Reports.select('modalFilterEscola', schools.map(x => ({ value: x.id_escolas, label: x.escola })), 'Todas as Unidades Escolares', ['modalFilterUniao', 'modalFilterAssoc'].includes(changed) ? '' : oldE);
  },

  updateScopeSummary() {
    const u = document.getElementById('modalFilterUniao')?.value || '';
    const a = document.getElementById('modalFilterAssoc')?.value || '';
    const e = document.getElementById('modalFilterEscola')?.value || '';
    const ano = document.getElementById('modalFilterAno')?.value || '2026';
    const bim = document.getElementById('modalFilterBimestre')?.value || '';
    const tipo = this.tipoAvaliacao.toUpperCase();

    const badge = document.getElementById('modalScopeBadge');
    const title = document.getElementById('modalScopeTitle');
    const desc = document.getElementById('modalScopeDesc');
    if (!badge || !title || !desc) return;

    if (e) {
      const escName = document.getElementById('modalFilterEscola')?.selectedOptions[0]?.text || 'Unidade Escolar';
      badge.textContent = 'Unidade Individual';
      badge.style.background = '#dcfce7';
      badge.style.color = '#15803d';
      title.textContent = `Relatório Executivo da Unidade · ${escName}`;
      desc.textContent = `Resultados, disciplinas, habilidades, turmas e estudantes da unidade selecionada na avaliação ${tipo}.`;
    } else if (a) {
      badge.textContent = 'Associação Regional';
      badge.style.background = '#fef3c7';
      badge.style.color = '#b45309';
      title.textContent = `Relatório Executivo da Associação · ${a}`;
      desc.textContent = `Resultados consolidados das escolas da associação, com desempenho por série, turma e habilidade.`;
    } else if (u) {
      badge.textContent = 'União Regional';
      badge.style.background = '#e0f2fe';
      badge.style.color = '#0369a1';
      title.textContent = `Relatório Executivo da União · ${u}`;
      desc.textContent = `Resultados das associações e escolas da união, com rankings e diagnóstico pedagógico.`;
    } else {
      badge.textContent = 'Rede Global';
      badge.style.background = '#e0e7ff';
      badge.style.color = '#3730a3';
      title.textContent = `Relatório Executivo Geral da Rede · ${tipo}`;
      desc.textContent = `Resultados de todas as uniões, associações e escolas, com rankings e diagnóstico pedagógico.`;
    }
  },

  open() {
    this.populateFilters();

    // Sincronizar com filtros já selecionados na tela principal se houver
    const mainU = document.getElementById('reportFilterUniao')?.value;
    const mainA = document.getElementById('reportFilterAssoc')?.value;
    const mainE = document.getElementById('reportFilterEscola')?.value;
    const mainAno = document.getElementById('reportFilterAno')?.value;
    const mainBim = document.getElementById('reportFilterBimestre')?.value;

    if (mainU) {
      const selU = document.getElementById('modalFilterUniao');
      if (selU) { selU.value = mainU; this.handleInstitutionalFilterChange('modalFilterUniao'); }
    }
    if (mainA) {
      const selA = document.getElementById('modalFilterAssoc');
      if (selA) { selA.value = mainA; this.handleInstitutionalFilterChange('modalFilterAssoc'); }
    }
    if (mainE) {
      const selE = document.getElementById('modalFilterEscola');
      if (selE) selE.value = mainE;
    }
    if (mainAno) {
      const selAno = document.getElementById('modalFilterAno');
      if (selAno) selAno.value = mainAno;
    }
    if (mainBim) {
      const selBim = document.getElementById('modalFilterBimestre');
      if (selBim) selBim.value = mainBim;
    }

    this.updateScopeSummary();

    const modal = document.getElementById('modalReportGenerator');
    if (modal) {
      modal.classList.add('active');
      document.body.style.overflow = 'hidden';
    }
  },

  close() {
    const modal = document.getElementById('modalReportGenerator');
    if (modal) {
      modal.classList.remove('active');
      document.body.style.overflow = '';
    }
  },

  async generate() {
    const btn = document.getElementById('btnConfirmGenerateReport');
    const loading = document.getElementById('modalReportLoading');
    const u = document.getElementById('modalFilterUniao')?.value || '';
    const a = document.getElementById('modalFilterAssoc')?.value || '';
    const e = document.getElementById('modalFilterEscola')?.value || '';
    const ano = document.getElementById('modalFilterAno')?.value || '';
    const bim = document.getElementById('modalFilterBimestre')?.value || '';
    const serie = document.getElementById('modalFilterSerie')?.value || '';
    const turma = document.getElementById('modalFilterTurma')?.value || '';

    const filters = {
      tipo_avaliacao: this.tipoAvaliacao,
      uniao: u,
      associacao: a,
      escola: e,
      ano: ano,
      bimestre: bim,
      serie: serie,
      turma: turma
    };

    if (btn) btn.disabled = true;
    if (loading) loading.classList.remove('hidden');

    App.showToast(`Iniciando geração do Relatório Completo (${this.tipoAvaliacao.toUpperCase()})...`, 'info');

    try {
      await API.downloadPdf('completo', filters);
      App.showToast('Relatório Executivo PDF compilado e baixado com sucesso!', 'success');
      this.close();
    } catch (err) {
      console.error(err);
      App.showToast(`Erro ao gerar PDF: ${err.message}`, 'danger');
    } finally {
      if (btn) btn.disabled = false;
      if (loading) loading.classList.add('hidden');
    }
  }
};
