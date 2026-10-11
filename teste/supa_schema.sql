--
-- PostgreSQL database dump
--

\restrict wHJWUiM6NJIqA89SglMDxoNYE7la8sQFtdaWJrWADutqs91aglVKG4g5ayZKFML

-- Dumped from database version 17.5
-- Dumped by pg_dump version 18.6

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: pluraal; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA pluraal;


--
-- Name: update_atualizado_em(); Type: FUNCTION; Schema: pluraal; Owner: -
--

CREATE FUNCTION pluraal.update_atualizado_em() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
   NEW.atualizado_em = now();
   RETURN NEW;
END;
$$;


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: aluno; Type: TABLE; Schema: pluraal; Owner: -
--

CREATE TABLE pluraal.aluno (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    id_simulado text,
    ano text,
    serie text,
    nivel text,
    nivel_serie text,
    bimestre text,
    tipo_simulado text,
    materia_simulado text,
    escola text,
    alunos text,
    ra text,
    turma text,
    inicio date,
    fim date,
    hora_inicio time without time zone,
    hora_fim time without time zone,
    tempo text,
    eventos text,
    disciplina text,
    nota_disciplina numeric(6,2),
    qtd_acertos_disciplina integer,
    qtd_questao_disciplina integer,
    total_final numeric(6,2),
    total_acertos integer,
    total_questao integer,
    nome_simulado text,
    data_ultima_insercao timestamp without time zone DEFAULT now()
);


--
-- Name: arquivos; Type: TABLE; Schema: pluraal; Owner: -
--

CREATE TABLE pluraal.arquivos (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    tipo_arquivo text,
    ano text,
    bimestre text,
    nome_arquivo text,
    arquivo bytea,
    pasta text,
    subpasta text,
    obs text,
    data_da_ultima_insercao timestamp without time zone DEFAULT now()
);


--
-- Name: escolas_pluraal; Type: TABLE; Schema: pluraal; Owner: -
--

CREATE TABLE pluraal.escolas_pluraal (
    id_escolas integer DEFAULT (100000 + (floor((random() * (900000)::double precision)))::integer) NOT NULL,
    "UNIAO" text,
    "SIGLA_UNIAO" text,
    "ASSOCIACAO" text,
    "SIGLA_ASSOCIACAO" text,
    "ESCOLA" text,
    CONSTRAINT escolas_pluraal_id_seis_digitos CHECK (((id_escolas >= 100000) AND (id_escolas <= 999999)))
);


--
-- Name: gabarito_aluno; Type: TABLE; Schema: pluraal; Owner: -
--

CREATE TABLE pluraal.gabarito_aluno (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    id_simulado text,
    alunos text,
    ra text,
    turma text,
    questao text,
    resposta text,
    status_questao text,
    gabarito text,
    dificuldade text,
    enunciado text,
    disciplina text,
    habilidade text,
    descricao text,
    escola text,
    ano text,
    bimestre text,
    nivel_serie text,
    data_ultima_insercao timestamp without time zone DEFAULT now()
);


--
-- Name: questao_simulados; Type: TABLE; Schema: pluraal; Owner: -
--

CREATE TABLE pluraal.questao_simulados (
    id text DEFAULT (gen_random_uuid())::text NOT NULL,
    id_simulado text,
    sequencia text,
    id_questao text,
    enunciado text,
    disciplina text,
    habilidade_conteudo text,
    habilidade text,
    descricao text,
    dificuldade text,
    gabarito text,
    ano text,
    perfil text,
    data_insercao timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    nome_simulado text
);


--
-- Name: usuario; Type: TABLE; Schema: pluraal; Owner: -
--

CREATE TABLE pluraal.usuario (
    id_usuario bigint NOT NULL,
    nome_completo_usuario text NOT NULL,
    email text NOT NULL,
    senha text NOT NULL,
    hierarquia text NOT NULL,
    ativo boolean DEFAULT true NOT NULL,
    trocar_senha_no_primeiro_acesso boolean DEFAULT true NOT NULL,
    pode_criar_usuario boolean DEFAULT false NOT NULL,
    criado_por_usuario_id bigint,
    criado_em timestamp with time zone DEFAULT now() NOT NULL,
    token_versao integer DEFAULT 1 NOT NULL,
    foto_perfil text,
    paginas_permitidas text[] DEFAULT '{reports,paaeb,data}'::text[],
    pode_simular_visao boolean DEFAULT false,
    limite_criacao_usuarios integer,
    pode_cadastrar_escola boolean DEFAULT false,
    data_expiracao_login date,
    CONSTRAINT usuario_hierarquia_check CHECK ((hierarquia = ANY (ARRAY['Master'::text, 'uniao'::text, 'associacao'::text, 'escola'::text])))
);


