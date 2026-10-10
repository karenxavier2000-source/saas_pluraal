from Backend.database.connection import get_db_cursor

try:
    with get_db_cursor(commit=True) as cur:
        cur.execute('''
            ALTER TABLE pluraal.usuario 
            ALTER COLUMN paginas_permitidas SET DEFAULT '{"reports", "paaeb", "data"}';
        ''')
        cur.execute('''
            UPDATE pluraal.usuario 
            SET paginas_permitidas = '{"reports", "paaeb", "data"}'
            WHERE paginas_permitidas IS NULL;
        ''')
    print('DB column updated successfully.')
except Exception as e:
    print('Error:', e)
