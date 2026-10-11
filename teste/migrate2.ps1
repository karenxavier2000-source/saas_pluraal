$ErrorActionPreference = "Stop"

Write-Host "Limpando arquivo de dump anterior..."
if (Test-Path "C:\Users\karen.xavier\Desktop\pluraal saas\dump_pluraal2.sql") {
    Remove-Item "C:\Users\karen.xavier\Desktop\pluraal saas\dump_pluraal2.sql"
}

Write-Host "Iniciando o NOVO dump do banco local (EXCLUINDO DADOS DE gabarito_aluno)..."
$env:PGPASSWORD = "Mudar@123"
& "C:\Program Files\PostgreSQL\18\bin\pg_dump.exe" -h 192.168.171.158 -p 5432 -U postgres -d postgres -n pluraal --no-owner --no-privileges --exclude-table-data=pluraal.gabarito_aluno -F p -f "C:\Users\karen.xavier\Desktop\pluraal saas\dump_pluraal2.sql"

if ($LASTEXITCODE -eq 0) {
    Write-Host "Dump concluído!"
    Write-Host "Restaurando tabelas base no Supabase..."
    $env:PGPASSWORD = "0Utl@nd&r2001"
    & "C:\Program Files\PostgreSQL\18\bin\psql.exe" -h aws-1-us-west-2.pooler.supabase.com -p 6543 -U postgres.xlptaftgfxogvmebqzoy -d postgres -f "C:\Users\karen.xavier\Desktop\pluraal saas\dump_pluraal2.sql"
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "MIGRAÇÃO DAS TABELAS BASE FINALIZADA!"
    } else {
        Write-Host "Erro durante a restauração no Supabase."
    }
} else {
    Write-Host "Erro durante o dump local."
}