--
-- Name: COLUMN usuario.data_expiracao_login; Type: COMMENT; Schema: pluraal; Owner: -
--

COMMENT ON COLUMN pluraal.usuario.data_expiracao_login IS 'Último dia em que o usuário pode entrar e usar a plataforma; NULL significa acesso sem prazo.';


--
-- Name: usuario_acesso; Type: TABLE; Schema: pluraal; Owner: -
--

CREATE TABLE pluraal.usuario_acesso (
    id_acesso bigint NOT NULL,
    id_usuario bigint NOT NULL,
    tipo text NOT NULL,
    sigla_uniao text,
    sigla_associacao text,
    id_escolas integer,
    CONSTRAINT ck_usuario_acesso_tipo CHECK ((((tipo = 'uniao'::text) AND (sigla_uniao IS NOT NULL) AND (sigla_associacao IS NULL) AND (id_escolas IS NULL)) OR ((tipo = 'associacao'::text) AND (sigla_uniao IS NOT NULL) AND (sigla_associacao IS NOT NULL) AND (id_escolas IS NULL)) OR ((tipo = 'escola'::text) AND (sigla_uniao IS NULL) AND (sigla_associacao IS NULL) AND (id_escolas IS NOT NULL)))),
    CONSTRAINT usuario_acesso_tipo_check CHECK ((tipo = ANY (ARRAY['uniao'::text, 'associacao'::text, 'escola'::text])))
);


--
-- Name: usuario_acesso_id_acesso_seq; Type: SEQUENCE; Schema: pluraal; Owner: -
--

ALTER TABLE pluraal.usuario_acesso ALTER COLUMN id_acesso ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME pluraal.usuario_acesso_id_acesso_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: usuario_id_usuario_seq; Type: SEQUENCE; Schema: pluraal; Owner: -
--

ALTER TABLE pluraal.usuario ALTER COLUMN id_usuario ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME pluraal.usuario_id_usuario_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: aluno aluno_pkey; Type: CONSTRAINT; Schema: pluraal; Owner: -
--

ALTER TABLE ONLY pluraal.aluno
    ADD CONSTRAINT aluno_pkey PRIMARY KEY (id);


--
-- Name: arquivos arquivos_pkey; Type: CONSTRAINT; Schema: pluraal; Owner: -
--

ALTER TABLE ONLY pluraal.arquivos
    ADD CONSTRAINT arquivos_pkey PRIMARY KEY (id);


--
-- Name: escolas_pluraal escolas_pluraal_pkey; Type: CONSTRAINT; Schema: pluraal; Owner: -
--

ALTER TABLE ONLY pluraal.escolas_pluraal
    ADD CONSTRAINT escolas_pluraal_pkey PRIMARY KEY (id_escolas);


--
-- Name: gabarito_aluno gabarito_aluno_pkey; Type: CONSTRAINT; Schema: pluraal; Owner: -
--

ALTER TABLE ONLY pluraal.gabarito_aluno
    ADD CONSTRAINT gabarito_aluno_pkey PRIMARY KEY (id);


--
-- Name: questao_simulados questao_simulados_pkey; Type: CONSTRAINT; Schema: pluraal; Owner: -
--

ALTER TABLE ONLY pluraal.questao_simulados
    ADD CONSTRAINT questao_simulados_pkey PRIMARY KEY (id);


--
-- Name: usuario_acesso usuario_acesso_pkey; Type: CONSTRAINT; Schema: pluraal; Owner: -
--

ALTER TABLE ONLY pluraal.usuario_acesso
    ADD CONSTRAINT usuario_acesso_pkey PRIMARY KEY (id_acesso);


--
-- Name: usuario usuario_pkey; Type: CONSTRAINT; Schema: pluraal; Owner: -
--

ALTER TABLE ONLY pluraal.usuario
    ADD CONSTRAINT usuario_pkey PRIMARY KEY (id_usuario);


--
-- Name: idx_aluno_escola; Type: INDEX; Schema: pluraal; Owner: -
--

CREATE INDEX idx_aluno_escola ON pluraal.aluno USING btree (escola);


--
-- Name: idx_aluno_escola_trim_lower; Type: INDEX; Schema: pluraal; Owner: -
--

CREATE INDEX idx_aluno_escola_trim_lower ON pluraal.aluno USING btree (lower(TRIM(BOTH FROM escola)));


