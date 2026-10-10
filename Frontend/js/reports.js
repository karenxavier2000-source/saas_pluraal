const Reports = {
  data: null, entities: [], catalog: [], level: 'uniao', sequence: 0,
  pendingPage: 1, pendingTotal: 0, pendingRequest: 0,
  skillLevel: 'geral', skillPage: 1,
  directoryPage: 0, directoryRequest: 0,
  studentRequest: 0,
  bimonthlyTab: 'uniao', bimonthlySearch: '', bimonthlyStudentView: '',
  init() {
    for (const id of ['reportFilterUniao','reportFilterAssoc','reportFilterEscola','reportFilterAno','reportFilterBimestre']) {
      document.getElementById(id)?.addEventListener('change', () => {
        this.updateFilters(id); this.loadReports();
      });
    }
    PdfFilters.init();
    for (const id of ['previewNivel','previewUniao','previewAssociacao','previewEscola']) {
      document.getElementById(id)?.addEventListener('change', () => {
        this.updatePreview(id); 
        this.loadReports();
      });
    }
    document.getElementById('btnReportClearFilters')?.addEventListener('click', () => this.clearFilters());
    document.getElementById('btnReportRefresh')?.addEventListener('click', () => this.refresh());
    document.getElementById('schoolAnalysisSearch')?.addEventListener('input', () => { this.renderSchools(); this.renderAnalysisNotes(); });
    document.getElementById('simuladosSearch')?.addEventListener('input', () => this.renderSimulados());
    document.querySelectorAll('[data-skill-level]').forEach(button=>button.addEventListener('click',()=>{
      this.skillLevel=button.dataset.skillLevel;this.skillPage=1;this.renderSkills();
    }));
    for (const id of ['skillsSearch','skillsSubject','skillsSort']) {
      document.getElementById(id)?.addEventListener(id==='skillsSearch'?'input':'change',()=>{
        this.skillPage=1;this.renderSkills();
      });
    }
    document.getElementById('skillsPrevious')?.addEventListener('click',()=>{this.skillPage--;this.renderSkills();});
    document.getElementById('skillsNext')?.addEventListener('click',()=>{this.skillPage++;this.renderSkills();});
    document.getElementById('skillsExport')?.addEventListener('click',()=>this.exportSkills());
    document.getElementById('studentDirectoryForm')?.addEventListener('submit',event=>{event.preventDefault();this.loadStudentDirectory(true);});
    document.getElementById('studentDirectoryMore')?.addEventListener('click',()=>this.loadStudentDirectory(false));
    document.getElementById('studentModalBody')?.addEventListener('input',event=>{
      if(event.target.id==='studentSkillsSearch') {
        const term=this.fold(event.target.value);
        document.querySelectorAll('#studentSkillsBody tr[data-search]').forEach(row=>{row.hidden=!row.dataset.search.includes(term);});
      }
    });
    document.getElementById('studentModalBody')?.addEventListener('click',event=>{
      if(event.target.closest('#studentSkillsExport'))this.exportStudentSkills();
    });
    let pendingTimer;
    document.getElementById('pendingStudentsSearch')?.addEventListener('input', () => {
      clearTimeout(pendingTimer);
      pendingTimer=setTimeout(() => this.loadPending(true), 300);
    });
    document.getElementById('pendingStudentsMore')?.addEventListener('click', () => this.loadPending(false));
    document.querySelectorAll('[data-rank]').forEach(button => button.addEventListener('click', () => {
      this.level = button.dataset.rank; this.renderRankings();
      document.querySelectorAll('[data-rank]').forEach(b => b.classList.toggle('active', b === button));
      this.renderAnalysisNotes();
    }));
    document.getElementById('viewReports')?.addEventListener('click', event => {
      const button = event.target.closest('[data-student-list]');
      if (button) this.openStudent(button.dataset.studentList, Number(button.dataset.index));
    });
    document.getElementById('studentModal')?.addEventListener('click', event => {
      if (event.target.id === 'studentModal') this.closeStudent();
    });
    document.querySelectorAll('[data-bim-tab]').forEach(btn => btn.addEventListener('click', () => {
      this.bimonthlyTab = btn.dataset.bimTab;
      document.querySelectorAll('[data-bim-tab]').forEach(b => b.classList.toggle('active', b === btn));
      const wrap = document.getElementById('bimonthlyStudentFilterWrap');
      if (wrap) wrap.classList.toggle('hidden', this.bimonthlyTab !== 'aluno');
      this.renderBimonthlyTable();
    }));
    document.getElementById('bimonthlySearch')?.addEventListener('input', (e) => {
      this.bimonthlySearch = this.fold(e.target.value);
      this.renderBimonthlyTable();
    });
    document.getElementById('bimonthlyStudentSelect')?.addEventListener('change', (e) => {
      this.bimonthlyStudentView = e.target.value;
      this.renderBimonthlyTable();
    });
  },
  esc(value) {
    return String(value ?? '').replace(/[&<>"']/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
  },
  num(value) { return Number(value || 0).toLocaleString('pt-BR'); },
  fold(value) {return String(value||'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase();},
  pct(value) { return Number(value || 0).toLocaleString('pt-BR', {maximumFractionDigits:1}) + '%'; },
  select(id, options, label, keep = '') {
    const el = document.getElementById(id);
    el.innerHTML = `<option value="">${this.esc(label)}</option>` + options.map(x => `<option value="${this.esc(x.value)}">${this.esc(x.label)}</option>`).join('');
    el.value = keep;
  },
  updateFilters(changed) {
    const u = document.getElementById('reportFilterUniao').value;
    const oldA = document.getElementById('reportFilterAssoc').value;
    const oldE = document.getElementById('reportFilterEscola').value;
    const assocs = [...new Set(this.entities.filter(x => !u || x.uniao === u).map(x => x.associacao).filter(Boolean))].sort();
    this.select('reportFilterAssoc', assocs.map(x => ({value:x,label:x})), 'Todas as associações', changed === 'reportFilterUniao' ? '' : oldA);
    const a = document.getElementById('reportFilterAssoc').value;
    const schools = this.entities.filter(x => (!u || x.uniao === u) && (!a || x.associacao === a));
    this.select('reportFilterEscola', schools.map(x => ({value:x.id_escolas,label:x.escola})), 'Todas as escolas', ['reportFilterUniao','reportFilterAssoc'].includes(changed) ? '' : oldE);
  },
  updatePreview(changed) {
    const level = document.getElementById('previewNivel').value;
    const oldU = document.getElementById('previewUniao').value;
    const oldA = document.getElementById('previewAssociacao').value;
    const oldE = document.getElementById('previewEscola').value;
    for (const [id,show] of [['previewUniao',['uniao','associacao','escola'].includes(level)],['previewAssociacao',['associacao','escola'].includes(level)],['previewEscola',level==='escola']]) {
      document.getElementById(id).classList.toggle('hidden',!show);
    }
    const unions = [...new Set(this.catalog.map(x => x.uniao).filter(Boolean))].sort();
    this.select('previewUniao',unions.map(x=>({value:x,label:x})),'Escolha a união',changed==='previewNivel'?'':oldU);
    if (level && !document.getElementById('previewUniao').value && unions.length) document.getElementById('previewUniao').value=unions[0];
    const u = document.getElementById('previewUniao').value;
    const assocs = [...new Set(this.catalog.filter(x=>x.uniao===u).map(x=>x.associacao).filter(Boolean))].sort();
    this.select('previewAssociacao',assocs.map(x=>({value:x,label:x})),'Escolha a associação',['previewNivel','previewUniao'].includes(changed)?'':oldA);
    if (['associacao','escola'].includes(level) && !document.getElementById('previewAssociacao').value && assocs.length) document.getElementById('previewAssociacao').value=assocs[0];
    const a = document.getElementById('previewAssociacao').value;
    this.select('previewEscola',this.catalog.filter(x=>x.uniao===u&&x.associacao===a).map(x=>({value:x.id_escolas,label:x.escola})),'Escolha a escola',['previewNivel','previewUniao','previewAssociacao'].includes(changed)?'':oldE);
    if (level==='escola' && !document.getElementById('previewEscola').value) document.getElementById('previewEscola').selectedIndex=1;
  },
  filters() {
    const f = {};
    for (const [key,id] of Object.entries({uniao:'reportFilterUniao',associacao:'reportFilterAssoc',escola:'reportFilterEscola',ano:'reportFilterAno',bimestre:'reportFilterBimestre'})) f[key]=document.getElementById(id).value;
    const level=document.getElementById('previewNivel').value;
    if (level) Object.assign(f,{preview_nivel:level,preview_uniao:document.getElementById('previewUniao').value,preview_associacao:document.getElementById('previewAssociacao').value,preview_escola:document.getElementById('previewEscola').value});
    return f;
  },
  async refresh() {
    const button = document.getElementById('btnReportRefresh');
    button.disabled = true;
    try {
      await this.loadReports(true);
    } finally {
      button.disabled = false;
    }
  },
  async loadReports(forceRefresh = false) {
    const f=this.filters();
    if (f.preview_nivel && f.preview_nivel !== 'Administrador' && (!f.preview_uniao || (f.preview_nivel!=='uniao'&&!f.preview_associacao) || (f.preview_nivel==='escola'&&!f.preview_escola))) return;
    const seq=++this.sequence, status=document.getElementById('reportStatus');
    status.textContent='Carregando análises da rede…'; status.className='report-status';
    document.getElementById('viewReports').classList.add('loading');
    try {
      const data=await API.getReports({...f,...(forceRefresh?{refresh:'1'}:{})});
      if (seq!==this.sequence) return;
      if (!data.rankings || !data.participacao_bimestre || !data.kpis) throw new Error('O servidor está com uma versão antiga da API. Reinicie o processo Python.');
      this.data=data;
      this.directoryPage=0;
      document.getElementById('studentDirectoryList').innerHTML='';
      document.getElementById('studentDirectoryNote').textContent='Digite um nome ou RA e clique em Buscar alunos. Para listar todos, deixe o campo vazio e clique em Buscar alunos. A busca respeita os filtros acima.';
      document.getElementById('studentDirectoryMore').classList.add('hidden');
      this.skillPage=1;
      const subject=document.getElementById('skillsSubject').value;
      const subjects=[...new Set((data.habilidades_por_nivel?.geral||[]).map(r=>r.disciplina))].sort();
      this.select('skillsSubject',subjects.map(x=>({value:x,label:x})),'Todas as disciplinas',subject);
      this.pendingPage=1;
      this.pendingTotal=data.total_alunos_pendentes||0;
      document.getElementById('pendingStudentsSearch').value='';
      const storedUser = API.getStoredUser();
      const canSimulate = storedUser?.hierarquia === 'Master' || !!storedUser?.pode_simular_visao;
      const hierarchyOrder = ['Master','Administrador','uniao','associacao','escola'];
      const ownIndex = hierarchyOrder.indexOf(storedUser?.hierarquia);
      const availableLevels = hierarchyOrder.slice(ownIndex + 1).filter(level => ['Administrador','uniao','associacao','escola'].includes(level));
      const previewSelect = document.getElementById('previewNivel');
      const currentPreview = previewSelect.value;
      const roleLabels = {Master:'Master',Administrador:'Administrador',uniao:'União',associacao:'Associação',escola:'Escola'};
      previewSelect.innerHTML = `<option value="">${roleLabels[storedUser?.hierarquia] || 'Minha'} — visão atual</option>` + availableLevels.map(level => `<option value="${level}">${roleLabels[level]}</option>`).join('');
      previewSelect.value = availableLevels.includes(currentPreview) ? currentPreview : '';
      document.getElementById('previewBar').classList.toggle('hidden', !canSimulate || !availableLevels.length);
      if (canSimulate) { this.catalog=data.entidades_catalogo||[]; this.updatePreview('init'); }
      this.entities=data.entidades_acessiveis||[];
      const union=document.getElementById('reportFilterUniao').value;
      const unions=[...new Set(this.entities.map(x=>x.uniao).filter(Boolean))].sort();
      this.select('reportFilterUniao',unions.map(x=>({value:x,label:x})),'Todas as uniões',union);
      if (!document.getElementById('reportFilterAno').options.length) {
        this.select('reportFilterAno',(data.anos_disponiveis||[]).map(x=>({value:x,label:x})),'Todos os anos');
        this.select('reportFilterBimestre',(data.bimestres_disponiveis||[]).map(x=>({value:x,label:x})),'Todos os bimestres');
      }
      this.updateFilters('init');
      document.getElementById('reportSubtitle').textContent=data.simulando?`Prévia do perfil ${data.perfil}: dados limitados ao escopo escolhido.`:`Visão ${data.perfil} · resultados e participação`;
      document.getElementById('topbarScopeTag').textContent=data.simulando?`Simulando: ${data.perfil}`:`Escopo: ${data.perfil}`;
      this.render(); status.className='report-status hidden';
      if (forceRefresh) App.showToast('Dados atualizados com sucesso.', 'success');
      PdfFilters.populateStatic(data);
    } catch (error) {
      if (seq===this.sequence) { status.textContent='Não foi possível carregar os dados: '+error.message; status.className='report-status error'; }
    } finally {
      if (seq===this.sequence) document.getElementById('viewReports').classList.remove('loading');
    }
  },
  clearFilters() {
    for (const id of ['reportFilterUniao','reportFilterAssoc','reportFilterEscola','reportFilterAno','reportFilterBimestre']) document.getElementById(id).value='';
    this.updateFilters('reportFilterUniao'); this.loadReports();
  },
  render() {
    const d=this.data,k=d.kpis;
    for (const [id,value] of Object.entries({kpiTotalAlunos:this.num(k.total_alunos),kpiMediaGeral:this.pct(k.media_geral),kpiTotalSimulados:this.num(k.total_simulados),kpiSimuladosRespondidos:this.num(k.simulados_respondidos),kpiSimuladosNaoRespondidos:this.num(k.simulados_nao_respondidos),kpiTotalEscolas:this.num(k.total_escolas),kpiParticipacao:this.pct(k.participacao),kpiQuestoes:this.num(k.questoes_respondidas)})) document.getElementById(id).textContent=value;
    const noteText = d.criterio_minimo_questoes ? `A partir de ${d.criterio_minimo_questoes} questões ou múltiplos simulados.` : 'Amostra reduzida neste filtro.';
    const bestNote = document.getElementById('studentRankingNote');
    if (bestNote) bestNote.textContent = noteText;
    const attNote = document.getElementById('attentionRankingNote');
    if (attNote) attNote.textContent = noteText;
    const levels = Object.keys(d.rankings || {});
    if (!levels.includes(this.level) || (d.visao && this.lastVision !== d.visao)) {
      this.level = levels.includes('uniao') ? 'uniao' : (levels[0] || 'escola');
      this.lastVision = d.visao;
    }
    document.querySelectorAll('[data-rank]').forEach(b => {
      const show = levels.includes(b.dataset.rank);
      b.classList.toggle('hidden', !show);
      b.classList.toggle('active', b.dataset.rank === this.level);
    });
    document.querySelectorAll('[data-bim-tab="uniao"]').forEach(b => b.classList.toggle('hidden', !levels.includes('uniao')));
    document.querySelectorAll('[data-bim-tab="associacao"]').forEach(b => b.classList.toggle('hidden', !levels.includes('associacao')));
    if (this.bimonthlyTab === 'uniao' && !levels.includes('uniao')) {
      this.bimonthlyTab = levels.includes('associacao') ? 'associacao' : 'escola';
    } else if (this.bimonthlyTab === 'associacao' && !levels.includes('associacao')) {
      this.bimonthlyTab = 'escola';
    }
    document.querySelectorAll('[data-bim-tab]').forEach(b => b.classList.toggle('active', b.dataset.bimTab === this.bimonthlyTab));
    this.renderSubjects();this.renderRankings();this.renderStudents('melhores_alunos','bestStudents');this.renderStudents('alunos_atencao','attentionStudents');this.renderParticipation();this.renderInsights();this.renderEvolution();this.renderDifficulty();this.renderSeries();this.renderPending();this.renderMatrix();this.renderSchools();this.renderSkills();this.renderBimonthly();this.renderSimulados();this.renderAnalysisNotes();
  },
  analysisNotes() {
    const d = this.data || {};
    const enough = rows => rows.filter(row => Number(row.acertos || 0) + Number(row.erros || 0) >= 30 && row.taxa_acerto != null);
    const subjects = enough(d.por_disciplina || []).sort((a, b) => a.taxa_acerto - b.taxa_acerto);
    const disciplines = !subjects.length
      ? 'Ainda não há disciplinas com pelo menos 30 respostas avaliadas para comparar neste filtro.'
      : subjects.length === 1
        ? `${subjects[0].disciplina} apresenta ${this.pct(subjects[0].taxa_acerto)} de acertos em ${this.num(subjects[0].acertos + subjects[0].erros)} respostas avaliadas.`
        : `${subjects[0].disciplina} tem o menor percentual de acertos (${this.pct(subjects[0].taxa_acerto)}), enquanto ${subjects.at(-1).disciplina} tem o maior (${this.pct(subjects.at(-1).taxa_acerto)}), entre disciplinas com pelo menos 30 respostas.`;

    const rankRows = d.rankings?.[this.level] || [];
    const visible = rankRows.filter(row => row.media_acerto != null && row.nome && row.nome !== 'Instituição reservada');
    const rankLabel = {uniao:'uniões', associacao:'associações', escola:'escolas'}[this.level] || 'instituições';
    const leader = visible[0];
    const ranking = !leader
      ? `Não há desempenho visível para comparar ${rankLabel} neste filtro.`
      : `${leader.nome} aparece em ${leader.posicao}º entre ${rankLabel}, com ${this.pct(leader.media_acerto)} de desempenho médio.${rankRows.some(row => row.nome === 'Instituição reservada') ? ' Algumas instituições têm identidade protegida.' : ''}`;

    const participationRows = (d.participacao_bimestre || []).filter(row => Number(row.esperados) > 0);
    const lowestParticipation = [...participationRows].sort((a, b) => a.fizeram / a.esperados - b.fizeram / b.esperados)[0];
    const participation = lowestParticipation
      ? `${lowestParticipation.bimestre} registra a menor participação: ${this.num(lowestParticipation.fizeram)} de ${this.num(lowestParticipation.esperados)} alunos esperados (${this.pct(100 * lowestParticipation.fizeram / lowestParticipation.esperados)}).`
      : 'Ainda não há alunos esperados por bimestre neste filtro.';

    const evolutionRows = (d.evolucao_bimestre || []).filter(row => row.taxa_acerto != null && Number(row.esperados) > 0);
    let evolution = 'Ainda não há dois bimestres com resultado para comparar a evolução.';
    if (evolutionRows.length === 1) {
      const row = evolutionRows[0];
      evolution = `Em ${row.bimestre}, o desempenho médio foi ${this.pct(row.taxa_acerto)} e a participação foi ${this.pct(100 * row.fizeram / row.esperados)}.`;
    } else if (evolutionRows.length > 1) {
      const first = evolutionRows[0], last = evolutionRows.at(-1);
      const delta = last.taxa_acerto - first.taxa_acerto;
      evolution = delta === 0
        ? `No ${first.bimestre} e no ${last.bimestre}, o desempenho médio foi igual: ${this.pct(first.taxa_acerto)}.`
        : `Do ${first.bimestre} ao ${last.bimestre}, o desempenho médio ${delta > 0 ? 'subiu' : 'caiu'} de ${this.pct(first.taxa_acerto)} para ${this.pct(last.taxa_acerto)} (${delta > 0 ? '+' : ''}${Number(delta.toFixed(1)).toLocaleString('pt-BR')} ${Math.abs(delta) === 1 ? 'ponto percentual' : 'pontos percentuais'}).`;
    }

    const difficultyRows = enough(d.por_dificuldade || []).sort((a, b) => a.taxa_acerto - b.taxa_acerto);
    const difficulty = difficultyRows.length === 1
      ? `No nível ${difficultyRows[0].dificuldade || 'Não informada'}, houve ${this.pct(difficultyRows[0].taxa_acerto)} de acertos em ${this.num(difficultyRows[0].acertos + difficultyRows[0].erros)} respostas.`
      : difficultyRows.length
      ? `${difficultyRows[0].dificuldade || 'Não informada'} apresenta o menor percentual de acertos entre os níveis com pelo menos 30 respostas: ${this.pct(difficultyRows[0].taxa_acerto)} em ${this.num(difficultyRows[0].acertos + difficultyRows[0].erros)} respostas.`
      : 'Ainda não há respostas suficientes por nível de dificuldade para comparar os percentuais.';

    const seriesRows = (d.por_serie || []).filter(row => Number(row.esperados) >= 30);
    const lowestSeries = [...seriesRows].sort((a, b) => a.participacao - b.participacao)[0];
    const series = seriesRows.length === 1
      ? `${lowestSeries.serie} registra ${this.num(lowestSeries.fizeram)} de ${this.num(lowestSeries.esperados)} alunos participantes (${this.pct(lowestSeries.participacao)}).`
      : lowestSeries
      ? `${lowestSeries.serie} tem a menor participação entre as séries com pelo menos 30 alunos esperados: ${this.num(lowestSeries.fizeram)} de ${this.num(lowestSeries.esperados)} (${this.pct(lowestSeries.participacao)}).`
      : 'Ainda não há séries com pelo menos 30 alunos esperados para comparar a participação.';

    const matrixRows = enough(d.matriz_disciplina_dificuldade || []).sort((a, b) => a.taxa_acerto - b.taxa_acerto);
    const matrix = matrixRows.length === 1
      ? `Em ${matrixRows[0].disciplina} / ${matrixRows[0].dificuldade || 'Não informada'}, houve ${this.pct(matrixRows[0].taxa_acerto)} de acertos em ${this.num(matrixRows[0].acertos + matrixRows[0].erros)} respostas.`
      : matrixRows.length
      ? `A combinação ${matrixRows[0].disciplina} / ${matrixRows[0].dificuldade || 'Não informada'} tem o menor percentual de acertos entre as células com pelo menos 30 respostas: ${this.pct(matrixRows[0].taxa_acerto)} em ${this.num(matrixRows[0].acertos + matrixRows[0].erros)} respostas.`
      : 'Ainda não há combinações de disciplina e dificuldade com pelo menos 30 respostas para comparar.';

    const schoolTerm = (document.getElementById('schoolAnalysisSearch')?.value || '').toLocaleLowerCase('pt-BR');
    const shownSchools = (d.escolas_resumo || []).filter(row => String(row.escola || '').toLocaleLowerCase('pt-BR').includes(schoolTerm)).slice(0, 50);
    const comparableSchools = shownSchools.filter(row => Number(row.esperados) >= 30).sort((a, b) => a.participacao - b.participacao);
    const schools = comparableSchools.length === 1
      ? `${comparableSchools[0].escola} registra ${this.num(comparableSchools[0].fizeram)} de ${this.num(comparableSchools[0].esperados)} alunos participantes (${this.pct(comparableSchools[0].participacao)}).`
      : comparableSchools.length
      ? `Entre as escolas exibidas com pelo menos 30 alunos esperados, ${comparableSchools[0].escola} tem a menor participação: ${this.num(comparableSchools[0].fizeram)} de ${this.num(comparableSchools[0].esperados)} (${this.pct(comparableSchools[0].participacao)}).`
      : 'Nenhuma escola exibida tem pelo menos 30 alunos esperados para comparar a participação.';

    return {disciplinasContainer:disciplines, rankingContainer:ranking, participationContainer:participation,
      evolutionContainer:evolution, difficultyContainer:difficulty, seriesTableBody:series,
      subjectDifficultyMatrix:matrix, schoolAnalysisBody:schools};
  },
  renderAnalysisNotes() {
    if (!this.data) return;
    for (const [anchorId, message] of Object.entries(this.analysisNotes())) {
      const anchor = document.getElementById(anchorId);
      if (!anchor) continue;
      const placement = anchorId === 'rankingContainer' ? anchor.parentElement
        : ['seriesTableBody', 'schoolAnalysisBody'].includes(anchorId) ? anchor.closest('.table-responsive') : anchor;
      const noteId = `${anchorId}Analysis`;
      let note = document.getElementById(noteId);
      if (!note) {
        note = document.createElement('div');
        note.id = noteId;
        note.className = 'analysis-comment';
        const label = document.createElement('strong');
        label.textContent = 'Leitura do visual';
        const paragraph = document.createElement('p');
        note.append(label, paragraph);
        placement.insertAdjacentElement('afterend', note);
      }
      note.querySelector('p').textContent = message;
    }
  },
  skillRows() {
    const term=this.fold(document.getElementById('skillsSearch').value),subject=document.getElementById('skillsSubject').value;
    const rows=(this.data?.habilidades_por_nivel?.[this.skillLevel]||[]).filter(r=>(!subject||r.disciplina===subject)&&this.fold([r.nome,r.ra,r.habilidade,r.descricao,r.disciplina,r.uniao,r.associacao,r.escola].join(' ')).includes(term));
    const sort=document.getElementById('skillsSort').value;
    return rows.sort((a,b)=>(sort==='high'?b.taxa_acerto-a.taxa_acerto:sort==='errors'?b.erros-a.erros:sort==='volume'?b.questoes-a.questoes:a.taxa_acerto-b.taxa_acerto)||b.questoes-a.questoes||a.habilidade.localeCompare(b.habilidade));
  },
  skillInstitutionHtml(r) {
    if(this.skillLevel==='aluno') return `<strong>${this.esc(r.nome||'Aluno')}</strong><small>RA: ${this.esc(r.ra||'N/I')} · Turma: ${this.esc(r.turma||'N/I')} · Série: ${this.esc(r.nivel_serie||'N/I')}</small><small>${this.esc(r.escola)} · ${this.esc(r.uniao)} / ${this.esc(r.associacao)}</small>`;
    return this.esc(this.skillLevel==='escola'?r.escola:this.skillLevel==='associacao'?`${r.uniao} / ${r.associacao}`:this.skillLevel==='uniao'?r.uniao:'Total do escopo');
  },
  skillInstitutionCsv(r) {
    if(this.skillLevel==='aluno') return `${r.nome||'Aluno'} (RA: ${r.ra||'N/I'}, Turma: ${r.turma||'N/I'}, Série: ${r.nivel_serie||'N/I'}) - ${r.escola}`;
    return this.skillLevel==='escola'?r.escola:this.skillLevel==='associacao'?`${r.uniao} / ${r.associacao}`:this.skillLevel==='uniao'?r.uniao:'Total do escopo';
  },
  renderSkills() {
    if(!this.data)return;
    const rows=this.skillRows(),pages=Math.max(1,Math.ceil(rows.length/30));
    this.skillPage=Math.max(1,Math.min(this.skillPage,pages));
    document.querySelectorAll('[data-skill-level]').forEach(b=>b.classList.toggle('active',b.dataset.skillLevel===this.skillLevel));
    document.querySelector('.skills-table th:first-child').textContent = this.skillLevel === 'aluno' ? 'Aluno / Detalhes' : 'Instituição';
    document.getElementById('skillsReportNote').textContent='Dados dos simulados realizados no escopo e nos filtros ativos. Cada habilidade é vinculada à sua disciplina.';
    document.getElementById('skillsReportBody').innerHTML=rows.length?rows.slice((this.skillPage-1)*30,this.skillPage*30).map(r=>`<tr><td>${this.skillInstitutionHtml(r)}</td><td><strong>${this.esc(r.habilidade)}</strong><small>${this.esc(r.disciplina)}</small></td><td class="skill-description">${this.esc(r.descricao||'Sem descrição cadastrada')}</td><td>${this.num(r.alunos)}</td><td>${this.num(r.simulados)}</td><td>${this.num(r.questoes)}</td><td>${this.num(r.acertos)}</td><td>${this.num(r.erros)}</td><td><span class="matrix-cell ${r.taxa_acerto<40?'low':r.taxa_acerto>=70?'high':''}">${this.pct(r.taxa_acerto)}</span>${r.questoes<10?'<small class="text-muted">Amostra pequena</small>':''}</td></tr>`).join(''):'<tr><td colspan="9" class="empty-state">Nenhuma habilidade encontrada com respostas avaliadas neste recorte.</td></tr>';
    document.getElementById('skillsPageNote').textContent=`${this.num(rows.length)} registros · página ${this.skillPage} de ${pages}`;
    document.getElementById('skillsPrevious').disabled=this.skillPage===1;
    document.getElementById('skillsNext').disabled=this.skillPage===pages;
  },
  exportSkills() {
    const rows=this.skillRows();if(!rows.length)return App.showToast('Nenhuma habilidade para exportar.','warning');
    const cell=x=>`"${String(x??'').replace(/"/g,'""')}"`;
    const csv='\ufeffInstituição,Disciplina,Habilidade,Descrição,Alunos,Simulados feitos,Respostas,Acertos,Erros,Taxa de acerto\n'+rows.map(r=>[this.skillInstitutionCsv(r),r.disciplina,r.habilidade,r.descricao,r.alunos,r.simulados,r.questoes,r.acertos,r.erros,r.taxa_acerto].map(cell).join(',')).join('\n');
    const url=URL.createObjectURL(new Blob([csv],{type:'text/csv;charset=utf-8'}));const a=document.createElement('a');a.href=url;a.download=`habilidades_${this.skillLevel}.csv`;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
  },
  exportStudentSkills() {
    const d=this.studentDetail,rows=d?.habilidades||[];
    if(!rows.length)return App.showToast('Nenhuma habilidade para exportar.','warning');
    const cell=x=>`"${String(x??'').replace(/"/g,'""')}"`;
    const csv='\ufeffAluno,Disciplina,Habilidade,Descrição,Simulados feitos,Questões,Acertos,Erros,Taxa de acerto\n'+rows.map(r=>[d.nome,r.disciplina,r.habilidade,r.descricao,r.simulados,r.questoes,r.acertos,r.erros,r.taxa_acerto].map(cell).join(',')).join('\n');
    const url=URL.createObjectURL(new Blob([csv],{type:'text/csv;charset=utf-8'}));const a=document.createElement('a');a.href=url;a.download='habilidades_aluno.csv';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
  },
  renderSubjects() {
    const rows=this.data.por_disciplina||[];
    document.getElementById('disciplinasContainer').innerHTML=rows.length?rows.map(r=>`<div class="progress-item"><div class="progress-header"><span>${this.esc(r.disciplina)}</span><strong>${this.pct(r.taxa_acerto)} acertos</strong></div><div class="progress-bar-bg"><div class="progress-bar-fill green" style="width:${r.taxa_acerto}%"></div></div><small class="text-muted">${this.pct(100-r.taxa_acerto)} erros · ${this.num(r.acertos)} acertos · ${this.num(r.erros)} erros</small></div>`).join(''):'<p class="empty-state">Sem respostas para este período.</p>';
  },
  renderRankings() {
    const rows=this.data.rankings?.[this.level]||[];
    document.getElementById('rankingContainer').innerHTML=rows.length?rows.map(r=>`<div class="ranking-row ${r.proprio?'own':''}"><span class="rank-position">${r.posicao==null?'—':`${r.posicao}º`}</span><div class="rank-name"><strong>${this.esc(r.nome)}</strong><small>${r.proprio?(r.media_acerto==null?'Sem resultado':`${this.num(r.esperados||0)} previstos · ${this.num(r.fizeram||0)} feitos · ${this.num((r.esperados||0)-(r.fizeram||0))} não feitos`):'Identidade protegida'}</small></div><strong class="rank-score">${r.media_acerto==null?(r.proprio?'—':'•••'):this.pct(r.media_acerto)}</strong></div>`).join(''):'<p class="empty-state">Sem instituições neste escopo.</p>';
  },
  renderStudents(key,id) {
    const allRows = this.data[key]||[];
    const rows = key === 'alunos_consulta' ? allRows : allRows.slice(0, 100);
    document.getElementById(id).innerHTML=rows.length?rows.map((r,i)=>`<button class="student-row" data-student-list="${key}" data-index="${i}"><span class="student-avatar">${this.esc((r.nome||'?')[0])}</span><span class="student-identity"><strong>${this.esc(r.nome)}</strong><small>${this.esc(r.school_key)} · ${this.num(r.simulados)} simulados · ${this.num(r.questoes)} questões</small></span><strong class="student-score">${r.taxa_acerto==null?'—':this.pct(r.taxa_acerto)}</strong><span aria-hidden="true">›</span></button>`).join(''):`<p class="empty-state">${key==='alunos_consulta'?'Nenhum aluno encontrado.':'Sem alunos avaliados.'}</p>`;
  },
  async loadStudentDirectory(reset) {
    if(!this.data)return;
    const request=++this.directoryRequest,seq=this.sequence,page=reset?1:this.directoryPage+1;
    const button=document.getElementById('studentDirectoryMore'),note=document.getElementById('studentDirectoryNote');
    note.textContent='Consultando alunos…';button.disabled=true;
    try {
      const result=await API.getReportStudents({...this.filters(),pagina:page,busca:document.getElementById('studentDirectorySearch').value.trim()});
      if(request!==this.directoryRequest||seq!==this.sequence)return;
      this.data.alunos_consulta=reset?result.alunos:[...(this.data.alunos_consulta||[]),...result.alunos];
      this.directoryPage=page;
      this.renderStudents('alunos_consulta','studentDirectoryList');
      note.textContent=`${this.num(result.total)} alunos encontrados · ${this.num(this.data.alunos_consulta.length)} exibidos`;
      button.classList.toggle('hidden',this.data.alunos_consulta.length>=result.total);
    } catch(error) {if(request===this.directoryRequest&&seq===this.sequence)note.textContent=error.message;}
    finally {if(request===this.directoryRequest)button.disabled=false;}
  },
  renderParticipation() {
    const rows=this.data.participacao_bimestre||[];
    document.getElementById('participationContainer').innerHTML=rows.length?rows.map(r=>{const pct=r.esperados?Math.round(100*r.fizeram/r.esperados):0;return `<details class="participation-group"><summary><span><strong>${this.esc(r.bimestre)}</strong><small>${this.num(r.fizeram)} de ${this.num(r.esperados)} alunos</small></span><span class="participation-meter"><i style="width:${pct}%"></i></span><strong>${pct}%</strong></summary><div class="participation-schools">${r.escolas.slice(0, 100).map(s=>`<div><span>${this.esc(s.escola)}</span><strong>${this.num(s.fizeram)} / ${this.num(s.esperados)}</strong></div>`).join('')}</div></details>`}).join(''):'<p class="empty-state">Sem participação para o período.</p>';
  },
  renderInsights() {
    const d=this.data,missing=(d.participacao_bimestre||[]).reduce((n,r)=>n+Math.max(0,r.esperados-r.fizeram),0);
    const subject=(d.por_disciplina||[]).filter(r=>r.acertos+r.erros>=30).sort((a,b)=>a.taxa_acerto-b.taxa_acerto)[0];
    const school=(d.escolas_resumo||[]).filter(r=>r.esperados>=30).sort((a,b)=>a.participacao-b.participacao)[0];
    const cards=[{label:'Oportunidade de participação',value:this.num(missing),note:'participações previstas ainda não realizadas nos bimestres exibidos'},
      {label:'Disciplina prioritária',value:subject?.disciplina||'Sem dados',note:subject?`${this.pct(subject.taxa_acerto)} de acerto em ${this.num(subject.acertos+subject.erros)} respostas`:'Sem respostas avaliadas'},
      {label:'Escola para acompanhamento',value:school?.escola||'Sem dados',note:school?`${this.pct(school.participacao)} de participação · ${this.num(school.esperados)} esperados`:'Sem escola com ao menos 30 alunos esperados'}];
    document.getElementById('insightsContainer').innerHTML=cards.map(c=>`<div class="insight-card"><span>${this.esc(c.label)}</span><strong>${this.esc(c.value)}</strong><small>${this.esc(c.note)}</small></div>`).join('');
  },
  renderEvolution() {
    const rows=this.data.evolucao_bimestre||[];
    document.getElementById('evolutionContainer').innerHTML=rows.length?`<div class="analysis-legend"><span><i class="green-dot"></i>Participação</span><span><i class="purple-dot"></i>Desempenho médio</span></div>`+rows.map(r=>{const part=r.esperados?100*r.fizeram/r.esperados:0;return `<div class="evolution-row"><strong>${this.esc(r.bimestre)}</strong><small>${this.num(r.fizeram)} participantes · ${this.num(r.simulados)} simulados</small><div class="dual-bar"><i class="participation" style="width:${Math.min(100,part)}%"></i><i class="achievement" style="width:${Math.min(100,r.taxa_acerto||0)}%"></i></div><div class="dual-values"><span>${this.pct(part)} participação</span><span>${r.taxa_acerto==null?'—':this.pct(r.taxa_acerto)} desempenho</span></div></div>`}).join(''):'<p class="empty-state">Sem evolução para o período.</p>';
  },
  renderDifficulty() {
    const rows=this.data.por_dificuldade||[];
    document.getElementById('difficultyContainer').innerHTML=rows.length?rows.map(r=>`<div class="difficulty-card"><div><strong>${this.esc(r.dificuldade||'Não informada')}</strong><small>${this.num(r.acertos+r.erros)} respostas · ${this.pct(100-r.taxa_acerto)} erros</small></div><strong>${this.pct(r.taxa_acerto)} acertos</strong><div class="progress-bar-bg"><div class="progress-bar-fill green" style="width:${r.taxa_acerto}%"></div></div></div>`).join(''):'<p class="empty-state">Sem respostas avaliadas.</p>';
  },
  renderSeries() {
    const rows=this.data.por_serie||[];
    document.getElementById('seriesTableBody').innerHTML=rows.length?rows.map(r=>`<tr><td><strong>${this.esc(r.serie)}</strong></td><td>${this.num(r.esperados)}</td><td>${this.num(r.fizeram)}</td><td>${this.pct(r.participacao)}</td><td>${r.taxa_acerto==null?'—':this.pct(r.taxa_acerto)}</td></tr>`).join(''):'<tr><td colspan="5" class="empty-state">Sem dados por série.</td></tr>';
  },
  renderPending() {
    const rows=this.data.alunos_pendentes||[];
    const total=this.pendingTotal;
    document.getElementById('pendingStudentsNote').textContent=total>rows.length?`${this.num(total)} sem simulado · exibindo ${this.num(rows.length)}`:`${this.num(total)} sem simulado no total`;
    document.getElementById('pendingStudents').innerHTML=rows.length?rows.map((r,i)=>`<button class="pending-row" data-student-list="alunos_pendentes" data-index="${i}"><span class="student-avatar">${this.esc((r.nome||'?')[0])}</span><div><strong>${this.esc(r.nome)}</strong><small>${this.esc(r.escola)} · ${this.esc(r.nivel_serie||r.serie||'Série não informada')}</small></div><span class="badge-not-done">Não feito: ${this.num(r.simulados_previstos)}</span></button>`).join(''):'<p class="empty-state">Nenhum aluno sem simulado realizado neste filtro.</p>';
    document.getElementById('pendingStudentsMore').classList.toggle('hidden',rows.length>=total);
  },
  async loadPending(reset) {
    if (!this.data) return;
    const request=++this.pendingRequest, reportSeq=this.sequence;
    const nextPage=reset?1:this.pendingPage+1;
    const button=document.getElementById('pendingStudentsMore');
    button.disabled=true;
    try {
      const result=await API.getPendingStudents({...this.filters(),pagina:nextPage,
        busca:document.getElementById('pendingStudentsSearch').value.trim()});
      if (request!==this.pendingRequest || reportSeq!==this.sequence) return;
      this.data.alunos_pendentes=reset?result.alunos:[...this.data.alunos_pendentes,...result.alunos];
      this.pendingPage=nextPage;
      this.pendingTotal=result.total;
      this.renderPending();
    } catch(error) {
      if (request===this.pendingRequest) document.getElementById('pendingStudentsNote').textContent=error.message;
    } finally {if (request===this.pendingRequest) button.disabled=false;}
  },
  renderMatrix() {
    const rows=this.data.matriz_disciplina_dificuldade||[],subjects=[...new Set(rows.map(r=>r.disciplina).filter(Boolean))],difficulties=[...new Set(rows.map(r=>r.dificuldade||'Não informada'))];
    const order=['Fácil','Médio','Difícil'];difficulties.sort((a,b)=>(order.indexOf(a)<0?99:order.indexOf(a))-(order.indexOf(b)<0?99:order.indexOf(b)));
    document.getElementById('subjectDifficultyMatrix').innerHTML=rows.length?`<div class="table-responsive"><table class="table analysis-table matrix-table"><thead><tr><th>Disciplina</th>${difficulties.map(x=>`<th>${this.esc(x)}</th>`).join('')}</tr></thead><tbody>${subjects.map(subject=>`<tr><td><strong>${this.esc(subject)}</strong></td>${difficulties.map(diff=>{const r=rows.find(x=>x.disciplina===subject&&(x.dificuldade||'Não informada')===diff);return `<td>${r?`<span class="matrix-cell ${r.taxa_acerto<40?'low':r.taxa_acerto>=70?'high':''}">${this.pct(r.taxa_acerto)} acertos<small>${this.pct(100-r.taxa_acerto)} erros · ${this.num(r.acertos+r.erros)} questões</small></span>`:'—'}</td>`}).join('')}</tr>`).join('')}</tbody></table></div>`:'<p class="empty-state">Sem respostas para cruzar disciplina e dificuldade.</p>';
  },
  renderSchools() {
    if (!this.data) return;
    const term=(document.getElementById('schoolAnalysisSearch').value||'').toLocaleLowerCase('pt-BR');
    const rows=(this.data.escolas_resumo||[]).filter(r=>r.escola.toLocaleLowerCase('pt-BR').includes(term)).slice(0, 50);
    document.getElementById('schoolAnalysisBody').innerHTML=rows.length?rows.map(r=>`<tr><td><strong>${this.esc(r.escola)}</strong><small>${this.esc(r.uniao)} / ${this.esc(r.associacao)}</small></td><td>${this.num(r.esperados)}</td><td>${this.num(r.fizeram)}</td><td><span class="metric-pill ${r.participacao<20?'low':''}">${this.pct(r.participacao)}</span></td><td>${r.taxa_acerto==null?'—':this.pct(r.taxa_acerto)}</td></tr>`).join(''):'<tr><td colspan="5" class="empty-state">Nenhuma escola encontrada.</td></tr>';
  },
  renderSimulados() {
    if (!this.data) return;
    const term = (document.getElementById('simuladosSearch')?.value || '').toLowerCase();
    let rows = this.data.simulados_disponiveis || [];
    
    // Deduplicate by id_simulado and uniao
    let deduplicated = [];
    const seen = new Set();
    rows.forEach(r => {
      const key = r.id_simulado + '|' + r.uniao;
      if (!seen.has(key)) {
        seen.add(key);
        // Clean up the name here as well
        const cleanNome = (r.nome_simulado || r.id_simulado).replace(/ - [A-Za-z0-9]+ - .*?(?:Aluno|Alunos).*$/i, '');
        r.nome_simulado_clean = cleanNome;
        deduplicated.push(r);
      } else {
        // Aggregate fizeram count
        const existing = deduplicated.find(d => d.id_simulado === r.id_simulado && d.uniao === r.uniao);
        if (existing) existing.fizeram = (existing.fizeram || 0) + (r.fizeram || 0);
      }
    });

    deduplicated = deduplicated.filter(r => !term || this.fold(`${r.id_simulado} ${r.nome_simulado_clean || ''}`).includes(this.fold(term)))
      .sort((a, b) => {
         const yearA = a.ano || ''; const yearB = b.ano || '';
         if (yearA !== yearB) return yearB.localeCompare(yearA);
         const bimA = a.bimestre || ''; const bimB = b.bimestre || '';
         return bimB.localeCompare(bimA);
      });

    document.getElementById('simuladosListTable').innerHTML = deduplicated.length ? deduplicated.slice(0, 100).map(r => {
      return `<tr onclick="openSimuladoModal('${this.esc(r.id_simulado)}', '${this.esc(r.nome_simulado_clean)}', '${this.esc(r.uniao)}')" style="cursor: pointer;"><td style="font-weight: 600;"><div style="color: #334155; font-size: 0.9rem;">${this.esc(r.nome_simulado_clean)} ${r.fizeram === 0 ? '<span class="badge" style="background: #e2e8f0; color: #64748b; margin-left: 8px;">Vazio</span>' : ''}</div><div style="font-size: 0.75rem; color: #64748b; font-weight: 500; margin-top: 4px;">ID: ${this.esc(r.id_simulado)}</div></td><td>${this.esc(r.uniao)}</td><td class="text-center"><button class="btn btn-outline btn-sm">Ver Detalhes</button></td></tr>`;
    }).join('') : '<tr><td colspan="5" class="empty-state">Nenhum simulado disponível neste período.</td></tr>';
  },
  async openStudent(key,index) {
    const student=this.data?.[key]?.[index];if (!student) return;
    const request=++this.studentRequest;
    const modal=document.getElementById('studentModal');
    document.getElementById('studentModalTitle').textContent=student.nome||'Aluno';
    document.getElementById('studentModalBody').innerHTML='<p class="empty-state">Carregando análise...</p>';
    modal.classList.add('active');
    try {
      const f=this.filters();
      const detail=await API.getStudentReport({escola:student.school_key,aluno:student.student_key,ano:f.ano||'',bimestre:f.bimestre||'',preview_nivel:f.preview_nivel||'',preview_uniao:f.preview_uniao||'',preview_associacao:f.preview_associacao||'',preview_escola:f.preview_escola||''});
      if (request===this.studentRequest && modal.classList.contains('active')) this.renderStudentDetail(detail);
    } catch(error) {if(request===this.studentRequest)document.getElementById('studentModalBody').innerHTML=`<p class="empty-state">${this.esc(error.message)}</p>`;}
  },
  closeStudent() {this.studentRequest++;document.getElementById('studentModal')?.classList.remove('active');},
  renderStudentDetail(d) {
    this.studentDetail=d;
    const difficulties=d.dificuldades||[],total=difficulties.reduce((n,x)=>n+x.acertos+x.erros,0),colors=['#5958a5','#76b875','#f2a24e','#e57863','#9ca3af'];
    let angle=0;const stops=difficulties.map((x,i)=>{const start=angle;angle+=100*(x.acertos+x.erros)/(total||1);return `${colors[i%colors.length]} ${start}% ${angle}%`;});
    const done=(d.historico||[]).filter(x=>x.realizado),pending=(d.historico||[]).filter(x=>!x.realizado);
    const skills=(rows,type)=>rows.length?rows.map(x=>`<div class="skill-row"><div><strong>${this.esc(x.habilidade)} · ${this.esc(x.disciplina)}</strong><p>${this.esc(x.descricao||'Sem descrição cadastrada')}</p></div><span>${this.num(x[type])} ${type==='acertos'?'acertos':'erros'}</span></div>`).join(''):`<p class="empty-state">${total?'Nenhuma habilidade com '+(type==='acertos'?'acertos':'erros')+' registrada.':'Detalhamento de habilidades ainda não disponível.'}</p>`;
    const history=rows=>rows.map(x=>`<div><span class="exam-status ${x.realizado?'done':'pending'}">${x.realizado?'Realizado':'Não feito'}</span><div><strong>${this.esc(x.nome||x.id_simulado)}</strong><small>${this.esc(x.bimestre||'')} ${x.data?'· '+this.esc(x.data):''}</small>${x.realizado?`<small>${this.num(x.questoes)} questões · ${this.num(x.acertos)} acertos${x.questoes_detalhadas===0?' · detalhamento ainda não disponível':''}</small>`:''}</div><strong class="exam-score">${x.realizado?this.pct(x.taxa_acerto):'—'}</strong></div>`).join('');
    const coverage=d.simulados?(d.simulados_sem_detalhamento
      ? `Os ${this.num(d.simulados)} simulados realizados entram no resumo. Dificuldade e habilidades usam ${this.num(d.questoes_detalhadas)} questões com detalhamento disponível; ${this.num(d.simulados_sem_detalhamento)} ${d.simulados_sem_detalhamento===1?'simulado tem':'simulados têm'} apenas o resultado consolidado.`
      : `Análises dos ${this.num(d.simulados)} simulados realizados. Simulados não feitos não entram nas taxas de acerto.`)
      : 'Este aluno ainda não tem simulado realizado neste período.';
    const donut=total?`<div class="difficulty-layout"><div class="donut" style="background:conic-gradient(${stops.join(',')})"><span>${this.num(total)}<small>questões analisadas</small></span></div><div class="difficulty-legend">${difficulties.map((x,i)=>`<div><i style="background:${colors[i%colors.length]}"></i><span>${this.esc(x.dificuldade||'Não informada')}</span><strong>${this.num(x.acertos+x.erros)}</strong><small>${this.pct(100*x.acertos/(x.acertos+x.erros))} acerto</small></div>`).join('')}</div></div>`:'<p class="empty-state">Detalhamento por dificuldade ainda não disponível.</p>';
    document.getElementById('studentModalBody').innerHTML=`
      <div class="student-summary"><div><strong>${this.num(d.simulados)} / ${this.num(d.simulados_previstos)}</strong><span>feitos / previstos · ${this.num(d.simulados_pendentes)} não feitos</span></div><div><strong>${this.num(d.questoes)}</strong><span>questões dos simulados feitos</span></div><div><strong>${d.taxa_acerto==null?'—':this.pct(d.taxa_acerto)}</strong><span>desempenho médio (Total Final)</span></div></div>
      <p class="text-muted text-xs">${this.esc(d.serie||'')} ${d.turma?'· Turma '+this.esc(d.turma):''}</p>
      <p class="student-analysis-note">${this.esc(coverage)}</p>
      <div class="modal-section"><h4>Questões por dificuldade</h4>${donut}</div>
      <div class="modal-section"><h4>Acertos e erros por disciplina</h4>${(d.disciplinas||[]).map(x=>`<div class="discipline-line"><span>${this.esc(x.disciplina)}</span><strong>${this.pct(x.taxa_acerto)} acertos</strong><small>${this.pct(100-x.taxa_acerto)} erros · ${this.num(x.acertos)} acertos · ${this.num(x.erros)} erros</small></div>`).join('')||'<p class="empty-state">Sem resultado por disciplina disponível.</p>'}</div>
      <div class="modal-section"><h4>Habilidades com mais acertos</h4>${skills(d.habilidades_mais_acertadas||[],'acertos')}</div>
      <div class="modal-section"><h4>Habilidades com mais erros</h4>${skills(d.habilidades_mais_erradas||[],'erros')}</div>
      <div class="modal-section"><h4>Relatório completo por habilidade (${this.num((d.habilidades||[]).length)})</h4><div class="student-skills-controls"><input id="studentSkillsSearch" class="form-control" type="search" placeholder="Buscar habilidade, disciplina ou descrição" aria-label="Buscar habilidade do aluno"><button id="studentSkillsExport" class="btn btn-outline">Exportar CSV</button></div><div class="table-responsive student-skills-table"><table class="table analysis-table skills-table"><thead><tr><th>Disciplina / habilidade</th><th>Descrição</th><th>Simulados</th><th>Questões</th><th>Acertos</th><th>Erros</th><th>Taxa de acerto</th></tr></thead><tbody id="studentSkillsBody">${(d.habilidades||[]).map(r=>`<tr data-search="${this.esc(this.fold([r.habilidade,r.disciplina,r.descricao].join(' ')))}"><td><strong>${this.esc(r.habilidade)}</strong><small>${this.esc(r.disciplina)}</small></td><td class="skill-description">${this.esc(r.descricao||'Sem descrição cadastrada')}</td><td>${this.num(r.simulados)}</td><td>${this.num(r.questoes)}</td><td>${this.num(r.acertos)}</td><td>${this.num(r.erros)}</td><td>${this.pct(r.taxa_acerto)}</td></tr>`).join('')||'<tr><td colspan="7" class="empty-state">Sem respostas com habilidade cadastrada.</td></tr>'}</tbody></table></div></div>
      <div class="modal-section"><h4>Simulados realizados (${this.num(done.length)})</h4><div class="exam-history completed-exams">${history(done)||'<p class="empty-state">Nenhum realizado neste período.</p>'}</div></div>
      ${pending.length?`<details class="modal-section pending-exams" open><summary><span class="pending-summary-title">Simulados não feitos (${this.num(pending.length)})</span></summary><div class="exam-history">${history(pending)}</div></details>`:''}`;
  },
  exportCsv() {
    const rows=this.data?.rankings?.[this.level]||[];
    if (!rows.length) return App.showToast('Nenhum dado para exportar.','warning');
    const cell=value=>`"${String(value??'').replace(/"/g,'""')}"`;
    const csv='\ufeffPosição,Instituição,Alunos avaliados,Taxa de acerto\n'+rows.map(r=>[r.posicao,r.nome,r.alunos,r.media_acerto].map(cell).join(',')).join('\n');
    const url=URL.createObjectURL(new Blob([csv],{type:'text/csv;charset=utf-8'}));const a=document.createElement('a');a.href=url;a.download=`ranking_${this.level}.csv`;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
  },
  renderBimonthly() {
    const ab = this.data?.analise_bimestral;
    if (!ab) return;

    // Badge do escopo ativo
    const scopeBadge = document.getElementById('bimonthlyScopeBadge');
    if (scopeBadge) {
      scopeBadge.textContent = this.data.simulando ? `Simulação: ${this.data.perfil}` : `Escopo: ${this.data.perfil || 'Rede Geral'}`;
    }

    // 1. Cards de Resumo dos Bimestres
    const kpisGrid = document.getElementById('bimonthlyKpisGrid');
    if (kpisGrid) {
      const evo = ab.evolucao_rede || [];
      if (!evo.length) {
        kpisGrid.innerHTML = '<p class="empty-state">Sem dados bimestrais consolidados neste filtro.</p>';
      } else {
        kpisGrid.innerHTML = evo.map(item => {
          const deltaClass = (item.delta == null) ? 'neutral' : (item.delta > 0 ? 'positive' : (item.delta < 0 ? 'negative' : 'neutral'));
          const deltaText = (item.delta == null) ? 'Base inicial' : (item.delta > 0 ? `↗ +${item.delta} pp` : (item.delta < 0 ? `↘ ${item.delta} pp` : `= 0.0 pp`));
          return `
            <div class="bimonthly-kpi-card">
              <span class="kpi-bim-label">${this.esc(item.bimestre)}</span>
              <div class="kpi-bim-value">
                <span>${item.taxa_acerto != null ? this.pct(item.taxa_acerto) : '—'}</span>
                <span class="kpi-bim-delta ${deltaClass}">${deltaText}</span>
              </div>
              <div class="kpi-bim-sub">
                <strong>${this.num(item.fizeram)}</strong> de ${this.num(item.alunos)} alunos (${this.pct(item.participacao)} pres.)
              </div>
            </div>
          `;
        }).join('');
      }
    }

    // 2. Comparativo Interanual por Bimestre (2026 vs 2025)
    const yearBody = document.getElementById('bimonthlyYearTableBody');
    const badge2025 = document.getElementById('badgeAno2025Status');
    const comp = ab.comparativo_anos || {};
    if (badge2025) {
      if (comp.tem_dados_2025) {
        badge2025.style.background = '#dcfce7';
        badge2025.style.color = '#15803d';
        badge2025.style.borderColor = '#bbf7d0';
        badge2025.textContent = '✓ Dados 2026 e 2025 consolidados';
      } else {
        badge2025.style.background = '#fef3c7';
        badge2025.style.color = '#92400e';
        badge2025.style.borderColor = '#fde68a';
        badge2025.textContent = '⏳ Módulo ativo · Aguardando carga de 2025';
      }
    }

    if (yearBody) {
      const linhas = comp.linhas || [];
      if (!linhas.length) {
        yearBody.innerHTML = '<tr><td colspan="5" class="empty-state">Sem dados comparativos anuais.</td></tr>';
      } else {
        yearBody.innerHTML = linhas.map(l => {
          const t2026 = l.ano_atual?.taxa_acerto != null ? `<strong>${this.pct(l.ano_atual.taxa_acerto)}</strong> <small class="text-muted">(${this.num(l.ano_atual.fizeram)} avaliados)</small>` : '—';
          let t2025 = '<span class="text-muted">Aguardando importação</span>';
          if (l.ano_anterior?.taxa_acerto != null) {
            t2025 = `<strong>${this.pct(l.ano_anterior.taxa_acerto)}</strong> <small class="text-muted">(${this.num(l.ano_anterior.fizeram)} avaliados)</small>`;
          }
          let deltaHtml = '—';
          let statusBadge = '<span class="delta-badge neutral">Base 2026</span>';
          if (l.delta_ano != null) {
            const cls = l.delta_ano > 0 ? 'positive' : (l.delta_ano < 0 ? 'negative' : 'neutral');
            const sign = l.delta_ano > 0 ? '+' : '';
            deltaHtml = `<strong class="delta-badge ${cls}">${sign}${l.delta_ano} pp</strong>`;
            statusBadge = l.delta_ano > 0 ? '<span class="delta-badge positive">Superavit Histórico ↗</span>' : '<span class="delta-badge negative">Atenção Curricular ↘</span>';
          }
          return `
            <tr>
              <td><strong>${this.esc(l.bimestre)}</strong></td>
              <td style="text-align: center;">${t2026}</td>
              <td style="text-align: center;">${t2025}</td>
              <td style="text-align: center;">${deltaHtml}</td>
              <td style="text-align: center;">${statusBadge}</td>
            </tr>
          `;
        }).join('');
      }
    }

    // 3. Atualizar Opções do Seletor de Alunos
    const studentSelect = document.getElementById('bimonthlyStudentSelect');
    if (studentSelect && !studentSelect.options.length) {
      const bimList = ab.bimestres_lista || [];
      let opts = bimList.map(b => `<option value="melhores_${this.esc(b)}">Melhores Alunos · ${this.esc(b)}</option>`).join('');
      opts += '<option value="evolucao_alunos">Evolução Longitudinal dos Alunos</option>';
      studentSelect.innerHTML = opts;
      this.bimonthlyStudentView = studentSelect.value;
    }

    // 4. Renderizar a Tabela da Tab Ativa
    this.renderBimonthlyTable();
  },

  renderBimonthlyTable() {
    const ab = this.data?.analise_bimestral;
    if (!ab) return;

    const thead = document.getElementById('bimonthlyEntityTableHead');
    const tbody = document.getElementById('bimonthlyEntityTableBody');
    const countNote = document.getElementById('bimonthlyCountNote');
    if (!thead || !tbody) return;

    const bims = ab.bimestres_lista || [];
    const term = this.bimonthlySearch || '';

    if (this.bimonthlyTab === 'uniao') {
      thead.innerHTML = `
        <tr style="background: #f8fafc;">
          <th style="padding: 0.75rem 1rem;">União</th>
          ${bims.map(b => `<th style="text-align: center; padding: 0.75rem 0.9rem;">${this.esc(b)}</th>`).join('')}
          <th style="text-align: center; padding: 0.75rem 0.9rem;">Média Geral</th>
          <th style="text-align: center; padding: 0.75rem 0.9rem;">Trajetória</th>
        </tr>
      `;
      const rows = (ab.por_uniao || []).filter(r => !term || this.fold(r.uniao).includes(term));
      if (!rows.length) {
        tbody.innerHTML = '<tr><td colspan="10" class="empty-state">Nenhuma união encontrada para este filtro.</td></tr>';
      } else {
        tbody.innerHTML = rows.map(r => {
          const cells = bims.map(b => {
            const bd = r.bimestres?.[b];
            if (!bd || bd.taxa_acerto == null) return '<td style="text-align: center;" class="text-muted">—</td>';
            const cls = bd.taxa_acerto >= 60 ? 'high' : (bd.taxa_acerto < 45 ? 'low' : '');
            const deltaStr = bd.delta != null ? `<small style="display:block; font-size:0.65rem; color:${bd.delta>=0?'#15803d':'#b91c1c'}">${bd.delta>=0?'+':''}${bd.delta} pp</small>` : '';
            return `<td style="text-align: center;"><span class="matrix-cell ${cls}" style="min-width: 60px; padding: 0.3rem 0.5rem;">${this.pct(bd.taxa_acerto)}</span>${deltaStr}</td>`;
          }).join('');
          return `
            <tr>
              <td><strong>${this.esc(r.uniao)}</strong><small>${this.num(r.fizeram_total)} simulados realizados</small></td>
              ${cells}
              <td style="text-align: center;"><strong>${this.pct(r.media_geral)}</strong></td>
              <td style="text-align: center;"><span class="metric-pill ${r.media_geral>=60?'':'low'}">${this.pct(r.media_geral)}</span></td>
            </tr>
          `;
        }).join('');
      }
      if (countNote) countNote.textContent = `${rows.length} uniões avaliadas`;

    } else if (this.bimonthlyTab === 'associacao') {
      thead.innerHTML = `
        <tr style="background: #f8fafc;">
          <th style="padding: 0.75rem 1rem;">Associação</th>
          <th style="padding: 0.75rem 1rem;">União</th>
          ${bims.map(b => `<th style="text-align: center; padding: 0.75rem 0.9rem;">${this.esc(b)}</th>`).join('')}
          <th style="text-align: center; padding: 0.75rem 0.9rem;">Média Geral</th>
        </tr>
      `;
      const rows = (ab.por_associacao || []).filter(r => !term || this.fold(`${r.associacao} ${r.uniao}`).includes(term));
      if (!rows.length) {
        tbody.innerHTML = '<tr><td colspan="10" class="empty-state">Nenhuma associação encontrada para este filtro.</td></tr>';
      } else {
        tbody.innerHTML = rows.map(r => {
          const cells = bims.map(b => {
            const bd = r.bimestres?.[b];
            if (!bd || bd.taxa_acerto == null) return '<td style="text-align: center;" class="text-muted">—</td>';
            const cls = bd.taxa_acerto >= 60 ? 'high' : (bd.taxa_acerto < 45 ? 'low' : '');
            return `<td style="text-align: center;"><span class="matrix-cell ${cls}" style="min-width: 60px; padding: 0.3rem 0.5rem;">${this.pct(bd.taxa_acerto)}</span></td>`;
          }).join('');
          return `
            <tr>
              <td><strong>${this.esc(r.associacao)}</strong><small>${this.num(r.fizeram_total)} simulados</small></td>
              <td>${this.esc(r.uniao)}</td>
              ${cells}
              <td style="text-align: center;"><strong>${this.pct(r.media_geral)}</strong></td>
            </tr>
          `;
        }).join('');
      }
      if (countNote) countNote.textContent = `${rows.length} associações avaliadas`;

    } else if (this.bimonthlyTab === 'escola') {
      thead.innerHTML = `
        <tr style="background: #f8fafc;">
          <th style="padding: 0.75rem 1rem;">Escola</th>
          <th style="padding: 0.75rem 1rem;">Associação / União</th>
          ${bims.map(b => `<th style="text-align: center; padding: 0.75rem 0.9rem;">${this.esc(b)}</th>`).join('')}
          <th style="text-align: center; padding: 0.75rem 0.9rem;">Média Geral</th>
        </tr>
      `;
      const rows = (ab.por_escola || []).filter(r => !term || this.fold(`${r.escola} ${r.associacao} ${r.uniao}`).includes(term)).slice(0, 100);
      if (!rows.length) {
        tbody.innerHTML = '<tr><td colspan="10" class="empty-state">Nenhuma escola encontrada para este filtro.</td></tr>';
      } else {
        tbody.innerHTML = rows.map(r => {
          const cells = bims.map(b => {
            const bd = r.bimestres?.[b];
            if (!bd || bd.taxa_acerto == null) return '<td style="text-align: center;" class="text-muted">—</td>';
            const cls = bd.taxa_acerto >= 60 ? 'high' : (bd.taxa_acerto < 45 ? 'low' : '');
            return `<td style="text-align: center;"><span class="matrix-cell ${cls}" style="min-width: 60px; padding: 0.3rem 0.5rem;">${this.pct(bd.taxa_acerto)}</span></td>`;
          }).join('');
          return `
            <tr>
              <td><strong>${this.esc(r.escola)}</strong><small>${this.num(r.fizeram_total)} simulados</small></td>
              <td>${this.esc(r.associacao)} <small class="text-muted">(${this.esc(r.uniao)})</small></td>
              ${cells}
              <td style="text-align: center;"><strong>${this.pct(r.media_geral)}</strong></td>
            </tr>
          `;
        }).join('');
      }
      if (countNote) countNote.textContent = `${rows.length} escolas avaliadas`;

    } else if (this.bimonthlyTab === 'aluno') {
      const mode = this.bimonthlyStudentView || '';
      if (mode.startsWith('melhores_')) {
        const bimKey = mode.replace('melhores_', '');
        thead.innerHTML = `
          <tr style="background: #f8fafc;">
            <th style="padding: 0.75rem 1rem;">Aluno / Detalhes</th>
            <th style="padding: 0.75rem 1rem;">Escola</th>
            <th style="padding: 0.75rem 1rem;">Série / Turma</th>
            <th style="text-align: center; padding: 0.75rem 1rem;">Simulados</th>
            <th style="text-align: center; padding: 0.75rem 1rem;">Questões</th>
            <th style="text-align: center; padding: 0.75rem 1rem;">Desempenho médio</th>
          </tr>
        `;
        const list = (ab.por_aluno?.[bimKey] || []).filter(r => !term || this.fold(`${r.nome} ${r.escola} ${r.turma}`).includes(term)).slice(0, 100);
        if (!list.length) {
          tbody.innerHTML = '<tr><td colspan="6" class="empty-state">Sem alunos registrados para este bimestre.</td></tr>';
        } else {
          tbody.innerHTML = list.map((r, i) => `
            <tr>
              <td><strong>${i + 1}º ${this.esc(r.nome)}</strong></td>
              <td>${this.esc(r.escola)}</td>
              <td>${this.esc(r.serie || '—')} <small class="text-muted">Turma: ${this.esc(r.turma || '—')}</small></td>
              <td style="text-align: center;">${this.num(r.simulados)}</td>
              <td style="text-align: center;">${this.num(r.questoes)}</td>
              <td style="text-align: center;"><span class="matrix-cell high" style="padding: 0.3rem 0.55rem;">${this.pct(r.taxa_acerto)}</span></td>
            </tr>
          `).join('');
        }
        if (countNote) countNote.textContent = `${list.length} destaques no ${bimKey}`;

      } else {
        // Evolução contínua dos alunos
        thead.innerHTML = `
          <tr style="background: #f8fafc;">
            <th style="padding: 0.75rem 1rem;">Aluno</th>
            <th style="padding: 0.75rem 1rem;">Escola</th>
            <th style="padding: 0.75rem 1rem;">Série / Turma</th>
            <th style="padding: 0.75rem 1rem;">Bimestres Avaliados</th>
            <th style="text-align: center; padding: 0.75rem 1rem;">Trajetória das Notas</th>
            <th style="text-align: center; padding: 0.75rem 1rem;">Variação (Delta)</th>
          </tr>
        `;
        const list = (ab.alunos_evolucao || []).filter(r => !term || this.fold(`${r.nome} ${r.escola} ${r.turma}`).includes(term)).slice(0, 100);
        if (!list.length) {
          tbody.innerHTML = '<tr><td colspan="6" class="empty-state">Nenhum aluno com múltiplos bimestres avaliados neste recorte.</td></tr>';
        } else {
          tbody.innerHTML = list.map(r => {
            const traj = (r.notas || []).map((n, idx) => `<span>${r.bimestres?.[idx] || ''}: <strong>${n != null ? n + '%' : '—'}</strong></span>`).join(' <span style="color:#94a3b8">→</span> ');
            const cls = r.delta > 0 ? 'positive' : (r.delta < 0 ? 'negative' : 'neutral');
            const sign = r.delta > 0 ? '+' : '';
            return `
              <tr>
                <td><strong>${this.esc(r.nome)}</strong></td>
                <td>${this.esc(r.escola)}</td>
                <td>${this.esc(r.serie || '—')} <small class="text-muted">Turma ${this.esc(r.turma || '—')}</small></td>
                <td><small>${(r.bimestres || []).join(', ')}</small></td>
                <td style="text-align: center; font-size: 0.75rem;">${traj}</td>
                <td style="text-align: center;"><span class="delta-badge ${cls}">${sign}${r.delta} pp</span></td>
              </tr>
            `;
          }).join('');
        }
        if (countNote) countNote.textContent = `${list.length} alunos com evolução longitudinal mapeada`;
      }
    }
  }
};

const PdfFilters = {
  init() {
    for (const id of ['pdfFilterUniao','pdfFilterAssoc','pdfFilterEscola']) {
      document.getElementById(id)?.addEventListener('change', () => this.updateFilters(id));
    }
    document.getElementById('btnPdfClearFilters')?.addEventListener('click', () => {
      ['pdfFilterUniao','pdfFilterAssoc','pdfFilterEscola','pdfFilterBimestre','pdfFilterSerie'].forEach(id => {
        const el = document.getElementById(id);
        if(el) el.value = '';
      });
      this.updateFilters('pdfFilterUniao');
    });
  },
  updateFilters(changed) {
    if (!Reports.entities || !Reports.entities.length) return;
    const u = document.getElementById('pdfFilterUniao').value;
    const oldA = document.getElementById('pdfFilterAssoc').value;
    const oldE = document.getElementById('pdfFilterEscola').value;
    
    const assocs = [...new Set(Reports.entities.filter(x => !u || x.uniao === u).map(x => x.associacao).filter(Boolean))].sort();
    Reports.select('pdfFilterAssoc', assocs.map(x => ({value:x,label:x})), 'Todas as associações', changed === 'pdfFilterUniao' ? '' : oldA);
    
    const a = document.getElementById('pdfFilterAssoc').value;
    const schools = Reports.entities.filter(x => (!u || x.uniao === u) && (!a || x.associacao === a));
    Reports.select('pdfFilterEscola', schools.map(x => ({value:x.id_escolas,label:x.escola})), 'Todas as escolas', ['pdfFilterUniao','pdfFilterAssoc'].includes(changed) ? '' : oldE);
  },
  populateStatic(data) {
    if (!document.getElementById('pdfFilterBimestre').options.length || document.getElementById('pdfFilterBimestre').options.length === 1) {
      Reports.select('pdfFilterBimestre', (data.bimestres_disponiveis||[]).map(x=>({value:x,label:x})), 'Todos os bimestres');
    }
    if (data.por_serie) {
       const series = data.por_serie.map(s => s.serie).sort();
       Reports.select('pdfFilterSerie', series.map(x=>({value:x,label:x})), 'Todas as séries');
    }
    
    const union=document.getElementById('pdfFilterUniao').value;
    const unions=[...new Set(Reports.entities.map(x=>x.uniao).filter(Boolean))].sort();
    Reports.select('pdfFilterUniao', unions.map(x=>({value:x,label:x})), 'Todas as uniões', union);
    this.updateFilters('init');
  }
};

const PdfReports = {
  getFilters() {
    return {
      uniao: document.getElementById('pdfFilterUniao')?.value || '',
      associacao: document.getElementById('pdfFilterAssoc')?.value || '',
      escola: document.getElementById('pdfFilterEscola')?.value || '',
      bimestre: document.getElementById('pdfFilterBimestre')?.value || '',
      serie: document.getElementById('pdfFilterSerie')?.value || ''
    };
  },

  async generate(type, btnElement) {
    if (typeof ReportModal !== 'undefined') {
      ReportModal.open();
      return;
    }
    const f = this.getFilters();
    
    if (type === 'uniao' && !f.uniao) {
      const unions = [...new Set((Reports.entities || []).map(e => e.uniao).filter(Boolean))];
      if (unions.length > 1) {
        return App.showToast('Por favor, selecione uma União no filtro acima para gerar o relatório de todas as suas unidades.', 'warning');
      } else if (unions.length === 1) {
        f.uniao = unions[0];
      }
    }

    if (type === 'escola' && !f.escola) {
      if (Reports.entities && Reports.entities.length > 1) {
        return App.showToast('Por favor, selecione uma escola no filtro acima para gerar o relatório da unidade.', 'warning');
      }
    }
    
    if (type === 'turma' && !f.escola) {
      if (Reports.entities && Reports.entities.length > 1) {
        return App.showToast('Por favor, selecione uma escola no filtro acima para gerar o relatório da turma.', 'warning');
      }
    }

    if (type === 'aluno') {
      let alunoId = f.aluno;
      if (!alunoId) {
        alunoId = prompt('Informe o RA ou Nome do aluno para gerar o boletim pedagógico:');
        if (!alunoId || !alunoId.trim()) return;
        f.aluno = alunoId.trim();
      }
    }

    const originalText = btnElement ? btnElement.innerHTML : '';
    if (btnElement) {
      btnElement.disabled = true;
      btnElement.innerHTML = '⏳ Gerando PDF...';
    }

    App.showToast('Processando e gerando documento PDF, aguarde...', 'info');

    try {
      await API.downloadPdf(type, f);
      App.showToast('Relatório PDF baixado com sucesso!', 'success');
    } catch (err) {
      App.showToast('Erro ao gerar PDF: ' + err.message, 'error');
    } finally {
      if (btnElement) {
        btnElement.disabled = false;
        btnElement.innerHTML = originalText;
      }
    }
  }
};
window.PdfReports = PdfReports;
