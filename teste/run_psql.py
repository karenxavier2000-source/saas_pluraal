import subprocess
import os

env = os.environ.copy()
env["PGPASSWORD"] = "0Utl@nd&r2001"
psql_path = r"C:\Program Files\PostgreSQL\18\bin\psql.exe"

commands = [
    [psql_path, "-h", "aws-0-us-east-1.pooler.supabase.com", "-p", "6543", "-U", "postgres.xwqllkbwtverxtxmqolb", "-d", "postgres", "-f", r"C:\Users\karen.xavier\Desktop\pluraal saas\supa_schema.sql"],
    [psql_path, "-h", "aws-0-us-east-1.pooler.supabase.com", "-p", "6543", "-U", "postgres.xwqllkbwtverxtxmqolb", "-d", "postgres", "-f", r"C:\Users\karen.xavier\Desktop\pluraal saas\supa_data.sql"],
    [psql_path, "-h", "aws-0-us-east-1.pooler.supabase.com", "-p", "6543", "-U", "postgres.xwqllkbwtverxtxmqolb", "-d", "postgres", "-c", r"\copy pluraal.gabarito_aluno FROM 'C:\Users\karen.xavier\Desktop\pluraal saas\gabarito_data.csv' WITH CSV"]
]

print("Iniciando restauracao no Supabase...")
for cmd in commands:
    print(f"Executando: {' '.join(cmd[:10])}...")
    result = subprocess.run(cmd, env=env, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"ERRO: {result.stderr}")
    else:
        print("SUCESSO!")

print("MIGRACAO FINALIZADA!")
