import sqlite3


def init_db():
    conn = sqlite3.connect('padaria.db')
    c = conn.cursor()

    # Tabela de usuários
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT UNIQUE NOT NULL,
                  password TEXT NOT NULL,
                  nome_completo TEXT NOT NULL,
                  setor TEXT NOT NULL)''')

    # Tabela de retirada de produtos
    c.execute('''CREATE TABLE IF NOT EXISTS retiradas
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  cod_origem TEXT NOT NULL,
                  desc_origem TEXT NOT NULL,
                  quant_origem INTEGER NOT NULL,
                  cod_destino TEXT NOT NULL,
                  prod_destino TEXT NOT NULL,
                  quant_destino INTEGER NOT NULL,
                  data TEXT NOT NULL,
                  user_id INTEGER NOT NULL,
                  FOREIGN KEY(user_id) REFERENCES users(id))''')

    conn.commit()
    conn.close()


init_db()