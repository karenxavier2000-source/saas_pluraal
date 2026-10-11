$ErrorActionPreference = "Stop"

$env:PGPASSWORD = "Mudar@123"
Write-Host "1. Fazendo dump da estrutura exata (Schema pluraal e paaeb)..."
& "C:\Program Files\PostgreSQL\18\bin\pg_dump.exe" -h 192.168.171.158 -p 5432 -U postgres -d postgres -n pluraal -n paaeb -s --no-owner --no-privileges -F p -f "C:\Users\karen.xavier\Desktop\pluraal saas\supa_schema.sql"

Write-Host "2. Fazendo dump dos dados (Todas tabelas EXCETO gabarito_aluno)..."
& "C:\Program Files\PostgreSQL\18\bin\pg_dump.exe" -h 192.168.171.158 -p 5432 -U postgres -d postgres -n pluraal -n paaeb -a --no-owner --no-privileges --exclude-table-data=pluraal.gabarito_aluno -F p -f "C:\Users\karen.xavier\Desktop\pluraal saas\supa_data.sql"

Write-Host "3. Extraindo amostra segura de 100 mil registros do gabarito..."
& "C:\Program Files\PostgreSQL\18\bin\psql.exe" -h 192.168.171.158 -p 5432 -U postgres -d postgres -c "\copy (SELECT * FROM pluraal.gabarito_aluno LIMIT 100000) TO 'C:\Users\karen.xavier\Desktop\pluraal saas\gabarito_data.csv' WITH CSV"

$env:PGPASSWORD = "0Utl@nd&r2001"
Write-Host "4. Aplicando a estrutura no Supabase..."
& "C:\Program Files\PostgreSQL\18\bin\psql.exe" -h aws-0-us-east-1.pooler.supabase.com -p 6543 -U postgres.xwqllkbwtverxtxmqolb -d postgres -f "C:\Users\karen.xavier\Desktop\pluraal saas\supa_schema.sql"

Write-Host "5. Restaurando os dados completos (Escolas, Alunos, etc)..."
& "C:\Program Files\PostgreSQL\18\bin\psql.exe" -h aws-0-us-east-1.pooler.supabase.com -p 6543 -U postgres.xwqllkbwtverxtxmqolb -d postgres -f "C:\Users\karen.xavier\Desktop\pluraal saas\supa_data.sql"

Write-Host "6. Restaurando a amostra segura do Gabarito..."
& "C:\Program Files\PostgreSQL\18\bin\psql.exe" -h aws-0-us-east-1.pooler.supabase.com -p 6543 -U postgres.xwqllkbwtverxtxmqolb -d postgres -c "\copy pluraal.gabarito_aluno FROM 'C:\Users\karen.xavier\Desktop\pluraal saas\gabarito_data.csv' WITH CSV"

Write-Host "MIGRACAO FINALIZADA! TUDO PRONTO PARA O VERCEL."
