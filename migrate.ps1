$ErrorActionPreference = "Stop"

Write-Host "Iniciando o dump do banco de dados local (192.168.171.158)..."
$env:PGPASSWORD = "Mudar@123"
& "C:\Program Files\PostgreSQL\18\bin\pg_dump.exe" -h 192.168.171.158 -p 5432 -U postgres -d postgres -n pluraal --no-owner --no-privileges -F p -f "C:\Users\karen.xavier\Desktop\pluraal saas\dump_pluraal.sql"

if ($LASTEXITCODE -eq 0) {
    Write-Host "Dump concluído com sucesso!"
    Write-Host "Iniciando a restauração no Supabase..."
    $env:PGPASSWORD = "0Utl@nd&r2001"
    & "C:\Program Files\PostgreSQL\18\bin\psql.exe" -h aws-1-us-west-2.pooler.supabase.com -p 6543 -U postgres.xlptaftgfxogvmebqzoy -d postgres -f "C:\Users\karen.xavier\Desktop\pluraal saas\dump_pluraal.sql"
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "MIGRAÇÃO FINALIZADA COM SUCESSO!"
    } else {
        Write-Host "Erro durante a restauração no Supabase."
    }
} else {
    Write-Host "Erro durante o dump local."
}