--
-- Name: idx_aluno_id_simulado; Type: INDEX; Schema: pluraal; Owner: -
--

CREATE INDEX idx_aluno_id_simulado ON pluraal.aluno USING btree (id_simulado);


--
-- Name: idx_aluno_inicio; Type: INDEX; Schema: pluraal; Owner: -
--

CREATE INDEX idx_aluno_inicio ON pluraal.aluno USING btree (inicio);


--
-- Name: idx_aluno_periodo; Type: INDEX; Schema: pluraal; Owner: -
--

CREATE INDEX idx_aluno_periodo ON pluraal.aluno USING btree (ano, bimestre);


--
-- Name: idx_aluno_ra; Type: INDEX; Schema: pluraal; Owner: -
--

CREATE INDEX idx_aluno_ra ON pluraal.aluno USING btree (ra);


--
-- Name: idx_aluno_simulado; Type: INDEX; Schema: pluraal; Owner: -
--

CREATE INDEX idx_aluno_simulado ON pluraal.aluno USING btree (id_simulado);


--
-- Name: idx_aluno_student_identity; Type: INDEX; Schema: pluraal; Owner: -
--

CREATE INDEX idx_aluno_student_identity ON pluraal.aluno USING btree (COALESCE(
CASE
    WHEN (TRIM(BOTH FROM ra) ~ '^[0-9]+[.]0+$'::text) THEN split_part(TRIM(BOTH FROM ra), '.'::text, 1)
    ELSE NULLIF(TRIM(BOTH FROM ra), ''::text)
END, ('nome:'::text || lower(TRIM(BOTH FROM alunos)))));


--
-- Name: idx_aluno_turma; Type: INDEX; Schema: pluraal; Owner: -
--

CREATE INDEX idx_aluno_turma ON pluraal.aluno USING btree (turma);


--
-- Name: idx_arquivos_ano_bim; Type: INDEX; Schema: pluraal; Owner: -
--

CREATE INDEX idx_arquivos_ano_bim ON pluraal.arquivos USING btree (ano, bimestre);


--
-- Name: idx_arquivos_nome; Type: INDEX; Schema: pluraal; Owner: -
--

CREATE INDEX idx_arquivos_nome ON pluraal.arquivos USING btree (nome_arquivo);


--
-- Name: idx_arquivos_tipo; Type: INDEX; Schema: pluraal; Owner: -
--

CREATE INDEX idx_arquivos_tipo ON pluraal.arquivos USING btree (tipo_arquivo);


--
-- Name: idx_gabarito_disciplina; Type: INDEX; Schema: pluraal; Owner: -
--

CREATE INDEX idx_gabarito_disciplina ON pluraal.gabarito_aluno USING btree (disciplina);


--
-- Name: idx_gabarito_escola; Type: INDEX; Schema: pluraal; Owner: -
--

CREATE INDEX idx_gabarito_escola ON pluraal.gabarito_aluno USING btree (escola);


--
-- Name: idx_gabarito_escola_simulado; Type: INDEX; Schema: pluraal; Owner: -
--

CREATE INDEX idx_gabarito_escola_simulado ON pluraal.gabarito_aluno USING btree (lower(TRIM(BOTH FROM escola)), id_simulado);


--
-- Name: idx_gabarito_escola_trim_lower; Type: INDEX; Schema: pluraal; Owner: -
--

CREATE INDEX idx_gabarito_escola_trim_lower ON pluraal.gabarito_aluno USING btree (lower(TRIM(BOTH FROM escola)));


--
-- Name: idx_gabarito_id_simulado; Type: INDEX; Schema: pluraal; Owner: -
--

CREATE INDEX idx_gabarito_id_simulado ON pluraal.gabarito_aluno USING btree (id_simulado);


--
-- Name: idx_gabarito_periodo; Type: INDEX; Schema: pluraal; Owner: -
--

CREATE INDEX idx_gabarito_periodo ON pluraal.gabarito_aluno USING btree (ano, bimestre);


--
-- Name: idx_gabarito_questao; Type: INDEX; Schema: pluraal; Owner: -
--

CREATE INDEX idx_gabarito_questao ON pluraal.gabarito_aluno USING btree (questao);


--
-- Name: idx_gabarito_ra; Type: INDEX; Schema: pluraal; Owner: -
--

CREATE INDEX idx_gabarito_ra ON pluraal.gabarito_aluno USING btree (ra);


--
-- Name: idx_gabarito_simulado; Type: INDEX; Schema: pluraal; Owner: -
--

