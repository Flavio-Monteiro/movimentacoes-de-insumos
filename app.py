from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from datetime import datetime
import pandas as pd
from fpdf import FPDF
import io


# Função para criar a aplicação Flask
def create_app():
    app = Flask(__name__)
    app.secret_key = 'c5efa0fa97d514e542270bedbb3f82d4'

    # Função para conectar ao banco de dados
    def get_db_connection():
        conn = sqlite3.connect('padaria.db')
        conn.row_factory = sqlite3.Row
        return conn

    # Rota principal
    @app.route('/')
    def index():
        if 'user_id' not in session:
            return redirect(url_for('login'))  # Redireciona para a página de login se não estiver logado
        return render_template('index.html')

    # Rota de login
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if 'user_id' in session:
            return redirect(url_for('index'))  # Se já estiver logado, redireciona para a página principal

        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            conn = get_db_connection()
            user = conn.execute('SELECT * FROM users WHERE username = ? AND password = ?',
                                (username, password)).fetchone()
            conn.close()
            if user:
                session['user_id'] = user['id']
                return redirect(url_for('index'))
            else:
                flash('Usuário ou senha incorretos')
        return render_template('login.html')

    # Rota de registro
    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if 'user_id' in session:
            return redirect(url_for('index'))  # Se já estiver logado, redireciona para a página principal

        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            nome_completo = request.form['nome_completo']
            setor = request.form['setor']

            conn = get_db_connection()
            try:
                conn.execute('INSERT INTO users (username, password, nome_completo, setor) VALUES (?, ?, ?, ?)',
                             (username, password, nome_completo, setor))
                conn.commit()
                conn.close()
                flash('Registro realizado com sucesso!')
                return redirect(url_for('login'))
            except sqlite3.IntegrityError:
                flash('Usuário já existe')
                conn.close()
        return render_template('register.html')

    # Rota para adicionar retirada de produtos
    @app.route('/add_retirada', methods=['POST'])
    def add_retirada():
        if 'user_id' not in session:
            return redirect(url_for('login'))  # Redireciona para a página de login se não estiver logado

        cod_origem = request.form['cod_origem']
        desc_origem = request.form['desc_origem']
        quant_origem = request.form['quant_origem']
        cod_destino = request.form['cod_destino']
        prod_destino = request.form['prod_destino']
        quant_destino = request.form['quant_destino']
        data = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        conn = get_db_connection()
        conn.execute(
            'INSERT INTO retiradas (cod_origem, desc_origem, quant_origem, cod_destino, prod_destino, quant_destino, data, user_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
            (cod_origem, desc_origem, quant_origem, cod_destino, prod_destino, quant_destino, data, session['user_id']))
        conn.commit()
        conn.close()

        flash('Retirada registrada com sucesso!')
        return redirect(url_for('index'))

    # Rota para logout
    @app.route('/logout')
    def logout():
        session.pop('user_id', None)  # Remove o user_id da sessão
        flash('Você foi desconectado com sucesso!')
        return redirect(url_for('login'))

    # Rota para listar produtos retirados
    @app.route('/minhas_retiradas')
    def minhas_retiradas():
        if 'user_id' not in session:
            return redirect(url_for('login'))  # Redireciona para a página de login se não estiver logado

        conn = get_db_connection()
        retiradas = conn.execute('SELECT * FROM retiradas WHERE user_id = ?', (session['user_id'],)).fetchall()
        conn.close()

        return render_template('minhas_retiradas.html', retiradas=retiradas)

    # Rota para gerar PDF
    @app.route('/gerar_pdf')
    def gerar_pdf():
        if 'user_id' not in session:
            return redirect(url_for('login'))  # Redireciona para a página de login se não estiver logado

        conn = get_db_connection()
        retiradas = conn.execute('SELECT * FROM retiradas WHERE user_id = ?', (session['user_id'],)).fetchall()
        conn.close()

        # Cria um objeto PDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)

        # Adiciona os dados das retiradas ao PDF
        for retirada in retiradas:
            pdf.cell(200, 10, txt=f"Cód. Origem: {retirada['cod_origem']}", ln=True)
            pdf.cell(200, 10, txt=f"Descrição: {retirada['desc_origem']}", ln=True)
            pdf.cell(200, 10, txt=f"Quantidade: {retirada['quant_origem']}", ln=True)
            pdf.cell(200, 10, txt=f"Cód. Destino: {retirada['cod_destino']}", ln=True)
            pdf.cell(200, 10, txt=f"Produto Destino: {retirada['prod_destino']}", ln=True)
            pdf.cell(200, 10, txt=f"Quantidade: {retirada['quant_destino']}", ln=True)
            pdf.cell(200, 10, txt=f"Data: {retirada['data']}", ln=True)
            pdf.ln(10)  # Adiciona uma quebra de linha entre as retiradas

        # Gera o PDF em memória
        pdf_output = pdf.output(dest='S').encode('latin1')

        # Retorna o PDF como uma resposta para download
        return pdf_output, 200, {'Content-Type': 'application/pdf',
                                 'Content-Disposition': 'attachment; filename=retiradas.pdf'}

    # Rota para gerar Excel
    @app.route('/gerar_excel')
    def gerar_excel():
        if 'user_id' not in session:
            return redirect(url_for('login'))  # Redireciona para a página de login se não estiver logado

        conn = get_db_connection()
        retiradas = conn.execute('SELECT * FROM retiradas WHERE user_id = ?', (session['user_id'],)).fetchall()
        conn.close()

        # Cria um DataFrame com todas as colunas retornadas pela consulta
        df = pd.DataFrame(retiradas, columns=[
            'id', 'cod_origem', 'desc_origem', 'quant_origem',
            'cod_destino', 'prod_destino', 'quant_destino', 'data', 'user_id'
        ])

        # Seleciona apenas as colunas desejadas para o Excel
        df = df[['cod_origem', 'desc_origem', 'quant_origem', 'cod_destino', 'prod_destino', 'quant_destino', 'data']]

        # Gera o arquivo Excel
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Retiradas')
        output.seek(0)

        # Retorna o Excel como uma resposta para download
        return output.getvalue(), 200, {
            'Content-Type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'Content-Disposition': 'attachment; filename=retiradas.xlsx'
        }

    return app


# Cria a instância do Flask
app = create_app()

# Roda a aplicação localmente (apenas para desenvolvimento)
if __name__ == '__main__':
    app.run(debug=True)