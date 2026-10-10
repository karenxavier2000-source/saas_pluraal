import psycopg2

conn = psycopg2.connect('dbname=pluraal user=postgres password=postgres host=localhost')
cur = conn.cursor()

try:
    cur.execute('''
        ALTER TABLE pluraal.usuario 
        ALTER COLUMN paginas_permitidas SET DEFAULT '{"reports", "paaeb", "data"}';
    ''')
    cur.execute('''
        UPDATE pluraal.usuario 
        SET paginas_permitidas = '{"reports", "paaeb", "data"}'
        WHERE paginas_permitidas IS NULL;
    ''')
    conn.commit()
    print('DB column updated successfully.')
except Exception as e:
    print('Error:', e)
    conn.rollback()
finally:
    cur.close()
    conn.close()