CREATE INDEX idx_gabarito_simulado ON pluraal.gabarito_aluno USING btree (id_simulado);


--
-- Name: idx_gabarito_status_questao; Type: INDEX; Schema: pluraal; Owner: -
--

CREATE INDEX idx_gabarito_status_questao ON pluraal.gabarito_aluno USING btree (status_questao);


--
-- Name: idx_gabarito_student_identity; Type: INDEX; Schema: pluraal; Owner: -
--

CREATE INDEX idx_gabarito_student_identity ON pluraal.gabarito_aluno USING btree (COALESCE(
CASE
    WHEN (TRIM(BOTH FROM ra) ~ '^[0-9]+[.]0+$'::text) THEN split_part(TRIM(BOTH FROM ra), '.'::text, 1)
    ELSE NULLIF(TRIM(BOTH FROM ra), ''::text)
END, ('nome:'::text || lower(TRIM(BOTH FROM alunos)))));


--
-- Name: idx_questao_simulados_dificuldade; Type: INDEX; Schema: pluraal; Owner: -
--

CREATE INDEX idx_questao_simulados_dificuldade ON pluraal.questao_simulados USING btree (dificuldade);


--
-- Name: idx_questao_simulados_duplicados; Type: INDEX; Schema: pluraal; Owner: -
--

CREATE INDEX idx_questao_simulados_duplicados ON pluraal.questao_simulados USING btree (id_simulado, perfil, nome_simulado);


--
-- Name: idx_questao_simulados_simulado; Type: INDEX; Schema: pluraal; Owner: -
--

CREATE INDEX idx_questao_simulados_simulado ON pluraal.questao_simulados USING btree (id_simulado, ano);


--
-- Name: idx_usuario_email_lower; Type: INDEX; Schema: pluraal; Owner: -
--

CREATE UNIQUE INDEX idx_usuario_email_lower ON pluraal.usuario USING btree (lower(email));


--
-- Name: uq_usuario_acesso_associacao; Type: INDEX; Schema: pluraal; Owner: -
--

CREATE UNIQUE INDEX uq_usuario_acesso_associacao ON pluraal.usuario_acesso USING btree (id_usuario, sigla_uniao, sigla_associacao) WHERE (tipo = 'associacao'::text);


--
-- Name: uq_usuario_acesso_escola; Type: INDEX; Schema: pluraal; Owner: -
--

CREATE UNIQUE INDEX uq_usuario_acesso_escola ON pluraal.usuario_acesso USING btree (id_usuario, id_escolas) WHERE (tipo = 'escola'::text);


--
-- Name: uq_usuario_acesso_uniao; Type: INDEX; Schema: pluraal; Owner: -
--

CREATE UNIQUE INDEX uq_usuario_acesso_uniao ON pluraal.usuario_acesso USING btree (id_usuario, sigla_uniao) WHERE (tipo = 'uniao'::text);


--
-- Name: uq_usuario_email; Type: INDEX; Schema: pluraal; Owner: -
--

CREATE UNIQUE INDEX uq_usuario_email ON pluraal.usuario USING btree (lower(email));


--
-- Name: usuario_acesso usuario_acesso_id_escolas_fkey; Type: FK CONSTRAINT; Schema: pluraal; Owner: -
--

ALTER TABLE ONLY pluraal.usuario_acesso
    ADD CONSTRAINT usuario_acesso_id_escolas_fkey FOREIGN KEY (id_escolas) REFERENCES pluraal.escolas_pluraal(id_escolas);


--
-- Name: usuario_acesso usuario_acesso_id_usuario_fkey; Type: FK CONSTRAINT; Schema: pluraal; Owner: -
--

ALTER TABLE ONLY pluraal.usuario_acesso
    ADD CONSTRAINT usuario_acesso_id_usuario_fkey FOREIGN KEY (id_usuario) REFERENCES pluraal.usuario(id_usuario) ON DELETE CASCADE;


--
-- Name: usuario usuario_criado_por_usuario_id_fkey; Type: FK CONSTRAINT; Schema: pluraal; Owner: -
--

ALTER TABLE ONLY pluraal.usuario
    ADD CONSTRAINT usuario_criado_por_usuario_id_fkey FOREIGN KEY (criado_por_usuario_id) REFERENCES pluraal.usuario(id_usuario);


--
-- PostgreSQL database dump complete
--

\unrestrict wHJWUiM6NJIqA89SglMDxoNYE7la8sQFtdaWJrWADutqs91aglVKG4g5ayZKFML

