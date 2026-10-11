# Pluraal SaaS

Sistema de Gestão e Análise Educacional Integrado (PAAEB, Escolas, Indicadores e Relatórios).

## Estrutura do Projeto

- `Frontend/` - Interface web com páginas estáticas, estilos (CSS) e scripts de tela (JS).
- `Backend/` - Servidor Flask contendo as rotas de API, autenticação JWT, integração com o banco PostgreSQL (Supabase) e geradores de relatórios.
- `api/` - Ponto de entrada WSGI (`index.py`) para deploy serverless na Vercel.
- `teste/` - Scripts de teste, rotinas de migração, conciliação e utilitários auxiliares.
- `vercel.json` - Configuração de rotas e builds da plataforma Vercel.
- `requirements.txt` - Dependências do Python.
- `run.py` - Script para inicialização local do servidor Flask.

---

## Como Rodar Localmente

1. **Instale as dependências:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure as variáveis de ambiente:**
   Crie um arquivo `.env` na raiz com as credenciais do banco:
   ```env
   PGHOST=aws-0-us-east-1.pooler.supabase.com
   PGPORT=6543
   PGDATABASE=postgres
   PGUSER=postgres.xwqllkbwtverxtxmqolb
   PGPASSWORD=sua_senha
   PGSSLMODE=require
   SECRET_KEY=sua_chave_secreta_jwt
   ```

3. **Inicie o servidor:**
   ```bash
   python run.py
   ```
   Acesse no navegador: `http://127.0.0.1:5050`

---

## Deploy na Vercel

1. Conecte este repositório no dashboard da [Vercel](https://vercel.com).
2. Configure as seguintes **Environment Variables** nas configurações do projeto na Vercel:
   - `PGHOST`
   - `PGPORT`
   - `PGDATABASE`
   - `PGUSER`
   - `PGPASSWORD`
   - `PGSSLMODE=require`
   - `SECRET_KEY`
3. O build e roteamento serão gerenciados automaticamente pelo `vercel.json`.
