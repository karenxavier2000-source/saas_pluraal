from Backend.database.connection import get_db_cursor

try:
    with get_db_cursor(commit=True) as cur:
        cur.execute('''
            ALTER TABLE pluraal.usuario 
            ADD COLUMN IF NOT EXISTS pode_cadastrar_escola BOOLEAN DEFAULT FALSE;
        ''')
        # update Master users to true
        cur.execute('''
            UPDATE pluraal.usuario 
            SET pode_cadastrar_escola = TRUE
            WHERE hierarquia = 'Master';
        ''')
    print('DB column updated successfully.')
except Exception as e:
    print('Error:', e)
