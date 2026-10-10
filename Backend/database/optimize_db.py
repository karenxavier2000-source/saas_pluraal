import psycopg
from Backend.config.settings import settings
from Backend.database.connection import get_db_cursor

def optimize_database():
    print("Otimizando banco de dados (criando índices de performance)...")
    try:
        with get_db_cursor() as cur:
            # Índices para a tabela de aluno
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_aluno_escola_trim_lower
                ON pluraal.aluno (LOWER(TRIM(escola)));
            """)
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_aluno_periodo
                ON pluraal.aluno (ano, bimestre);
            """)
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_aluno_simulado
                ON pluraal.aluno (id_simulado);
            """)
            
            # Índice na identidade complexa do aluno
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_aluno_student_identity
                ON pluraal.aluno (
                    (COALESCE(CASE WHEN TRIM(ra) ~ '^[0-9]+[.]0+$'
                        THEN SPLIT_PART(TRIM(ra), '.', 1)
                        ELSE NULLIF(TRIM(ra), '') END, 'nome:' || LOWER(TRIM(alunos))))
                );
            """)

            # Índices para a tabela de gabarito_aluno
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_gabarito_escola_trim_lower
                ON pluraal.gabarito_aluno (LOWER(TRIM(escola)));
            """)
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_gabarito_simulado
                ON pluraal.gabarito_aluno (id_simulado);
            """)
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_gabarito_student_identity
                ON pluraal.gabarito_aluno (
                    (COALESCE(CASE WHEN TRIM(ra) ~ '^[0-9]+[.]0+$'
                        THEN SPLIT_PART(TRIM(ra), '.', 1)
                        ELSE NULLIF(TRIM(ra), '') END, 'nome:' || LOWER(TRIM(alunos))))
                );
            """)

            # Índices de filtros
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_gabarito_status_questao
                ON pluraal.gabarito_aluno (status_questao);
            """)

            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_gabarito_periodo
                ON pluraal.gabarito_aluno (ano, bimestre);
            """)

            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_gabarito_escola_simulado
                ON pluraal.gabarito_aluno (lower(trim(escola)), id_simulado);
            """)

            print("Índices criados com sucesso!")
    except Exception as e:
        print(f"Erro ao otimizar banco: {e}")

if __name__ == '__main__':
    optimize_database()
