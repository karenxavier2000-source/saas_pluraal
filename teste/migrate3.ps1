$ErrorActionPreference = "Stop"

# Senha com caracteres especiais encodados (@ -> %40, & -> %26)
$uri = "postgresql://postgres.xwqllkbwtverxtxmqolb:0Utl%40nd%26r2001@aws-0-us-east-1.pooler.supabase.com:6543/postgres"

Write-Host "4. Aplicando a estrutura no Supabase..."
& "C:\Program Files\PostgreSQL\18\bin\psql.exe" $uri -f "C:\Users\karen.xavier\Desktop\pluraal saas\supa_schema.sql"

Write-Host "5. Restaurando os dados completos (Escolas, Alunos, etc)..."
& "C:\Program Files\PostgreSQL\18\bin\psql.exe" $uri -f "C:\Users\karen.xavier\Desktop\pluraal saas\supa_data.sql"

Write-Host "6. Restaurando a amostra segura do Gabarito..."
& "C:\Program Files\PostgreSQL\18\bin\psql.exe" $uri -c "\copy pluraal.gabarito_aluno FROM 'C:\Users\karen.xavier\Desktop\pluraal saas\gabarito_data.csv' WITH CSV"

Write-Host "MIGRACAO FINALIZADA COM SUCESSO!"
