import psycopg2
import bcrypt

# Conectar e atualizar
conn = psycopg2.connect(host='192.168.171.158', port=5432, dbname='postgres', user='postgres', password='Mudar@123')
cur = conn.cursor()

# Hash correto
correct_hash = bcrypt.hashpw('Senha123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

cur.execute('UPDATE pluraal.usuario SET senha = %s', (correct_hash,))
conn.commit()
print('Passwords updated correctly')
