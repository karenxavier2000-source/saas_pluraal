# Sincronização educacional PostgreSQL → MySQL (2026)

Fonte: tabelas educacionais `pluraal` do PostgreSQL. O MySQL conserva seus registros antigos e seus valores já preenchidos. O vínculo do simulado usa `ID_SIMULADO + ESCOLA`; linhas de alunos também usam aluno e disciplina, e linhas de questões também usam `ID_QUESTAO`.

## Alterações aplicadas

- `escolas_pluraal`: 63 escolas inseridas.
- `simulados`: 1.412 combinações de simulado e escola inseridas; 389 registros existentes tiveram campos vazios preenchidos.
- `alunos_simulados`: 216.681 linhas existentes vinculadas à fonte; 153.518 linhas de 2026 inseridas. Foram adicionadas as colunas `PG_SOURCE_ID`, `RA` e `TOTAL_FINAL`.
- `mapa_simulados`: 13.628 questões inseridas; 5.595 habilidades antes vazias preenchidas.
- `questao_simulado`: 13.628 questões inseridas; 4.813 habilidades antes vazias preenchidas; 1.101 linhas tiveram contagens de respostas ou taxa de acerto preenchidas quando o vínculo era verificável.
- `alunos_simulados`: mais 37.396 totais de questões por disciplina e 38.879 linhas de respostas/acertos foram completados após a carga inicial.

## Validação

- As 370.199 linhas de `pluraal.aluno` de 2026 estão representadas por 370.199 valores únicos de `PG_SOURCE_ID` no MySQL.
- O desempenho médio de `TOTAL_FINAL` da AAMAR no 3º bimestre de 2026 coincide nos dois bancos: Cidade Nova 76,4%, Boa Vista 67,6% e Itacoatiara 51,1%.
- Reexecuções de cada etapa não encontraram novos registros para inserir nem novos valores seguros para preencher.
- O sincronizador é [sync_education_mysql.py](sync_education_mysql.py); sem `--apply`, executa apenas uma prévia.

## Valores que permaneceram vazios

O PostgreSQL não contém dados de 2025 na tabela `pluraal.aluno`; os registros de 2025 do MySQL não foram modificados. Em 2026, `TOTAL_FINAL` continua vazio para simulados sem nota na fonte e para linhas antigas do MySQL sem correspondência inequívoca. As colunas `DESEMPENHO_MATERIA` e algumas contagens de alternativas não têm equivalência confiável para todas as linhas. Há 56 escolas cujo nome existe no PostgreSQL, mas cujos campos de união ou associação estão vazios também na fonte. Esses campos foram mantidos vazios conforme a orientação de preservar a ausência real de dado.

Linhas antigas do MySQL com disciplina vazia não foram vinculadas por `ID_SIMULADO + ESCOLA` isoladamente: essa dupla contém vários alunos e disciplinas. Atribuir uma disciplina sem vínculo inequívoco poderia duplicar ou trocar resultados.
